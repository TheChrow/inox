import os

from adapters.odoo.client.odoo_client import OdooAPIClient


def get_odoo_client() -> OdooAPIClient:
    base_url = os.environ.get("ODOO_BASE_URL")
    api_key = os.environ.get("ODOO_API_KEY")
    db = os.environ.get("ODOO_DB")

    missing = [k for k, v in {
        "ODOO_BASE_URL": base_url,
        "ODOO_API_KEY": api_key,
        "ODOO_DB": db,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing Odoo env vars: {', '.join(missing)}")

    return OdooAPIClient({
        "base_url": base_url,
        "api_key": api_key,
        "db": db,
        "timeout": int(os.environ.get("ODOO_TIMEOUT", 10)),
    })
