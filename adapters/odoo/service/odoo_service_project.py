
from adapters.odoo.client.odoo_client import OdooAPIClient


class OdooProjectService:

    def __init__(self, client: OdooAPIClient):
        self.client = client
        self.base_path = "/json/2/project.project"


    def search_read_project(self, domain: list, fields: list):
        return self.client.post(
            f"{self.base_path}/search_read",
            {
                "domain": domain,
                "fields": fields,
            },
        )