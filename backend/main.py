from typing import Any, List

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from .db import db  # When Python imports a module (here db.py), it runs the top-level code (db = Database()) of that module once.
from .sql_validator import validate_sql
from .logger_config import logger
from .llm import LLMError, generate_sql, generate_insights, repair_sql
from .charting.charting import generate_chart
from .config import settings

import pandas as pd


class UploadResponse(BaseModel):
    preview: List[dict[str, Any]]
    row_count: int
    columns: List[str]


class QueryResultRow(BaseModel):
    __root__: dict[str, Any]


class QueryResponse(BaseModel):
    sql: str
    result: List[dict[str, Any]]
    insights: str
    chart_html: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
    hint: str | None = None


app = FastAPI(title="AI Data Explorer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Convert to object dtype first so None can replace NaN in numeric columns.
def dataframe_to_json_records(df: pd.DataFrame, limit: int = 5):
    safe_df = df.head(limit).astype(object).where(pd.notna(df.head(limit)), None)
    return safe_df.to_dict(orient="records")


@app.get("/health", response_model=dict)
def health() -> dict[str, Any]:
    """Basic health check endpoint."""
    try:
        # Touch the DB to ensure the connection object exists.
        db.get_schema()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Health check failed for DB: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Database is not ready",
        ) from exc

    return {
        "status": "ok",
        "environment": settings.environment,
    }


@app.post("/upload_csv", response_model=UploadResponse)
def upload_csv(file: UploadFile = File(...)):
    logger.info("Received CSV upload: filename=%s", file.filename)
    try:
        df = pd.read_csv(file.file)
    except Exception as exc:
        logger.error("Failed to read uploaded CSV: %s", exc)
        raise HTTPException(
            status_code=400,
            detail="Could not read CSV file. Please verify the file format.",
        ) from exc

    # After this DuckDB has a table named data with contents of df
    db.load_dataframe(df)

    preview_records = dataframe_to_json_records(df)
    response = UploadResponse( # Creates an instance of the UploadResponse class
        preview=preview_records,
        row_count=len(df),
        columns=[str(col) for col in df.columns],
    )
    return response


@app.get("/query", response_model=QueryResponse, responses={400: {"model": ErrorResponse}})
def query_data(nl_query: str = Query(...)):
    # http://localhost:8000/query?nl_query=top%2010%20customers

    schema = db.get_schema()
    sql = ""

    try:
        sql = generate_sql(nl_query, schema)
        logger.info("Generated SQL: %s", sql)
        validate_sql(sql)
        df = db.query(sql)  # df contains the results of the SQL query as a pandas DataFrame
    except LLMError as llm_error:
        logger.error("LLM error during SQL generation: %s", llm_error)
        raise HTTPException(
            status_code=503,
            detail="The AI query engine is currently unavailable. Please try again.",
        ) from llm_error
    except Exception as first_error:
        first_error_text = str(first_error)
        logger.warning("Initial SQL failed: %s", first_error_text)

        if not sql:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": first_error_text,
                    "code": "query_failed",
                },
            )

        try:
            repaired_sql = repair_sql(nl_query, schema, sql, first_error_text)
            logger.info("Repaired SQL: %s", repaired_sql)
            validate_sql(repaired_sql)
            df = db.query(repaired_sql)
            sql = repaired_sql
        except Exception as second_error:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": str(second_error),
                    "code": "query_failed_after_repair",
                    "hint": "Try simplifying your request or narrowing the scope.",
                },
            )

    insights = generate_insights(df.head(10).to_string())  # Generate insights based on a preview of the data
    chart_html = generate_chart(df)

    return QueryResponse(
        sql=sql,
        result=dataframe_to_json_records(df, 50),
        insights=insights,
        chart_html=chart_html,
    )
