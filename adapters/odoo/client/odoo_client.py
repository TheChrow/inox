import requests
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class OdooUnavailableError(requests.exceptions.RequestException):
    """Odoo respondió algo que no es la API (redirección o HTML), p. ej. base bloqueada."""


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
                allow_redirects=False,
            )

            if response.is_redirect:
                location = response.headers.get("Location", "")
                if "/_odoo/upgrade" in location:
                    detail = "la base de datos está bloqueada (suscripción vencida o actualización en curso)"
                else:
                    detail = f"redirigió a {location or 'una página desconocida'}"
                raise OdooUnavailableError(f"Odoo no está disponible: {detail}.")

            response.raise_for_status()

            try:
                data = response.json()
            except ValueError as exc:
                content_type = response.headers.get("Content-Type", "desconocido")
                raise OdooUnavailableError(
                    f"Odoo no está disponible: respondió {content_type} en vez de JSON (HTTP {response.status_code})."
                ) from exc

            # manejar JSON-RPC
            if path.startswith("/web/"):

                if data.get("error"):
                    raise Exception(data["error"])

                return data.get("result")

            return data

        except OdooUnavailableError:
            logger.error(f"Odoo no disponible: {url} - {payload}")
            raise

        except requests.exceptions.HTTPError as exc:
            body_text = ""
            if exc.response is not None:
                try:
                    body_text = exc.response.text
                except Exception:
                    body_text = ""
            logger.exception(f"Odoo API error: {url} - {payload} - body={body_text}")
            raise requests.exceptions.HTTPError(
                f"{exc} | odoo_body={body_text}",
                response=exc.response,
                request=exc.request,
            ) from exc

        except requests.exceptions.RequestException:
            logger.exception(f"Odoo API error: {url} - {payload}")
            raise