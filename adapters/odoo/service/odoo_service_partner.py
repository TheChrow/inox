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
        addresses: Optional[list] = None,
    ) -> dict:
        contacts = contacts or []
        addresses = addresses or []

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
        address_ids: list = []
        try:
            for contact in contacts:
                values = {**_non_empty(contact), "parent_id": customer_id, "type": "contact"}
                contact_ids.append(self.create_partner(values))

            for address in addresses:
                values = {**_non_empty(address), "parent_id": customer_id}
                values.pop("region", None)  # placeholder hasta que exista geo-service que resuelva a state_id
                address_ids.append(self.create_partner(values))
        except Exception:
            cleanup = [*contact_ids, *address_ids]
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
            "address_ids": address_ids,
        }


def _non_empty(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "", [])}
