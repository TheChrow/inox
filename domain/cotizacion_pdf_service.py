"""Genera el PDF de una cotización Odoo con el branding de inox.

Flujo:
  1. Lee la cotización desde Odoo por `name` (cabecera + líneas).
  2. Lee el partner completo (cabecera con dirección + primer contacto).
  3. Calcula totales derivados (IVA = amount_total - amount_untaxed) y
     enriquece las líneas con el subtotal con descuento.
  4. Renderiza `cotizacion_pdf.html` con WeasyPrint y devuelve los bytes.
"""

import logging
import os
import sys
from datetime import date, datetime
from typing import Optional

from django.template.loader import render_to_string

from adapters.odoo.service.odoo_service_partner import PartnerOdooService
from adapters.odoo.service.odoo_service_sales import SaleOdooService

logger = logging.getLogger(__name__)


class CotizacionNotFoundError(Exception):
    """La cotización no existe en Odoo."""


class CotizacionPDFService:
    def __init__(
        self,
        sale_service: SaleOdooService,
        partner_service: PartnerOdooService,
    ):
        self.sale_service = sale_service
        self.partner_service = partner_service

    def generar_pdf(
        self,
        odoo_name: str,
        *,
        vendedor: Optional[dict] = None,
        base_url: Optional[str] = None,
    ) -> bytes:
        data = self.sale_service.read_quotation_by_name(odoo_name)
        if not data:
            raise CotizacionNotFoundError(f"Cotización no encontrada en Odoo: {odoo_name}")

        order = data["order"]
        lines = data["lines"]

        partner_id = _m2o_id(order.get("partner_id"))
        cliente_data = self.partner_service.read_customer_full(partner_id) if partner_id else None
        cliente = _formatear_cliente(cliente_data) if cliente_data else _cliente_minimo(order)

        productos = [_formatear_linea(idx, ln) for idx, ln in enumerate(lines, start=1)]

        amount_untaxed = float(order.get("amount_untaxed") or 0)
        amount_total = float(order.get("amount_total") or 0)
        iva = amount_total - amount_untaxed
        descuento_total = sum(p["descuento_monto"] for p in productos)

        contexto = {
            "cotizacion": {
                "numero": order.get("name") or odoo_name,
                "fecha": _formatear_fecha(order.get("date_order")),
                "validez": _formatear_fecha(order.get("validity_date")),
                "estado": order.get("state"),
                "referencia": order.get("client_order_ref") or "",
                "observaciones": order.get("note") or "",
                "cliente": cliente,
                "vendedor": vendedor or {},
                "productos": productos,
                "totales": {
                    "neto": amount_untaxed,
                    "iva": iva,
                    "total": amount_total,
                    "descuento": descuento_total,
                    "tiene_descuento": descuento_total > 0,
                },
            },
        }

        # Import diferido: WeasyPrint requiere GTK/cairo/pango en el sistema y
        # romper el import del módulo al arrancar Django no compensa el caso
        # común de máquinas sin esas DLLs (Windows local). En producción Linux
        # está disponible y este import es trivial.
        _ensure_gtk_on_windows()
        from weasyprint import HTML

        html_string = render_to_string("cotizacion_pdf.html", contexto)
        return HTML(string=html_string, base_url=base_url).write_pdf()


def _formatear_cliente(full: dict) -> dict:
    customer = full.get("customer") or {}
    contacto = (full.get("contacts") or [None])[0] or {}
    direccion = ", ".join(
        p for p in [
            customer.get("street"),
            customer.get("street2"),
            customer.get("city"),
            customer.get("zip"),
        ] if p
    )
    state_pair = customer.get("state_id")
    region = state_pair[1] if isinstance(state_pair, list) and len(state_pair) > 1 else ""
    return {
        "nombre": customer.get("name") or "",
        "rut": customer.get("vat") or "",
        "email": customer.get("email") or "",
        "telefono": customer.get("phone") or "",
        "giro": customer.get("comment") or "",
        "direccion": direccion,
        "region": region,
        "es_empresa": bool(customer.get("is_company")),
        "contacto": {
            "nombre": contacto.get("name") or "",
            "cargo": contacto.get("function") or "",
            "email": contacto.get("email") or "",
            "telefono": contacto.get("phone") or "",
        } if contacto else None,
    }


def _cliente_minimo(order: dict) -> dict:
    pair = order.get("partner_id")
    return {
        "nombre": pair[1] if isinstance(pair, list) and len(pair) > 1 else "",
        "rut": "", "email": "", "telefono": "", "giro": "",
        "direccion": "", "region": "", "es_empresa": False, "contacto": None,
    }


def _formatear_linea(idx: int, ln: dict) -> dict:
    cantidad = float(ln.get("product_uom_qty") or 0)
    precio_unit = float(ln.get("price_unit") or 0)
    descuento_pct = float(ln.get("discount") or 0)
    subtotal = float(ln.get("price_subtotal") or 0)
    bruto_sin_descuento = cantidad * precio_unit
    descuento_monto = bruto_sin_descuento - subtotal
    precio_con_descuento = precio_unit * (1 - descuento_pct / 100) if descuento_pct else precio_unit
    return {
        "indice": idx,
        "sku": ln.get("product_default_code") or "",
        "descripcion": ln.get("product_name") or "",
        "comentario": ln.get("name") or "",
        "imagen": ln.get("product_image") or "",
        "cantidad": cantidad,
        "precio_unitario": precio_unit,
        "descuento_pct": descuento_pct,
        "precio_con_descuento": precio_con_descuento,
        "descuento_monto": descuento_monto,
        "subtotal": subtotal,
    }


def _formatear_fecha(raw) -> str:
    if not raw:
        return ""
    if isinstance(raw, date):
        return raw.strftime("%d-%m-%Y")
    s = str(raw)[:10]  # corta "YYYY-MM-DD HH:MM:SS" si viene con hora
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        return s


def _m2o_id(value) -> Optional[int]:
    if isinstance(value, list) and value:
        return value[0]
    if isinstance(value, int):
        return value
    return None


_GTK_BIN_CANDIDATES = (
    r"C:\Program Files\GTK3-Runtime Win64\bin",
    r"C:\Program Files (x86)\GTK3-Runtime Win64\bin",
)


def _ensure_gtk_on_windows() -> None:
    """Hace que WeasyPrint encuentre las DLL de GTK aunque el PATH del shell
    no se haya recargado tras instalar el runtime.

    No-op en Linux/macOS: el sistema ya provee cairo/pango/gobject.
    """
    if sys.platform != "win32":
        return
    add_dll_directory = getattr(os, "add_dll_directory", None)
    if not add_dll_directory:
        return
    for path in _GTK_BIN_CANDIDATES:
        if os.path.isdir(path):
            try:
                add_dll_directory(path)
            except (OSError, FileNotFoundError):
                logger.debug("No se pudo registrar GTK dll dir: %s", path, exc_info=True)
            return
