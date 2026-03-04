import requests
import re

OLLAMA_URL = "http://localhost:11434/api/generate" # requres POST request
MODEL_NAME = "phi3"


def call_ollama(nl_query: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": nl_query,
            "stream": False # We want the full response at once, not a stream of tokens aka bit by bit
        }
    )

    return response.json()["response"].strip()


def clean_sql_output(raw_sql: str) -> str:
    sql = raw_sql.strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)
    return sql.strip()

def generate_sql(nl_query: str, schema_cols: list[str]) -> str:
    columns_text = ", ".join(schema_cols)

    prompt = f"""
    You convert natural language into DuckDB SQL queries.
    The table name is 'data'.
    Available columns: {columns_text}

    Rules:
    - Only output valid SQL.
    - Return only raw SQL as plain text.
    - Don't explain.
    - Don't use markdown.
    - Don't use markdown fences.
    - Don't include explanations or any text before/after SQL.
    - Don't use backticks.

    User request: {nl_query}
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
    
