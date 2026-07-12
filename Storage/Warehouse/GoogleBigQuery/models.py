from __future__ import annotations

from google.cloud.bigquery import SchemaField  # type: ignore[import-untyped]

_PYTHON_TO_BQ: dict[type, str] = {
    str: "STRING",
    int: "INTEGER",
    float: "FLOAT",
    bool: "BOOLEAN",
    bytes: "BYTES",
}


def map_schema(schema: dict[str, type]) -> list[SchemaField]:
    """Convert a ``{column_name: python_type}`` dict into BigQuery SchemaFields."""
    fields: list[SchemaField] = []
    for name, py_type in schema.items():
        bq_type = _PYTHON_TO_BQ.get(py_type, "STRING")
        fields.append(SchemaField(name, bq_type))
    return fields
