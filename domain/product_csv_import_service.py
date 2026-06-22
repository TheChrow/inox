"""Carga masiva de productos vía CSV.

Estrategia: upsert por `code`. Cada fila se procesa de forma independiente
dentro de un savepoint, de modo que un error en una fila no aborta la carga
del resto. Devuelve un resumen con creados, actualizados y errores por
número de línea (1 = cabecera).
"""

import csv
import io
from dataclasses import dataclass, field
from typing import IO, Iterable

from django.db import transaction

from infrastructure.models.products_db import Product


REQUIRED_COLUMNS = (
    "code",
    "name",
    "list_price",
    "sale_price",
    "product_url",
    "max_store_discount",
    "max_project_discount",
)

OPTIONAL_COLUMNS = (
    "image_url",
    "total_stock",
    "brand",
    "cost",
    "is_discontinued",
    "is_inactive",
    "tree_type",
    "certification",
)

ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

FLOAT_FIELDS = {
    "list_price",
    "sale_price",
    "max_store_discount",
    "max_project_discount",
    "cost",
}

INT_FIELDS = {"total_stock"}


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    errors: list[tuple[int, str]] = field(default_factory=list)

    @property
    def total_ok(self) -> int:
        return self.created + self.updated


class CsvFormatError(Exception):
    """Errores estructurales del archivo (cabecera ausente, encoding, etc.)."""


def _decode(file_obj: IO[bytes]) -> Iterable[str]:
    raw = file_obj.read()
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return io.StringIO(raw.decode(encoding))
        except UnicodeDecodeError:
            continue
    raise CsvFormatError("No se pudo decodificar el archivo (probar UTF-8).")


def _coerce(field_name: str, raw_value: str):
    value = (raw_value or "").strip()
    if field_name in FLOAT_FIELDS:
        if value == "":
            raise ValueError(f"'{field_name}' es obligatorio numérico")
        try:
            return float(value.replace(",", "."))
        except ValueError:
            raise ValueError(f"'{field_name}' no es un número válido: {value!r}")
    if field_name in INT_FIELDS:
        if value == "":
            return 0
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"'{field_name}' no es un entero válido: {value!r}")
    return value


def _detect_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        first_line = sample.splitlines()[0] if sample else ""
        for candidate in (";", "\t", "|"):
            if candidate in first_line and first_line.count(candidate) > first_line.count(","):
                return candidate
        return ","


def import_products_from_csv(file_obj: IO[bytes]) -> ImportResult:
    stream = _decode(file_obj)
    sample = stream.read(4096)
    stream.seek(0)
    delimiter = _detect_delimiter(sample)
    reader = csv.DictReader(stream, delimiter=delimiter)
    if reader.fieldnames is None:
        raise CsvFormatError("El archivo está vacío o no tiene cabecera.")

    headers = {h.strip() for h in reader.fieldnames}
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        raise CsvFormatError(
            "Faltan columnas obligatorias: " + ", ".join(missing)
        )

    result = ImportResult()

    for row_num, row in enumerate(reader, start=2):
        try:
            with transaction.atomic():
                _upsert_row(row, result)
        except Exception as exc:
            result.errors.append((row_num, str(exc)))

    return result


def _upsert_row(row: dict, result: ImportResult) -> None:
    code = (row.get("code") or "").strip()
    if not code:
        raise ValueError("'code' es obligatorio")

    defaults = {}
    for field_name in ALL_COLUMNS:
        if field_name == "code":
            continue
        if field_name not in row:
            continue
        raw = row.get(field_name)
        if raw is None:
            continue
        if field_name not in REQUIRED_COLUMNS and str(raw).strip() == "":
            continue
        defaults[field_name] = _coerce(field_name, raw)

    _, created = Product.objects.update_or_create(code=code, defaults=defaults)
    if created:
        result.created += 1
    else:
        result.updated += 1


def csv_template_bytes() -> bytes:
    """CSV de ejemplo descargable desde el admin."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(ALL_COLUMNS)
    writer.writerow([
        "LED-001",                         # code
        "Foco LED 9W",                     # name
        "9990",                            # list_price
        "8990",                            # sale_price
        "https://ejemplo.cl/p/led-001",    # product_url
        "10",                              # max_store_discount
        "15",                              # max_project_discount
        "https://ejemplo.cl/foco.jpg",     # image_url
        "100",                             # total_stock
        "Luminox",                         # brand
        "1500",                            # cost
        "0",                               # is_discontinued
        "NO",                              # is_inactive
        "DEFAULT",                         # tree_type
        "4",                               # certification
    ])
    return buf.getvalue().encode("utf-8-sig")
