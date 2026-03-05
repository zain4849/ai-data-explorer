import requests
import re

OLLAMA_URL = "http://localhost:11434/api/generate" # requres POST request
MODEL_NAME = "phi3"

SQL_RULES = """
- Only output valid SQL.
- Return only raw SQL as plain text.
- Don't explain.
- Don't use markdown.
- Don't use markdown fences.
- Don't include explanations or any text before/after SQL.
- Don't use backticks.
- Do not add SQL comments.
- Respect column data types.
- Never compare TEXT/VARCHAR columns directly to numeric literals.

"""

def call_ollama(nl_query: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": nl_query,
            "stream": False # We want the full response at once, not a stream of tokens aka bit by bit
        },
        timeout=60
    )

    return response.json()["response"].strip()


def clean_sql_output(raw_sql: str) -> str:
    sql = raw_sql.strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)
    # Remove SQL comments so only executable SQL is returned.
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    return sql.strip()

def has_unresolved_placeholders(sql: str) -> bool:
    patterns = [
        r"\[[^\]]+\]",
        r"<[^>]+>",
        r"\bTODO\b",
        r"\?\?\?",
    ]
    return any(re.search(pattern, sql, flags=re.IGNORECASE) for pattern in patterns)


def _build_schema_text(schema_cols: list[dict[str, str]]) -> str:
    lines = []
    for col in schema_cols:
        known_values = col.get("known_values")
        if known_values:
            values_text = ", ".join([repr(value) for value in known_values]) # ["'pending'", "'approved'", "'rejected'"] ", ".join -> "'pending', 'approved', 'rejected'"
            lines.append(f"- {col['name']} ({col['type']}), known_values: [{values_text}]") # status (TEXT), known_values: ['pending', 'approved', 'rejected']
        else:
            lines.append(f"- {col['name']} ({col['type']})")

        # lines = [
        #    "- id (INTEGER)",
        #    "- username (TEXT)",
        #    "- age (INTEGER)",
        #    "- status (TEXT), known_values: ['pending', 'approved', 'rejected']"
        # ]
    
    return "\n".join(lines)

    # - id (INTEGER)
    # - username (TEXT)
    # - age (INTEGER)
    # - status (TEXT), known_values: ['pending', 'approved', 'rejected']



def generate_sql(nl_query: str, schema_cols: list[dict[str, str]]) -> str:
    columns_text = _build_schema_text(schema_cols)

    prompt = f"""
    You convert natural language into DuckDB SQL queries.
    The table name is 'data'.
    Available columns and types:
    {columns_text}

    Rules:
    {SQL_RULES}

    User request: {nl_query}
    """

    sql = clean_sql_output(call_ollama(prompt))
    if has_unresolved_placeholders(sql):
        repair_prompt = f"""
        Rewrite the SQL below into executable DuckDB SQL.
        Keep intent the same, but remove placeholders and assumptions not present in the request.
        Table name is 'data'.
        Available columns and types:
        {columns_text}

        Rules:
        {SQL_RULES}

        User request: {nl_query}
        SQL to rewrite:
        {sql}
        """
        sql = clean_sql_output(call_ollama(repair_prompt))

    return sql


def repair_sql(
    nl_query: str,
    schema_cols: list[dict[str, str]],
    bad_sql: str,
    db_error: str,
) -> str:
    columns_text = _build_schema_text(schema_cols)

    prompt = f"""
    Fix this DuckDB SQL so it executes correctly.
    The table name is 'data'.
    Available columns and types:
    {columns_text}

    User request: {nl_query}
    Broken SQL: {bad_sql}
    DuckDB error: {db_error}

    Rules:
    {SQL_RULES}
    """

    return clean_sql_output(call_ollama(prompt))

def generate_insights(df_preview: str) -> str:
    prompt = f"""
    You're a data analyst.
    Provide short insights about trends, outliers, or patterns.

    Dataset preview: {df_preview}

    Keep the answer concise.
    """

    return call_ollama(prompt)
    
