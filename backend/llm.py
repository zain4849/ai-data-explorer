import re
from typing import Tuple

import requests

from .config import settings
from .logger_config import logger


class LLMError(Exception): # LLMError is a subclass of Exception, so it behaves like an exception. No extra code needed.
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
            "GEMINI_API_KEY must be set for gemini provider. "
            "Get a free key at https://aistudio.google.com/app/apikey"
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
        logger.error(
            "Gemini API failed with status %s: %s",
            response.status_code,
            response.text[:800],
        )
        raise LLMError("LLM provider returned an error response")

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Failed to decode Gemini JSON response: %s", exc)
        raise LLMError("LLM provider returned invalid JSON") from exc

    try:
        candidates = data.get("candidates", [])
        if not candidates:
            prompt_feedback = data.get("promptFeedback", {})
            raise LLMError(
                f"Gemini returned no candidates. {prompt_feedback.get('blockReason', 'Unknown')}"
            )
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

    Fix strategy:
    - Read the DuckDB error carefully and fix exactly what it complains about.
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
    
