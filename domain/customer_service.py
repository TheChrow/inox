"""Orquestación de creación/actualización de clientes: Odoo primero, DB inox después.

Regla del flujo:
  1. Crear/actualizar en Odoo. Si falla, propagar excepción y NO tocar la DB.
  2. Si Odoo respondió OK, leer el cliente completo de Odoo para tener los
     ids de contactos recién creados.
  3. Upsert en la DB de inox por `odoo_id` dentro de una transacción.
  4. Si la persistencia local falla, registrar el error y devolver
     `db_persisted=False` para que la capa de presentación pueda avisar.

La dirección (street/city/zip/state_id/country_id) vive en la cabecera del
res.partner raíz en Odoo y en los mismos campos del modelo Customer local.
CustomerAddress queda reservado para direcciones secundarias (no se puebla
desde este flujo).
"""

import logging
from typing import Optional

from django.db import transaction

from adapters.odoo.service.odoo_service_partner import PartnerOdooService
from infrastructure.models.customer_contact_db import CustomerContact
from infrastructure.models.customer_db import Customer

logger = logging.getLogger(__name__)


class CustomerService:
    def __init__(self, partner_service: PartnerOdooService):
        self.partner_service = partner_service

    def create_or_update(
        self,
        customer: dict,
        contacts: Optional[list] = None,
    ) -> dict:
        odoo_result = self.partner_service.create_customer(
            customer=customer,
            contacts=contacts,
        )
        return {**odoo_result, **self._persist_after_odoo(odoo_result["customer_id"])}

    def update_existing(
        self,
        customer_id: int,
        customer: dict,
        contact: Optional[dict] = None,
    ) -> dict:
        odoo_result = self.partner_service.update_customer(
            customer_id=customer_id,
            customer=customer,
            contact=contact,
        )
        return {
            "existing": True,
            "customer_id": odoo_result["customer_id"],
            "contact_ids": [odoo_result["contact_id"]] if odoo_result.get("contact_id") else [],
            **self._persist_after_odoo(odoo_result["customer_id"]),
        }

    def _persist_after_odoo(self, customer_id: int) -> dict:
        full = self.partner_service.read_customer_full(customer_id)
        if not full:
            return {"db_persisted": False, "db_error": "No se pudo releer el cliente desde Odoo."}

        try:
            return {"db_persisted": True, "db_error": None, **self._persist_local(full)}
        except Exception as exc:
            logger.exception(
                "Cliente persistido en Odoo (id=%s) pero falló la persistencia local",
                customer_id,
            )
            return {"db_persisted": False, "db_error": str(exc)}

    @transaction.atomic
    def _persist_local(self, full: dict) -> dict:
        odoo_customer = full["customer"]
        customer_obj = self._upsert_customer(odoo_customer)

        contact_ids = []
        for c in full.get("contacts") or []:
            obj = self._upsert_contact(customer_obj, c)
            contact_ids.append(obj.id)

        return {
            "local_customer_id": customer_obj.id,
            "local_contact_ids": contact_ids,
        }

    def _upsert_customer(self, data: dict) -> Customer:
        country_id, _ = _split_m2o(data.get("country_id"))
        state_id, _ = _split_m2o(data.get("state_id"))

        defaults = {
            "name": data.get("name") or "",
            "is_company": bool(data.get("is_company")),
            "vat": data.get("vat") or "",
            "email": data.get("email") or "",
            "phone": data.get("phone") or "",
            "website": data.get("website") or "",
            "comment": data.get("comment") or "",
            "street": data.get("street") or "",
            "street2": data.get("street2") or "",
            "city": data.get("city") or "",
            "zip": data.get("zip") or "",
            "country_id": country_id,
            "state_id": state_id,
        }
        obj, _ = Customer.objects.update_or_create(
            odoo_id=data["id"], defaults=defaults,
        )
        return obj

    def _upsert_contact(self, customer: Customer, data: dict) -> CustomerContact:
        defaults = {
            "customer": customer,
            "name": data.get("name") or "",
            "function": data.get("function") or "",
            "email": data.get("email") or "",
            "phone": data.get("phone") or "",
        }
        obj, _ = CustomerContact.objects.update_or_create(
            odoo_id=data["id"], defaults=defaults,
        )
        return obj


def _split_m2o(value):
    """Odoo devuelve many2one como [id, display_name] o False. Normaliza a (id, name)."""
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return value[0], value[1]
    if isinstance(value, int):
        return value, None
    return None, None
