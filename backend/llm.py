import re

import requests

from .config import settings
from .logger_config import logger


class LLMError(
    Exception
):  # LLMError is a subclass of Exception, so it behaves like an exception. No extra code needed.
    """Raised when an LLM provider call fails or returns invalid data."""


def _get_ollama_config() -> tuple[str, str]:
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
- Do not end with a semicolon.
- Respect column data types.
- Never compare TEXT/VARCHAR columns directly to numeric literals.
- Always include a LIMIT clause (e.g. LIMIT 100) unless the user explicitly asks for fewer rows.
- When a column lists known_values, treat these as the only allowed literal values for that column; do not invent new categorical string values.
- Prefer using columns whose names closely match the user's request terms instead of inferring from loosely related text columns.
- Avoid using generic text columns with LIKE '%%...%%' filters when there is already a more specific structured column that represents the same concept.
- Keep queries as simple as possible. Only use columns directly relevant to the user's question.
- Every non-aggregated column in SELECT or ORDER BY must appear in GROUP BY. Do not reference bare columns outside GROUP BY unless they are inside an aggregate function.

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
        raise LLMError(
            "LLM provider is unavailable"
        ) from exc  # raising an exception stops normal execution flow and propagates the error up the call stack

    # this line ain't reached if the above exception was raised, but in try/except where no raise is used, the code below would still execute
    if response.status_code != 200:
        # handle HTTP errors returned by the server: like 404, 500, etc.
        logger.error(
            "LLM request failed with status %s: %s",
            response.status_code,
            response.text[:500],
        )
        raise LLMError("LLM provider returned an error response")

    # {
    # "response": "SELECT * FROM users WHERE age > 21 LIMIT 100;"
    # }

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Failed to decode LLM JSON response: %s", exc)
        raise LLMError("LLM provider returned invalid JSON") from exc

    content = data.get("response")  # content = "SELECT * FROM users WHERE age > 21 LIMIT 100;"
    if not isinstance(content, str):
        logger.error("LLM response missing 'response' field: %s", data)
        raise LLMError("LLM provider returned an unexpected payload")

    text = content.strip()
    logger.info("LLM call succeeded (chars=%d)", len(text))
    return text  # text = "SELECT * FROM users WHERE age > 21 LIMIT 100;"


def _call_openai_compatible(prompt: str, *, base_url: str | None = None, model: str | None = None) -> str:
    """
    Call an OpenAI-compatible Chat Completions API (OpenAI, Groq, etc.).

    Expected environment variables:
      - OPENAI_API_KEY or GROQ_API_KEY
      - OPENAI_API_BASE (optional; Groq default: https://api.groq.com/openai/v1)
      - OPENAI_MODEL (optional; Groq default: llama-3.3-70b-versatile)
    """
    api_key = settings.openai_api_key
    api_base = base_url or settings.openai_api_base
    model_name = model or settings.openai_model

    # Groq defaults when using groq provider
    if settings.llm_provider.lower() == "groq":
        api_base = api_base or "https://api.groq.com/openai/v1"
        model_name = model_name or "llama-3.3-70b-versatile"

    if not api_base:
        api_base = "https://api.openai.com/v1"
    if not model_name:
        model_name = "gpt-4o-mini"

    if not api_key:
        raise LLMError(
            "OPENAI_API_KEY or GROQ_API_KEY must be set for openai/groq provider. "
            "Get a free key at https://console.groq.com"
        )

    url = api_base.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a precise assistant. Follow the user's instructions exactly."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.RequestException as exc:
        logger.error("LLM request to OpenAI-compatible API failed: %s", exc)
        raise LLMError("LLM provider is unavailable") from exc

    if response.status_code != 200:
        logger.error(
            "LLM request failed with status %s: %s",
            response.status_code,
            response.text[:800],
        )
        raise LLMError("LLM provider returned an error response")

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Failed to decode LLM JSON response: %s", exc)
        raise LLMError("LLM provider returned invalid JSON") from exc

    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.error("Unexpected LLM payload shape: %s", data)
        raise LLMError("LLM provider returned an unexpected payload") from exc

    if not isinstance(content, str):
        raise LLMError("LLM provider returned an unexpected payload")

    text = content.strip()
    logger.info("LLM call succeeded (chars=%d)", len(text))
    return text


def _call_gemini(prompt: str) -> str:
    """
    Call Google AI Studio (Gemini) API.

    Expected environment variables:
      - GEMINI_API_KEY (get free key at https://aistudio.google.com/app/apikey)
      - GEMINI_MODEL (optional; default: gemini-1.5-flash)
    """
    api_key = settings.gemini_api_key
    model = settings.gemini_model or "gemini-1.5-flash"

    if not api_key:
        raise LLMError(
            "GEMINI_API_KEY must be set for gemini provider. Get a free key at https://aistudio.google.com/app/apikey"
        )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
    except requests.RequestException as exc:
        logger.error("LLM request to Gemini API failed: %s", exc)
        raise LLMError("LLM provider is unavailable") from exc

    if response.status_code != 200:
        try:
            err_json = response.json()
            msg = err_json.get("error", {}).get("message", response.text[:200])
        except Exception:
            msg = response.text[:200] if response.text else "No response body"
        logger.error(
            "Gemini API failed with status %s: %s",
            response.status_code,
            response.text[:800],
        )
        raise LLMError(f"Gemini API error ({response.status_code}): {msg}")

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Failed to decode Gemini JSON response: %s", exc)
        raise LLMError("LLM provider returned invalid JSON") from exc

    try:
        candidates = data.get("candidates", [])
        if not candidates:
            prompt_feedback = data.get("promptFeedback", {})
            raise LLMError(f"Gemini returned no candidates. {prompt_feedback.get('blockReason', 'Unknown')}")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise LLMError("Gemini returned empty content")
        content = parts[0].get("text", "")
    except LLMError:
        raise
    except Exception as exc:
        logger.error("Unexpected Gemini payload shape: %s", data)
        raise LLMError("LLM provider returned an unexpected payload") from exc

    if not isinstance(content, str):
        raise LLMError("LLM provider returned an unexpected payload")

    text = content.strip()
    logger.info("LLM call succeeded (chars=%d)", len(text))
    return text


def call_llm(prompt: str) -> str:
    """Entry point for all LLM calls, using configured provider."""
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return _call_ollama(prompt)

    if provider in {"openai", "openai_compatible", "groq"}:
        return _call_openai_compatible(prompt)

    if provider == "gemini":
        return _call_gemini(prompt)

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
    """Build schema text. When 'table' is present, group columns by table for clarity."""
    from collections import OrderedDict
    by_table: OrderedDict[str | None, list[dict]] = OrderedDict()
    for col in schema_cols:
        t = col.get("table") if isinstance(col, dict) else None
        if t not in by_table:
            by_table[t] = []
        by_table[t].append(col)

    lines = []
    for table_name, cols in by_table.items():
        if table_name:
            lines.append(f"\nTable: {table_name}")
        for col in cols:
            known_values = col.get("known_values")
            prefix = "  " if table_name else ""
            if known_values:
                values_text = ", ".join([repr(v) for v in known_values])
                lines.append(f"{prefix}- {col['name']} ({col['type']}), known_values: [{values_text}]")
            else:
                lines.append(f"{prefix}- {col['name']} ({col['type']})")
    return "\n".join(lines).strip()

    # - id (INTEGER)
    # - username (TEXT)
    # - age (INTEGER)
    # - status (TEXT), known_values: ['pending', 'approved', 'rejected']


def _build_multi_table_schema_text(tables: list) -> str:
    """Build schema text for multi-table contexts using TableInfo objects or dicts."""
    lines = []
    for table in tables:
        if hasattr(table, "qualified_name"):
            # TableInfo object
            table_name = table.qualified_name
            lines.append(f"\nTable: {table_name}")
            for col in table.columns:
                extras = []
                if col.is_pk:
                    extras.append("PK")
                if col.fk_reference:
                    extras.append(f"FK->{col.fk_reference}")
                if col.known_values:
                    vals = ", ".join(repr(v) for v in col.known_values)
                    extras.append(f"known_values: [{vals}]")
                extra_str = f" [{', '.join(extras)}]" if extras else ""
                lines.append(f"  - {col.name} ({col.data_type}){extra_str}")
        elif isinstance(table, dict) and "table_name" in table:
            # Dict format: {"table_name": "...", "columns": [...]}
            lines.append(f"\nTable: {table['table_name']}")
            for col in table.get("columns", []):
                lines.append(f"  - {col['name']} ({col['type']})")
    return "\n".join(lines)


DIALECT_HINTS = {
    "duckdb": "Use DuckDB SQL syntax.",
    "postgresql": "Use PostgreSQL syntax. Quote identifiers with double quotes. Use ILIKE for case-insensitive matching.",
    "mysql": "Use MySQL syntax. Quote identifiers with backticks. Use LIKE for case-insensitive matching (MySQL is case-insensitive by default).",
    "sqlite": "Use SQLite syntax. Quote identifiers with double quotes. SQLite has limited function support.",
}


def generate_sql(
    nl_query: str,
    schema_cols: list[dict[str, str]],
    dialect: str = "duckdb",
    tables: list | None = None,
) -> str:
    if tables:
        columns_text = _build_multi_table_schema_text(tables)
        table_hint = "Use the table names shown above."
    else:
        columns_text = _build_schema_text(schema_cols)
        schema_tables = list(dict.fromkeys(c.get("table") for c in schema_cols if isinstance(c, dict) and c.get("table")))
        if schema_tables:
            table_hint = (
                f"The table name is '{schema_tables[0]}'."
                if len(schema_tables) == 1
                else f"Use the table names: {', '.join(repr(t) for t in schema_tables)}."
            )
        else:
            table_hint = "Use the table names shown in the schema."
    dialect_hint = DIALECT_HINTS.get(dialect, DIALECT_HINTS["duckdb"])

    prompt = f"""
    You convert natural language into SQL queries.
    {dialect_hint}
    {table_hint}
    Available schema:
    {columns_text}

    Rules:
    {SQL_RULES}

    User request: {nl_query}
    """

    sql = clean_sql_output(call_llm(prompt))
    if has_unresolved_placeholders(sql):
        repair_prompt = f"""
        Rewrite the SQL below into executable {dialect} SQL.
        Keep intent the same, but remove placeholders and assumptions not present in the request.
        {table_hint}
        Available schema:
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
    dialect: str = "duckdb",
    tables: list | None = None,
) -> str:
    if tables:
        columns_text = _build_multi_table_schema_text(tables)
        table_hint = "Use the table names shown above."
    else:
        columns_text = _build_schema_text(schema_cols)
        schema_tables = list(dict.fromkeys(c.get("table") for c in schema_cols if isinstance(c, dict) and c.get("table")))
        if schema_tables:
            table_hint = (
                f"The table name is '{schema_tables[0]}'."
                if len(schema_tables) == 1
                else f"Use the table names: {', '.join(repr(t) for t in schema_tables)}."
            )
        else:
            table_hint = "Use the table names shown in the schema."

    dialect_hint = DIALECT_HINTS.get(dialect, DIALECT_HINTS["duckdb"])

    prompt = f"""
    Fix this {dialect} SQL so it executes correctly.
    {dialect_hint}
    {table_hint}
    Available schema:
    {columns_text}

    User request: {nl_query}
    Broken SQL: {bad_sql}
    Database error: {db_error}

    Fix strategy:
    - Read the error carefully and fix exactly what it complains about.
    - If a column is missing from GROUP BY, either add it to GROUP BY or wrap it in an aggregate (e.g. ANY_VALUE, MAX, SUM).
    - If a column doesn't exist, remove it from the query entirely.
    - Simplify the query: remove columns and clauses that are not needed to answer the user's question.
    - Do not just wrap things randomly in aggregate functions without understanding the error.

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


def explain_result(
    nl_query: str,
    sql: str,
    result_summary: str,
    chart_type: str | None = None,
) -> str:
    """Generate a plain-language explanation of what a query result or chart means."""
    chart_note = f"\nThe data is visualized as a {chart_type} chart." if chart_type else ""

    prompt = f"""You're a data analyst explaining results to a non-technical user.

User question: {nl_query}
SQL query used: {sql}
{chart_note}

Result summary:
{result_summary}

Provide a clear, plain-language explanation of what this data means.
Mention key findings, what the numbers represent, and any notable patterns.
Keep it concise (2-4 sentences).
"""
    return call_llm(prompt)
