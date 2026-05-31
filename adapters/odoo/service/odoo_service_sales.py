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