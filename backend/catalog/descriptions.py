"""AI-generated human-readable descriptions for tables and columns."""

from ..connectors.types import TableInfo
from ..llm import call_llm
from ..logger_config import logger


def generate_descriptions(tables: list[TableInfo]) -> dict[str, dict[str, str]]:
    """Generate AI descriptions for tables and their columns.

    Returns a nested dict: {table_name: {"__table__": "desc", col_name: "desc", ...}}
    """
    if not tables:
        return {}

    schema_text = _build_schema_summary(tables)
    prompt = f"""You are a data catalog assistant. Given the database schema below, produce a
short human-readable description (1 sentence) for each table and each column.

Return the output as a structured list with this format:
TABLE: <table_name> - <description>
  COLUMN: <column_name> - <description>

Schema:
{schema_text}
"""

    try:
        raw = call_llm(prompt)
        return _parse_descriptions(raw, tables)
    except Exception as exc:
        logger.warning("Failed to generate schema descriptions: %s", exc)
        return {}


def _build_schema_summary(tables: list[TableInfo]) -> str:
    lines = []
    for t in tables[:30]:
        cols_text = ", ".join(
            f"{c.name} ({c.data_type}{'PK' if c.is_pk else ''}{'->'+c.fk_reference if c.fk_reference else ''})"
            for c in t.columns[:50]
        )
        lines.append(f"Table: {t.qualified_name} [{t.row_count or '?'} rows] => {cols_text}")
    return "\n".join(lines)


def _parse_descriptions(raw: str, tables: list[TableInfo]) -> dict[str, dict[str, str]]:
    """Best-effort parse of the LLM response into structured descriptions."""
    result: dict[str, dict[str, str]] = {}
    current_table: str | None = None

    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        upper = line.upper()
        if upper.startswith("TABLE:"):
            rest = line[len("TABLE:"):].strip()
            parts = rest.split(" - ", 1)
            table_name = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            current_table = table_name
            result.setdefault(current_table, {})
            result[current_table]["__table__"] = desc

        elif upper.startswith("COLUMN:") and current_table:
            rest = line[len("COLUMN:"):].strip()
            parts = rest.split(" - ", 1)
            col_name = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            result.setdefault(current_table, {})
            result[current_table][col_name] = desc

    return result
