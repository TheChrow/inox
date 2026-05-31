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

    def create_quotation(
        self,
        partner_id: int,
        lines: list,
        validity_date: Optional[str] = None,
        client_order_ref: Optional[str] = None,
        note: Optional[str] = None,
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