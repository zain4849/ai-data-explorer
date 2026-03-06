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
    sql_stripped = sql.strip()

    # Disallow multiple statements – only a single optional trailing ';' is allowed.
    if ";" in sql_stripped[:-1]:
        raise ValueError("Multiple SQL statements are not allowed.")

    # Ignore a single trailing semicolon for validation purposes.
    if sql_stripped.endswith(";"):
        sql_core = sql_stripped[:-1].rstrip()
    else:
        sql_core = sql_stripped

    sql_lower = sql_core.lower()

    # Must start with an ALLOWED_KEYWORD
    if not any(sql_lower.startswith(keyword) for keyword in ALLOWED_KEYWORDS):
        raise ValueError("Only SELECT queries are allowed.")

    # Must not have any FORBIDDEN_KEYWORDS
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_lower:
            raise ValueError(f"Forbidden keyword detected : {keyword}")

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, sql_core, flags=re.IGNORECASE):
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
    has_trailing_semicolon = sql_stripped.endswith(";")

    # Work on the core query without a trailing semicolon.
    if has_trailing_semicolon:
        sql_core = sql_stripped[:-1].rstrip()
    else:
        sql_core = sql_stripped

    sql_lower = sql_core.lower()

    # If a LIMIT already exists, return the original SQL unchanged.
    if re.search(r"\blimit\b", sql_lower):
        return sql_stripped

    limited_sql = f"{sql_core} LIMIT {default_limit}"

    if has_trailing_semicolon:
        limited_sql += ";"

    return limited_sql
