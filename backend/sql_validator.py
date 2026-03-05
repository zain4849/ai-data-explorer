import re

from .config import settings


FORBIDDEN_KEYWORDS = [
    "drop",
    "delete",
    "alter",
    "truncate",
    "insert",
    "update",
    "create",
    "rename",
]

ALLOWED_KEYWORDS = [
    "select",
    "with",
]

FORBIDDEN_PATTERNS = [
    r"\[[^\]]+\]",
    r"<[^>]+>",
    r"\bTODO\b",
    r"\?\?\?",
]


def validate_sql(sql: str) -> bool:
    sql_lower = sql.strip().lower()

    # Must start with an ALLOWED_KEYWORD
    if not any(sql_lower.startswith(keyword) for keyword in ALLOWED_KEYWORDS):
        raise ValueError("Only SELECT queries are allowed.")

    # Must not have any FORBIDDEN_KEYWORDS
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_lower:
            raise ValueError(f"Forbidden keyword detected : {keyword}")

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, sql, flags=re.IGNORECASE):
            raise ValueError("Unresolved placeholder token detected in SQL.")

    return True


def ensure_limit(sql: str, default_limit: int | None = None) -> str:
    """
    Ensure the SQL query has a LIMIT clause.

    If a LIMIT already exists, the SQL is returned unchanged.
    """
    if default_limit is None:
        default_limit = settings.default_query_limit

    sql_stripped = sql.strip()
    sql_lower = sql_stripped.lower()

    if " limit " in sql_lower or sql_lower.endswith(" limit"):
        return sql_stripped

    return f"{sql_stripped} LIMIT {default_limit}"
