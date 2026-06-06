"""Orquestación de creación/actualización de clientes: Odoo primero, DB inox después.

Regla del flujo:
  1. Crear/actualizar en Odoo. Si falla, propagar excepción y NO tocar la DB.
  2. Si Odoo respondió OK, leer el cliente completo de Odoo para tener los
     ids de contactos y direcciones recién creados.
  3. Upsert en la DB de inox por `odoo_id` dentro de una transacción.
  4. Si la persistencia local falla, registrar el error y devolver
     `db_persisted=False` para que la capa de presentación pueda avisar.
"""

import logging
from typing import Optional

from django.db import transaction

from adapters.odoo.service.odoo_service_partner import PartnerOdooService
from infrastructure.models.customer_address_db import CustomerAddress
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
        addresses: Optional[list] = None,
    ) -> dict:
        odoo_result = self.partner_service.create_customer(
            customer=customer,
            contacts=contacts,
            addresses=addresses,
        )

        full = self.partner_service.read_customer_full(odoo_result["customer_id"])

        local = {"db_persisted": False, "db_error": None}
        if full:
            try:
                local_ids = self._persist_local(full)
                local = {"db_persisted": True, "db_error": None, **local_ids}
            except Exception as exc:
                logger.exception(
                    "Cliente persistido en Odoo (id=%s) pero falló la persistencia local",
                    odoo_result["customer_id"],
                )
                local = {"db_persisted": False, "db_error": str(exc)}

        return {**odoo_result, **local}

    @transaction.atomic
    def _persist_local(self, full: dict) -> dict:
        odoo_customer = full["customer"]
        customer_obj = self._upsert_customer(odoo_customer)

        contact_ids = []
        for c in full.get("contacts") or []:
            obj = self._upsert_contact(customer_obj, c)
            contact_ids.append(obj.id)

        address_ids = []
        for a in full.get("addresses") or []:
            obj = self._upsert_address(customer_obj, a)
            address_ids.append(obj.id)

        return {
            "local_customer_id": customer_obj.id,
            "local_contact_ids": contact_ids,
            "local_address_ids": address_ids,
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

    def _upsert_address(self, customer: Customer, data: dict) -> CustomerAddress:
        country_id, _ = _split_m2o(data.get("country_id"))
        state_id, _ = _split_m2o(data.get("state_id"))
        type_ = data.get("type") or CustomerAddress.OTHER
        if type_ not in dict(CustomerAddress.TYPE_CHOICES):
            type_ = CustomerAddress.OTHER

        defaults = {
            "customer": customer,
            "type": type_,
            "name": data.get("name") or "",
            "street": data.get("street") or "",
            "street2": data.get("street2") or "",
            "city": data.get("city") or "",
            "zip": data.get("zip") or "",
            "country_id": country_id,
            "state_id": state_id,
            "phone": data.get("phone") or "",
        }
        obj, _ = CustomerAddress.objects.update_or_create(
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
