from adapters.odoo.client.odoo_client import OdooAPIClient


class TaskService:
    def __init__(self, client: OdooAPIClient):
        self.client = client
        self.base_path = "/json/2/project.task"

    def search(self, domain: list):
        return self.client.post(
            f"{self.base_path}/search",
            {"domain": domain},
        )

    def read(self, ids: list, fields: list):
        return self.client.post(
            f"{self.base_path}/read",
            {
                "ids": ids,
                "fields": fields,
            },
        )

    def search_read(self, domain: list, fields: list):
        return self.client.post(
            f"{self.base_path}/search_read",
            {
                "domain": domain,
                "fields": fields,
            },
        )

    def create(self, values: dict):
        return self.client.post(
            f"{self.base_path}/create",
            {
                "vals_list": [values],
            },
        )
    
    def write_task(self, ids: list, values: dict):
        return self.client.post(
            f"{self.base_path}/write",
            {
                "ids": ids,
                "vals": values,
            },
        )