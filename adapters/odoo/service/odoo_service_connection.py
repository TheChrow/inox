from adapters.odoo.client.odoo_client import OdooAPIClient


class OdooConnectionService:
    def __init__(self, client: OdooAPIClient):
        self.client = client
        self.base_path = "/json/2/res.users"

    def ping(self) -> dict:
        try:
            users = self.client.post(
                f"{self.base_path}/search_read",
                {
                    "domain": [],
                    "fields": ["id", "login"],
                    "limit": 1,
                },
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        user = users[0] if isinstance(users, list) and users else None
        return {
            "ok": True,
            "db": self.client.db,
            "base_url": self.client.baseurl,
            "user": user,
        }
