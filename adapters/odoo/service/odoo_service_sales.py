from typing import Optional

from adapters.odoo.client.odoo_client import OdooAPIClient


class SaleOdooService:
    def __init__(self, client: OdooAPIClient):
        self.client = client
        self.base_path = "/json/2/sale.order"
        self.line_path = "/json/2/sale.order.line"
        self.partner_path = "/json/2/res.partner"
        self.product_path = "/json/2/product.product"

    def search_read(self, domain: list, fields: list) -> list:
        return self.client.post(
            f"{self.base_path}/search_read",
            {"domain": domain, "fields": fields},
        )

    def search_read_paginated(
        self,
        domain: list,
        fields: list,
        limit: int,
        offset: int,
        order: str = "date_order desc, id desc",
    ) -> list:
        return self.client.post(
            f"{self.base_path}/search_read",
            {
                "domain": domain,
                "fields": fields,
                "limit": limit,
                "offset": offset,
                "order": order,
            },
        )

    def search_count(self, domain: list) -> int:
        result = self.client.post(
            f"{self.base_path}/search_count",
            {"domain": domain},
        )
        if isinstance(result, int):
            return result
        if isinstance(result, list) and result and isinstance(result[0], int):
            return result[0]
        return 0

    def list_quotations(
        self,
        *,
        limit: int,
        offset: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        date_doc: Optional[str] = None,
        doc_num: Optional[str] = None,
        partner_text: Optional[str] = None,
        salesperson_id: Optional[int] = None,
        salesperson_name: Optional[str] = None,
        state: Optional[str] = None,
        amount_total: Optional[float] = None,
    ) -> dict:
        domain = self._build_quotations_domain(
            date_from=date_from,
            date_to=date_to,
            date_doc=date_doc,
            doc_num=doc_num,
            partner_text=partner_text,
            salesperson_id=salesperson_id,
            salesperson_name=salesperson_name,
            state=state,
            amount_total=amount_total,
        )

        fields = [
            "id",
            "name",
            "partner_id",
            "user_id",
            "x_studio_vendedor",
            "date_order",
            "state",
            "amount_untaxed",
            "amount_total",
        ]

        total = self.search_count(domain)
        records = self.search_read_paginated(
            domain=domain,
            fields=fields,
            limit=limit,
            offset=offset,
        )

        return {"total": total, "records": records}

    @staticmethod
    def _build_quotations_domain(
        *,
        date_from: Optional[str],
        date_to: Optional[str],
        date_doc: Optional[str],
        doc_num: Optional[str],
        partner_text: Optional[str],
        salesperson_id: Optional[int],
        salesperson_name: Optional[str],
        state: Optional[str],
        amount_total: Optional[float],
    ) -> list:
        domain: list = []

        if date_doc:
            domain.append(("date_order", ">=", f"{date_doc} 00:00:00"))
            domain.append(("date_order", "<=", f"{date_doc} 23:59:59"))
        else:
            if date_from:
                domain.append(("date_order", ">=", f"{date_from} 00:00:00"))
            if date_to:
                domain.append(("date_order", "<=", f"{date_to} 23:59:59"))

        if doc_num:
            domain.append(("name", "ilike", doc_num))

        if partner_text:
            domain.append(("partner_id.name", "ilike", partner_text))

        if salesperson_id:
            domain.append(("x_studio_vendedor", "=", salesperson_id))
        elif salesperson_name:
            domain.append(("x_studio_vendedor", "ilike", salesperson_name))

        if state:
            domain.extend(SaleOdooService._state_clauses(state))

        if amount_total is not None:
            domain.append(("amount_total", "=", amount_total))

        return domain

    @staticmethod
    def _state_clauses(state_code: str) -> list:
        mapping = {
            "O": [("state", "in", ["draft", "sent"])],
            "C": [("state", "in", ["sale", "done"])],
            "Y": [("state", "=", "cancel")],
        }
        return mapping.get(state_code, [])

    def read(self, ids: list, fields: list) -> list:
        return self.client.post(
            f"{self.base_path}/read",
            {"ids": ids, "fields": fields},
        )

    def create(self, values: dict) -> list:
        return self.client.post(
            f"{self.base_path}/create",
            {"vals_list": [values]},
        )

    def write(self, ids: list, values: dict) -> bool:
        return self.client.post(
            f"{self.base_path}/write",
            {"ids": ids, "vals": values},
        )

    def search_partner(self, domain: list) -> list:
        return self.client.post(
            f"{self.partner_path}/search_read",
            {
                "domain": domain,
                "fields": ["id", "name", "vat", "street", "email"],
            },
        )
    
    def create_line(self, values: dict):
        return self.client.post(
            f"{self.line_path}/create",
            {
                "vals_list": [values],
            },
        )
    
    def search_product(self, domain: list, fields: list) -> list:
        return self.client.post(
            f"{self.product_path}/search_read",
            {
                "domain": domain,
                "fields": fields
                },
        )

    def resolve_products_by_sku(self, skus: list) -> dict:
        """
        Recibe lista de SKUs y devuelve {sku: product_id}.
        SKUs no encontrados no aparecen en el dict — el caller decide qué hacer.
        """
        if not skus:
            return {}
        products = self.search_product(
            domain=[("default_code", "in", list(set(skus)))],
            fields=["id", "default_code"],
        )
        return {p["default_code"]: p["id"] for p in products if p.get("default_code")}

    def unlink(self, ids: list) -> bool:
        if not ids:
            return True
        return self.client.post(
            f"{self.base_path}/unlink",
            {"ids": ids},
        )

    def unlink_line(self, ids: list) -> bool:
        if not ids:
            return True
        return self.client.post(
            f"{self.line_path}/unlink",
            {"ids": ids},
        )

    def read_quotation_by_name(self, name: str) -> Optional[dict]:
        """Lee una cotización Odoo a partir de su `name` (ej. 'S00004').

        Devuelve un dict con:
          - order: cabecera con id, name, state, partner_id, x_studio_vendedor,
                   date_order, validity_date, client_order_ref, note, totales.
          - lines: lista de líneas con product_id resuelto a default_code,
                   nombre, precio de lista e imagen.
        Devuelve None si no encuentra la cotización.
        """
        name = (name or "").strip()
        if not name:
            return None

        order_fields = [
            "id", "name", "state", "partner_id", "x_studio_vendedor",
            "date_order", "validity_date", "client_order_ref", "note",
            "amount_untaxed", "amount_total", "order_line",
        ]
        orders = self.client.post(
            f"{self.base_path}/search_read",
            {
                "domain": [("name", "=", name)],
                "fields": order_fields,
                "limit": 1,
            },
        )
        if not isinstance(orders, list) or not orders:
            return None
        order = orders[0]

        line_ids = order.get("order_line") or []
        lines: list = []
        if line_ids:
            line_fields = [
                "id", "product_id", "name", "product_uom_qty",
                "price_unit", "discount", "price_subtotal", "price_total",
            ]
            raw_lines = self.client.post(
                f"{self.line_path}/read",
                {"ids": line_ids, "fields": line_fields},
            )
            if isinstance(raw_lines, list):
                lines = raw_lines

        # Resolver product_id -> default_code, name, list_price desde Odoo
        product_ids = sorted({
            ln["product_id"][0]
            for ln in lines
            if isinstance(ln.get("product_id"), list) and ln["product_id"]
        })
        product_by_id: dict = {}
        if product_ids:
            product_rows = self.client.post(
                f"{self.product_path}/read",
                {
                    "ids": product_ids,
                    "fields": ["id", "default_code", "name", "list_price"],
                },
            )
            if isinstance(product_rows, list):
                product_by_id = {p["id"]: p for p in product_rows}

        # Imagen: tomar `image_url` desde el modelo Product local por SKU,
        # no desde Odoo (image_128).
        from infrastructure.models.products_db import Product
        codes = {
            (product_by_id.get(pid) or {}).get("default_code")
            for pid in product_ids
        }
        codes.discard(None)
        codes.discard("")
        image_by_code: dict = {}
        if codes:
            image_by_code = dict(
                Product.objects.filter(code__in=codes).values_list("code", "image_url")
            )

        for ln in lines:
            pid_pair = ln.get("product_id")
            product_id = pid_pair[0] if isinstance(pid_pair, list) and pid_pair else None
            product = product_by_id.get(product_id) or {}
            default_code = product.get("default_code") or ""
            ln["product_default_code"] = default_code
            ln["product_name"] = product.get("name") or (pid_pair[1] if isinstance(pid_pair, list) and len(pid_pair) > 1 else "")
            ln["product_list_price"] = product.get("list_price") or 0
            ln["product_image"] = image_by_code.get(default_code, "")

        return {"order": order, "lines": lines}

    def create_quotation(
        self,
        partner_id: int,
        lines: list,
        validity_date: Optional[str] = None,
        client_order_ref: Optional[str] = None,
        note: Optional[str] = None,
        salesperson_code: Optional[str] = None,
    ) -> dict:
        """
        Crea una sale.order en estado 'draft' (cotización) con sus líneas.

        lines: [{ "default_code", "quantity", "price_unit", "discount"?, "description"? }, ...]

        Flujo:
          1. Resolver SKU → product_id (1 viaje a Odoo).
          2. Si faltan SKUs en Odoo, levantar ValueError listando los faltantes.
          3. Intentar crear order + lines embebidas en 1 sola llamada.
          4. Si Odoo rechaza el formato embebido, fallback: crear order vacía + line por line.
          5. Rollback parcial: si una línea falla en modo fallback, unlink de la order.
        """
        skus = [ln["default_code"] for ln in lines]
        sku_to_id = self.resolve_products_by_sku(skus)

        missing = sorted({s for s in skus if s not in sku_to_id})
        if missing:
            raise ValueError(f"SKUs no encontrados en Odoo: {missing}")

        line_vals = [
            _build_line_vals(ln, sku_to_id[ln["default_code"]])
            for ln in lines
        ]

        order_vals = {"partner_id": partner_id}
        if validity_date:
            order_vals["validity_date"] = validity_date
        if client_order_ref:
            order_vals["client_order_ref"] = client_order_ref
        if note:
            order_vals["note"] = note
        if salesperson_code:
            order_vals["x_studio_vendedor"] = salesperson_code

        # Intento 1: crear todo en una sola llamada con order_line embebidas
        embedded_vals = {
            **order_vals,
            "order_line": [[0, 0, lv] for lv in line_vals],
        }
        try:
            ids = self.client.post(
                f"{self.base_path}/create",
                {"vals_list": [embedded_vals]},
            )
            order_id = ids[0] if isinstance(ids, list) else ids
        except Exception:
            # Intento 2 (fallback): order vacía + create_line por cada línea
            order_id = self._create_with_separate_lines(order_vals, line_vals)

        # Leer el name para devolverlo
        name = None
        try:
            read_result = self.read([order_id], ["name"])
            if isinstance(read_result, list) and read_result:
                name = read_result[0].get("name")
        except Exception:
            pass

        return {"order_id": order_id, "name": name}

    def update_quotation(
        self,
        name: str,
        lines: list,
        *,
        partner_id: Optional[int] = None,
        validity_date: Optional[str] = None,
        client_order_ref: Optional[str] = None,
        note: Optional[str] = None,
        salesperson_code: Optional[str] = None,
    ) -> dict:
        """Actualiza una cotización existente (búsqueda por `name`).

        Sólo permitido en estado 'draft' o 'sent'. Estrategia para las líneas:
        reemplazo total (clear+add) — más simple y predecible que diffear, y
        evita estados inconsistentes si el usuario añadió/quitó/editó filas.

        Flujo:
          1. search_read por name → id, state, order_line.
          2. Validar state ∈ (draft, sent).
          3. Resolver SKU → product_id; faltantes → ValueError.
          4. Intento 1: write con `order_line: [(5,0,0), (0,0,vals)...]`.
          5. Fallback: write cabecera + unlink líneas viejas + create_line por cada nueva.
        """
        name = (name or "").strip()
        if not name:
            raise ValueError("Falta el nombre de la cotización a actualizar.")

        orders = self.client.post(
            f"{self.base_path}/search_read",
            {
                "domain": [("name", "=", name)],
                "fields": ["id", "state", "order_line"],
                "limit": 1,
            },
        )
        if not isinstance(orders, list) or not orders:
            raise ValueError(f"Cotización no encontrada en Odoo: {name}")
        order = orders[0]
        order_id = order["id"]
        if order.get("state") not in ("draft", "sent"):
            raise ValueError(
                f"No se puede modificar la cotización {name} en estado '{order.get('state')}'."
            )

        skus = [ln["default_code"] for ln in lines]
        sku_to_id = self.resolve_products_by_sku(skus)
        missing = sorted({s for s in skus if s not in sku_to_id})
        if missing:
            raise ValueError(f"SKUs no encontrados en Odoo: {missing}")

        line_vals = [
            _build_line_vals(ln, sku_to_id[ln["default_code"]])
            for ln in lines
        ]

        header_vals: dict = {}
        if partner_id:
            header_vals["partner_id"] = partner_id
        if validity_date:
            header_vals["validity_date"] = validity_date
        if client_order_ref is not None:
            header_vals["client_order_ref"] = client_order_ref
        if note is not None:
            header_vals["note"] = note
        if salesperson_code is not None:
            header_vals["x_studio_vendedor"] = salesperson_code

        embedded_vals = {
            **header_vals,
            "order_line": [[5, 0, 0]] + [[0, 0, lv] for lv in line_vals],
        }
        try:
            self.write([order_id], embedded_vals)
        except Exception:
            if header_vals:
                self.write([order_id], header_vals)
            old_line_ids = order.get("order_line") or []
            if old_line_ids:
                try:
                    self.unlink_line(old_line_ids)
                except Exception:
                    pass
            for lv in line_vals:
                self.create_line({**lv, "order_id": order_id})

        return {"order_id": order_id, "name": name}

    def _create_with_separate_lines(self, order_vals: dict, line_vals: list) -> int:
        created = self.client.post(
            f"{self.base_path}/create",
            {"vals_list": [order_vals]},
        )
        order_id = created[0] if isinstance(created, list) else created

        try:
            for lv in line_vals:
                self.create_line({**lv, "order_id": order_id})
        except Exception:
            try:
                self.unlink([order_id])
            except Exception:
                pass
            raise

        return order_id


def _build_line_vals(line: dict, product_id: int) -> dict:
    vals = {
        "product_id": product_id,
        "product_uom_qty": line["quantity"],
        "price_unit": line["price_unit"],
    }
    if line.get("discount"):
        vals["discount"] = line["discount"]
    if line.get("description"):
        vals["name"] = line["description"]
    return vals