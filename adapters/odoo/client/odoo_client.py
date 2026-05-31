import requests
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class OdooAPIClient:
    def __init__(self, config: dict):
        self.baseurl = config.get("base_url", "").rstrip("/")
        self.api_key = config.get("api_key")
        self.db = config.get("db")  # opcional

        self.session = requests.Session()
        self.timeout = config.get("timeout", 10)

        if not self.api_key:
            raise ValueError("API Key is required")

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # importante si Odoo es multi-db
        if self.db:
            headers["X-Odoo-Database"] = self.db
    
        return headers

    def post(self, path: str, payload=None):
        url = f"{self.baseurl}{path}"

        if path.startswith("/web/"):
            body = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": payload or {},
                "id": 1,
            }
        else:
            body = payload or {}

        try:
            response = self.session.post(
                url,
                json=body,
                headers=self._headers(),
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

            # manejar JSON-RPC
            if path.startswith("/web/"):

                if data.get("error"):
                    raise Exception(data["error"])

                return data.get("result")

            return data

        except requests.exceptions.RequestException:
            logger.exception(f"Odoo API error: {url} - {payload}")
            raise