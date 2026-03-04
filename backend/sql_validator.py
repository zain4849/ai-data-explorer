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

def validate_sql(sql: str) -> bool:
    sql_lower = sql.strip().lower()

    # Must start with an ALLOWED_KEYWORD
    if not any(sql_lower.startswith(keyword) for keyword in ALLOWED_KEYWORDS):
        raise ValueError("Only SELECT queries are allowed.")

    # Must not have any FORBIDDEN_KEYWORDS
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_lower:
            raise ValueError(f"Forbidden keyword detected : {keyword}")

    return True