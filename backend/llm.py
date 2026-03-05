import re
from typing import Tuple

import requests

from .config import settings
from .logger_config import logger


class LLMError(Exception):
    """Raised when an LLM provider call fails or returns invalid data."""


def _get_ollama_config() -> Tuple[str, str]:
    return settings.ollama_url, settings.ollama_model

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
- Always include a LIMIT clause (e.g. LIMIT 100) unless the user explicitly asks for fewer rows.

"""

def _call_ollama(prompt: str) -> str:
    url, model = _get_ollama_config()

    try:
        response = requests.post(
            url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,  # we want the full response at once
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        # handle network/connection errors: like connection refused, timeout, etc.
        logger.error("LLM request to Ollama failed: %s", exc)
        raise LLMError("LLM provider is unavailable") from exc # raising an exception stops normal execution flow and propagates the error up the call stack

    # this line ain't reached if the above exception was raised, but in try/except where no raise is used, the code below would still execute
    if response.status_code != 200:
        # handle HTTP errors returned by the server: like 404, 500, etc. 
        logger.error(
            "LLM request failed with status %s: %s",
            response.status_code,
            response.text[:500],
        )
        raise LLMError("LLM provider returned an error response")

    print(response)
    # {
    # "response": "SELECT * FROM users WHERE age > 21 LIMIT 100;"
    # }

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Failed to decode LLM JSON response: %s", exc)
        raise LLMError("LLM provider returned invalid JSON") from exc

    content = data.get("response") # content = "SELECT * FROM users WHERE age > 21 LIMIT 100;"
    if not isinstance(content, str):
        logger.error("LLM response missing 'response' field: %s", data)
        raise LLMError("LLM provider returned an unexpected payload")

    text = content.strip()
    logger.info("LLM call succeeded (chars=%d)", len(text))
    return text # text = "SELECT * FROM users WHERE age > 21 LIMIT 100;"


def call_llm(prompt: str) -> str:
    """Entry point for all LLM calls, using configured provider."""
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return _call_ollama(prompt)

    # Future providers (e.g. openai) can be implemented here.
    raise LLMError(f"Unsupported LLM provider: {settings.llm_provider}")


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

    sql = clean_sql_output(call_llm(prompt))
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
        sql = clean_sql_output(call_llm(repair_prompt))

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

    return clean_sql_output(call_llm(prompt))

def generate_insights(df_preview: str) -> str:
    prompt = f"""
    You're a data analyst.
    Provide short insights about trends, outliers, or patterns.

    Dataset preview: {df_preview}

    Keep the answer concise.
    """

    return call_llm(prompt)
    
