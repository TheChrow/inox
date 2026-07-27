import html
import logging
import re
from typing import Optional

from django.utils.html import strip_tags

from adapters.odoo.client.odoo_client import OdooAPIClient

logger = logging.getLogger(__name__)

# Campo Chileno (l10n_cl) para "Descripción de la actividad" (giro).
# Se aplica sólo si el módulo l10n_cl está instalado en el Odoo destino;
# el servicio detecta el error de campo inexistente y reintenta sin él.
ACTIVITY_FIELD = "l10n_cl_activity_description"

# Chile en res.country (defecto usado por el frontend).
CHILE_COUNTRY_ID = 46


class PartnerOdooService:
    def __init__(self, client: OdooAPIClient):
        self.client = client
        self.base_path = "/json/2/res.partner"
        self._activity_field_supported: Optional[bool] = None

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
        base_fields = [
            "id", "name", "is_company", "vat", "email", "phone",
            "website", "comment", "ref", "street", "street2", "city", "zip",
            "country_id", "state_id", "child_ids",
        ]
        customer_fields = list(base_fields)
        included_activity = self._activity_field_supported is not False
        if included_activity:
            customer_fields.append(ACTIVITY_FIELD)
        try:
            rows = self.client.post(
                f"{self.base_path}/read",
                {"ids": [customer_id], "fields": customer_fields},
            )
        except Exception as exc:
            if included_activity and _is_unknown_field_error(exc, ACTIVITY_FIELD):
                self._activity_field_supported = False
                included_activity = False
                rows = self.client.post(
                    f"{self.base_path}/read",
                    {"ids": [customer_id], "fields": base_fields},
                )
            else:
                raise
        if included_activity:
            self._activity_field_supported = True
        if not isinstance(rows, list) or not rows:
            return None
        customer = rows[0]
        customer["comment"] = _html_to_text(customer.get("comment"))
        raw_activity = customer.pop(ACTIVITY_FIELD, None)
        customer["activity_description"] = (raw_activity or "").strip() if isinstance(raw_activity, str) else ""

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
        payload = self._prepare_partner_values(values)
        return self._create_with_activity_fallback(payload)

    def write_partner(self, ids: list, values: dict) -> bool:
        payload = self._prepare_partner_values(values)
        return self._write_with_activity_fallback(ids, payload)

    def _create_with_activity_fallback(self, values: dict) -> int:
        try:
            result = self.client.post(
                f"{self.base_path}/create",
                {"vals_list": [values]},
            )
        except Exception as exc:
            fallback = self._strip_activity_on_unknown_field(values, exc)
            if fallback is None:
                raise
            result = self.client.post(
                f"{self.base_path}/create",
                {"vals_list": [fallback]},
            )
        if isinstance(result, list) and result:
            return result[0]
        if isinstance(result, int):
            return result
        raise RuntimeError(f"Unexpected Odoo create response: {result!r}")

    def _write_with_activity_fallback(self, ids: list, values: dict) -> bool:
        try:
            return self.client.post(
                f"{self.base_path}/write",
                {"ids": ids, "vals": values},
            )
        except Exception as exc:
            fallback = self._strip_activity_on_unknown_field(values, exc)
            if fallback is None:
                raise
            return self.client.post(
                f"{self.base_path}/write",
                {"ids": ids, "vals": fallback},
            )

    def _resolve_customer_relations(self, customer: dict) -> dict:
        """Convierte inputs "amigables" (region: str) en FKs que entiende Odoo.

        - Si viene `region` como texto y no viene `state_id`, intenta resolver
          el res.country.state que mejor calce (fuzzy, priorizando el country
          declarado en el payload; por defecto Chile).
        - Descarta `region` del dict resultante (no es campo de Odoo).
        - Si el input trae `state_id` explícito, tiene prioridad y no se toca.
        """
        if not isinstance(customer, dict):
            return customer
        out = dict(customer)
        region = out.pop("region", None)
        if not out.get("state_id") and region:
            country_id = out.get("country_id") or CHILE_COUNTRY_ID
            try:
                state_id = self.resolve_state_id(region, country_id=country_id)
            except Exception:
                logger.exception("No se pudo resolver la región '%s'", region)
                state_id = None
            if state_id:
                out["state_id"] = state_id
        return out

    def _prepare_partner_values(self, values: dict) -> dict:
        """Mapea claves de dominio a claves de Odoo antes de escribir."""
        out = dict(values)
        activity = out.pop("activity_description", None)
        if activity and self._activity_field_supported is not False:
            out[ACTIVITY_FIELD] = activity
        elif activity:
            # Sabemos que el campo no existe; caemos a `comment` (Notas internas)
            # para no perder la información capturada por el vendedor.
            existing_comment = out.get("comment")
            out["comment"] = existing_comment or activity
        return out

    def _strip_activity_on_unknown_field(self, values: dict, exc: Exception) -> Optional[dict]:
        if ACTIVITY_FIELD not in values:
            return None
        if not _is_unknown_field_error(exc, ACTIVITY_FIELD):
            return None
        self._activity_field_supported = False
        fallback = {k: v for k, v in values.items() if k != ACTIVITY_FIELD}
        # Preserva el giro en `comment` si el campo específico no está.
        activity = values.get(ACTIVITY_FIELD)
        if activity and not fallback.get("comment"):
            fallback["comment"] = activity
        return fallback

    def resolve_state_id(
        self,
        region_name: str,
        country_id: int = CHILE_COUNTRY_ID,
    ) -> Optional[int]:
        """Buscar res.country.state cuyo nombre coincida con `region_name`.

        Estrategia (en orden):
          1. Limpiar sufijos ("(CL)", "Región de", etc.) y probar match exacto.
          2. Match ilike parcial (contiene el término).
          3. Match por normalización (sin acentos, palabra por palabra).
        """
        name = (region_name or "").strip()
        if not name:
            return None

        # 1) Exacto sobre la versión limpia. Odoo devuelve el many2one como
        #    display_name ("Metropolitana (CL)"), pero el name real es
        #    "Metropolitana"; también atrapamos "Región Metropolitana", etc.
        cleaned = _strip_state_decoration(name)
        for candidate in _dedup([cleaned, name]):
            rows = self.client.post(
                "/json/2/res.country.state/search_read",
                {
                    "domain": [("country_id", "=", country_id), ("name", "=ilike", candidate)],
                    "fields": ["id", "name"],
                    "limit": 1,
                },
            )
            if isinstance(rows, list) and rows:
                return rows[0]["id"]

        # 2) Parcial (contiene)
        rows = self.client.post(
            "/json/2/res.country.state/search_read",
            {
                "domain": [("country_id", "=", country_id), ("name", "ilike", cleaned or name)],
                "fields": ["id", "name"],
                "limit": 5,
            },
        )
        if isinstance(rows, list) and rows:
            return _pick_best_state_match(cleaned or name, rows)

        # 3) Normalizado sobre la lista completa (16 regiones ≈ 1 query barata)
        all_rows = self.client.post(
            "/json/2/res.country.state/search_read",
            {
                "domain": [("country_id", "=", country_id)],
                "fields": ["id", "name"],
                "limit": 200,
            },
        )
        if isinstance(all_rows, list) and all_rows:
            return _pick_best_state_match(name, all_rows)
        return None

    def list_states(self, country_id: int = CHILE_COUNTRY_ID) -> list:
        rows = self.client.post(
            "/json/2/res.country.state/search_read",
            {
                "domain": [("country_id", "=", country_id)],
                "fields": ["id", "name"],
                "limit": 200,
                "order": "name asc",
            },
        )
        return rows if isinstance(rows, list) else []

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
        customer = self._resolve_customer_relations(customer)

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

        customer = self._resolve_customer_relations(customer)
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


def _html_to_text(value) -> str:
    """Aplanar HTML de Odoo (campos Html como res.partner.comment) a texto plano."""
    if not value:
        return ""
    return html.unescape(strip_tags(value)).strip()


def _is_unknown_field_error(exc: Exception, field: str) -> bool:
    """Detectar si el error de Odoo proviene de un campo inexistente.

    Odoo devuelve mensajes tipo "Invalid field 'x' on model 'res.partner'" o
    "Field 'x' does not exist". Buscamos el nombre del campo en el texto para
    no confundirnos con otros errores.
    """
    text = str(exc).lower()
    if field.lower() not in text:
        return False
    markers = ("invalid field", "does not exist", "unknown field", "no such field")
    return any(m in text for m in markers)


_ACCENT_MAP = str.maketrans({
    "á": "a", "à": "a", "ä": "a", "â": "a",
    "é": "e", "è": "e", "ë": "e", "ê": "e",
    "í": "i", "ì": "i", "ï": "i", "î": "i",
    "ó": "o", "ò": "o", "ö": "o", "ô": "o",
    "ú": "u", "ù": "u", "ü": "u", "û": "u",
    "ñ": "n",
    "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u", "Ñ": "n",
})


def _strip_state_decoration(name: str) -> str:
    """Sacar decoraciones típicas del nombre de una región.

    Ejemplos: "Metropolitana (CL)" -> "Metropolitana"; "Región Metropolitana"
    -> "Metropolitana"; "Región de la Araucanía" -> "Araucanía".
    """
    if not name:
        return ""
    v = re.sub(r"\s*\(.*?\)\s*", " ", name)
    v = re.sub(r"^\s*regi[oó]n(al)?\s+(de(l)?\s+)?", "", v, flags=re.IGNORECASE)
    return v.strip()


def _dedup(items):
    seen = set()
    out = []
    for it in items:
        key = (it or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out


def _normalize(name: str) -> str:
    if not name:
        return ""
    v = name.lower().translate(_ACCENT_MAP)
    # Quita sufijos tipo "(cl)", "región de", etc., para comparar núcleos.
    v = re.sub(r"\(.*?\)", " ", v)
    v = re.sub(r"\bregion(al)?\b", " ", v)
    v = re.sub(r"\bde(l)?\b", " ", v)
    v = re.sub(r"[^a-z0-9]+", " ", v)
    return " ".join(v.split())


def _pick_best_state_match(query: str, rows: list) -> Optional[int]:
    """Elegir el mejor match entre varias regiones candidatas.

    - Exacto normalizado gana.
    - Si no, el candidato cuya versión normalizada contenga (o esté contenida
      en) la del query.
    - Empate: primer resultado.
    """
    q = _normalize(query)
    if not q:
        return rows[0]["id"] if rows else None

    exact = [r for r in rows if _normalize(r.get("name", "")) == q]
    if exact:
        return exact[0]["id"]

    contains = [
        r for r in rows
        if q in _normalize(r.get("name", "")) or _normalize(r.get("name", "")) in q
    ]
    if contains:
        return contains[0]["id"]

    return rows[0]["id"]
