from typing import Optional

from adapters.odoo.client.odoo_client import OdooAPIClient


class PartnerOdooService:
    def __init__(self, client: OdooAPIClient):
        self.client = client
        self.base_path = "/json/2/res.partner"

    def search_read(self, domain: list, fields: list) -> list:
        return self.client.post(
            f"{self.base_path}/search_read",
            {"domain": domain, "fields": fields},
        )

    def find_by_vat(self, vat: str) -> Optional[dict]:
        if not vat:
            return None
        result = self.client.post(
            f"{self.base_path}/search_read",
            {
                "domain": [("vat", "=", vat)],
                "fields": ["id", "name", "vat", "email"],
                "limit": 1,
            },
        )
        return result[0] if isinstance(result, list) and result else None

    def search_customers(self, query: str, limit: int = 10) -> list:
        """Buscar clientes raíz (sin parent) por VAT o nombre, para autocompletar."""
        query = (query or "").strip()
        if not query:
            return []
        domain = [
            ("parent_id", "=", False),
            "|",
            ("vat", "ilike", query),
            ("name", "ilike", query),
        ]
        result = self.client.post(
            f"{self.base_path}/search_read",
            {
                "domain": domain,
                "fields": ["id", "name", "vat", "email", "phone", "is_company"],
                "limit": limit,
            },
        )
        return result if isinstance(result, list) else []

    def read_customer_full(self, customer_id: int) -> Optional[dict]:
        """Leer un cliente raíz junto con sus contactos y direcciones hijas.

        Devuelve un dict con keys: customer, contacts (lista), addresses (lista).
        contacts incluye sólo registros con type=contact; addresses incluye los
        tipos invoice/delivery/other. El orden de hijos es el natural de Odoo,
        por lo que el frontend puede tomar siempre el primero.
        """
        if not customer_id:
            return None
        customer_fields = [
            "id", "name", "is_company", "vat", "email", "phone",
            "website", "comment", "street", "street2", "city", "zip",
            "country_id", "state_id", "child_ids",
        ]
        rows = self.client.post(
            f"{self.base_path}/read",
            {"ids": [customer_id], "fields": customer_fields},
        )
        if not isinstance(rows, list) or not rows:
            return None
        customer = rows[0]

        child_ids = customer.get("child_ids") or []
        children: list = []
        if child_ids:
            child_fields = [
                "id", "name", "type", "function", "email", "phone",
                "street", "street2", "city", "zip", "country_id", "state_id",
            ]
            child_rows = self.client.post(
                f"{self.base_path}/read",
                {"ids": child_ids, "fields": child_fields},
            )
            if isinstance(child_rows, list):
                children = child_rows

        contacts = [c for c in children if c.get("type") == "contact"]
        addresses = [c for c in children if c.get("type") in ("invoice", "delivery", "other")]

        return {
            "customer": customer,
            "contacts": contacts,
            "addresses": addresses,
        }

    def create_partner(self, values: dict) -> int:
        result = self.client.post(
            f"{self.base_path}/create",
            {"vals_list": [values]},
        )
        if isinstance(result, list) and result:
            return result[0]
        if isinstance(result, int):
            return result
        raise RuntimeError(f"Unexpected Odoo create response: {result!r}")

    def write_partner(self, ids: list, values: dict) -> bool:
        return self.client.post(
            f"{self.base_path}/write",
            {"ids": ids, "vals": values},
        )

    def unlink(self, ids: list) -> bool:
        if not ids:
            return True
        return self.client.post(
            f"{self.base_path}/unlink",
            {"ids": ids},
        )

    def create_customer(
        self,
        customer: dict,
        contacts: Optional[list] = None,
    ) -> dict:
        """Crear cliente raíz y, opcionalmente, su contacto principal.

        - La dirección (street/street2/city/zip/state_id/country_id) viaja
          en `customer`, NO como partner hijo: se guarda en la cabecera del
          res.partner raíz, no como una "dirección" secundaria.
        - `contacts` admite 0 o 1 item. Si es persona natural, debe ser 0
          (validado en serializer). Si es empresa con contacto, se crea como
          res.partner hijo con type='contact'.
        """
        contacts = contacts or []

        existing_partner = self.find_by_vat(customer.get("vat"))
        if existing_partner:
            customer_id = existing_partner["id"]
            updates = _non_empty(customer)
            if updates:
                self.write_partner([customer_id], updates)
            existing = True
        else:
            customer_id = self.create_partner(_non_empty(customer))
            existing = False

        contact_ids: list = []
        try:
            for contact in contacts:
                values = {**_non_empty(contact), "parent_id": customer_id, "type": "contact"}
                contact_ids.append(self.create_partner(values))
        except Exception:
            cleanup = [*contact_ids]
            if not existing:
                cleanup.insert(0, customer_id)
            if cleanup:
                try:
                    self.unlink(cleanup)
                except Exception:
                    pass
            raise

        return {
            "existing": existing,
            "customer_id": customer_id,
            "contact_ids": contact_ids,
        }

    def update_customer(
        self,
        customer_id: int,
        customer: dict,
        contact: Optional[dict] = None,
    ) -> dict:
        """Actualizar cabecera del partner y upsertar el contacto principal.

        - `customer` viaja completo (incluida dirección) y se aplica con write.
        - `contact`: si el partner ya tiene hijos type='contact', se actualiza
          el primero (upsert sobre el "contacto principal"). Si no hay ninguno
          y el payload trae contacto, se crea. Si el payload no trae contacto,
          no se toca nada.
        """
        if not customer_id:
            raise ValueError("Falta customer_id para actualizar el cliente.")

        updates = _non_empty(customer)
        if updates:
            self.write_partner([customer_id], updates)

        contact_id: Optional[int] = None
        if contact:
            existing_children = self.client.post(
                f"{self.base_path}/search_read",
                {
                    "domain": [
                        ("parent_id", "=", customer_id),
                        ("type", "=", "contact"),
                    ],
                    "fields": ["id"],
                    "limit": 1,
                    "order": "id asc",
                },
            )
            contact_vals = _non_empty(contact)
            if isinstance(existing_children, list) and existing_children:
                contact_id = existing_children[0]["id"]
                if contact_vals:
                    self.write_partner([contact_id], contact_vals)
            else:
                values = {**contact_vals, "parent_id": customer_id, "type": "contact"}
                contact_id = self.create_partner(values)

        return {
            "customer_id": customer_id,
            "contact_id": contact_id,
        }


def _non_empty(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "", [])}
