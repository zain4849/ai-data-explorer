from typing import Any

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .auth.dependencies import get_current_user, get_optional_user
from .auth.routes import router as auth_router
from .middleware.audit import AuditLoggingMiddleware
from .charting.charting import generate_chart
from .config import settings
from .dataset_upload import load_dataframe_from_upload, normalize_column_names, normalize_dataframe_types
from .db import db_manager, sanitize_table_name
from .llm import LLMError, explain_result, generate_insights, generate_sql, repair_sql
from .logger_config import generate_request_id, logger
from .models.base import init_db
from .models.user import User
from .routes.connections import router as connections_router
from .routes.dashboards import router as dashboards_router
from .routes.export import router as export_router
from .routes.admin import router as admin_router
from .sql_validator import ensure_limit, fix_phantom_table_data, validate_sql

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json"}


class UploadResponse(BaseModel):
    preview: list[dict[str, Any]]
    row_count: int
    columns: list[str]
    dataset_id: str | None = None
    table_name: str | None = None


class QueryResponse(BaseModel):
    sql: str
    result: list[dict[str, Any]]
    insights: str
    chart_html: str
    explanation: str | None = None


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
    hint: str | None = None


# Pydantic will:
#   Take your inputs
#   Validate their types (List[dict[str, Any]], int, List[str])
#   Convert them if possible
#   Return an object with these values accessible as attributes.
#
# Pydantic will:
#   Take your inputs
#   Validate their types (List[dict[str, Any]], int, List[str])
#   Convert them if possible
#   Return an object with these values accessible as attributes.
#

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        logger.info(
            "%s %s",
            request.method,
            request.url.path,
            extra={"request_id": request_id},
        )
        try:
            response: Response = await call_next(request)
        except Exception:
            logger.exception("Unhandled error in request %s %s", request.method, request.url.path)
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="AI Data Explorer", version="0.1.0")
app.state.limiter = limiter
from .routes.datasets import router as datasets_router
from .routes.chat import router as chat_router
from fastapi import APIRouter


v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth_router)
v1_router.include_router(dashboards_router)
v1_router.include_router(connections_router)
v1_router.include_router(export_router)
v1_router.include_router(admin_router)
v1_router.include_router(datasets_router)
v1_router.include_router(chat_router)



_UNSAFE_SECRET_PLACEHOLDERS = frozenset({"dev-secret-change-in-production", "change-me-in-production-use-a-real-secret"})


@app.on_event("startup")
def _startup():
    # Production safety: refuse to start with default/placeholder SECRET_KEY
    if settings.environment == "production" and settings.secret_key in _UNSAFE_SECRET_PLACEHOLDERS:
        raise RuntimeError(
            "SECRET_KEY must be set to a secure random value in production. "
            "Generate one with: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    # Log LLM config (no secrets) so users can verify provider/key setup
    provider = settings.llm_provider.lower()
    has_key = False
    if provider == "gemini":
        has_key = bool(settings.gemini_api_key)
        logger.info("LLM: provider=gemini has_key=%s", has_key)
    elif provider in {"openai", "openai_compatible", "groq"}:
        has_key = bool(settings.openai_api_key)
        logger.info("LLM: provider=%s has_key=%s", provider, has_key)
    elif provider == "ollama":
        logger.info("LLM: provider=ollama url=%s model=%s", settings.ollama_url, settings.ollama_model)
    else:
        logger.warning("LLM: unknown provider=%s", provider)
    if provider == "gemini" and not has_key:
        logger.warning("GEMINI_API_KEY not set - queries will fail. Add it to backend/.env")
    try:
        init_db()
        _seed_default_roles()
        logger.info("App metadata database initialized")
    except Exception as exc:
        logger.warning("Could not initialize app DB (may need PostgreSQL): %s", exc)


def _seed_default_roles():
    """Create default roles if they don't exist."""
    import json as _json
    from sqlalchemy import select as _sel
    from sqlalchemy.orm import Session as _Ses
    from .models.role import Role
    from .models.base import get_engine

    roles = [
        ("admin", ["manage_users", "manage_connections", "execute_queries", "view_dashboards", "export_data", "view_audit_logs"]),
        ("analyst", ["manage_connections", "execute_queries", "view_dashboards", "export_data"]),
        ("viewer", ["view_dashboards"]),
    ]
    engine = get_engine()
    with _Ses(engine) as session:
        for name, perms in roles:
            existing = session.execute(_sel(Role).where(Role.name == name)).scalar_one_or_none()
            if not existing:
                session.add(Role(name=name, permissions=_json.dumps(perms)))
        session.commit()


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)


# Convert to object dtype first so None can replace NaN in numeric columns.
def dataframe_to_json_records(df: pd.DataFrame, limit: int = 5):
    """Convert DataFrame rows to JSON-safe list of dicts, replacing NaN with None."""
    safe_df = df.head(limit).astype(object).where(pd.notna(df.head(limit)), None)
    return safe_df.to_dict(orient="records")


# FastAPI has special helpers to say where a parameter comes from in the request.
# File(...) is a helper that says the parameter comes from the request body.
# Query(...) is a helper that says the parameter comes from the query string.
# Path(...) is a helper that says the parameter comes from the path.
# Header(...) is a helper that says the parameter comes from the header.
# Cookie(...) is a helper that says the parameter comes from the cookie.
# Body(...) is a helper that says the parameter comes from the body.
# Form(...) is a helper that says the parameter comes from the form.
# FastAPI has special helpers to say where a parameter comes from in the request.
# File(...) is a helper that says the parameter comes from the request body.
# Query(...) is a helper that says the parameter comes from the query string.
# Path(...) is a helper that says the parameter comes from the path.
# Header(...) is a helper that says the parameter comes from the header.
# Cookie(...) is a helper that says the parameter comes from the cookie.
# Body(...) is a helper that says the parameter comes from the body.
# Form(...) is a helper that says the parameter comes from the form.

# multipart/form-data is an HTTP request format used when a request needs to send multiple pieces of data (fields), especially files.
# Each piece of data is called a field.
# Think of it like a form submission split into parts.
# Simple Idea

# A multipart request looks like:

# request body
#  ├── field 1
#  ├── field 2
#  ├── field 3
#  └── file

# Each field has:
# a name
# a value
# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=dict)
def health() -> dict[str, Any]:
    """Basic health check endpoint."""
    try:
        db_manager.get_connection(None).execute("SELECT 1")
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


@v1_router.post("/datasets", response_model=UploadResponse)
@limiter.limit("5/minute")  # 5 requests per minute per client
def upload_csv(request: Request, file: UploadFile = File(...), user: User | None = Depends(get_optional_user)):
    import json as _json
    from pathlib import Path as _Path

    # --- Validate file extension --- Someone could rename malware.exe to file.csv — the extension check alone cannot guarantee the file is actually a CSV.
    filename = file.filename or ""
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Only CSV, XLSX, and JSON files are allowed.",
        )

    # --- Validate content type --- This checks the MIME type sent by the browser or client (like text/csv).
    content_type = (file.content_type or "").lower()
    if content_type not in {
        "text/csv",
        "application/vnd.ms-excel",
        "application/json",
        "application/octet-stream",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a CSV, XLSX, or JSON file.",
        )

    # --- Read and validate file size ---
    contents = file.file.read()  # Returns the raw bytes of the file.
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    logger.info("Received CSV upload: filename=%s, size=%d bytes", filename, len(contents))

    # Next to each function i list the reasons why we needed them in a try except block
    try:
        # df = pd.read_csv(io.BytesIO(contents))
        df = load_dataframe_from_upload(file) # Bad CSV (malformed), bad JSON, bad Excel, encoding issues, empty file, unsupported structure
        # Normalize the dataframe types and columns w/ spaces in b/w
        df = normalize_column_names(df) # Edge cases with column names (e.g. all-numeric index)
        df = normalize_dataframe_types(df) # Type inference/casting issues on unusual data
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(
            status_code=400,
            detail="Could not read uploaded file.",
        ) from exc

    user_id = user.id if user else None
    table_name = sanitize_table_name(filename)
    file_ext = _Path(filename).suffix.lower().lstrip(".")

    # Persist the raw file to disk so the dataset survives backend restarts
    dataset_id = None
    if user_id:
        upload_dir = db_manager.uploads_dir_for(user_id)
        from uuid import uuid4
        dataset_id = str(uuid4())
        saved_path = upload_dir / f"{dataset_id}_{filename}"
        saved_path.write_bytes(contents)

        # Record in PostgreSQL
        try:
            from .models.base import get_engine
            from .models.dataset import Dataset
            from sqlalchemy.orm import Session as _Ses

            with _Ses(get_engine()) as session:
                ds = Dataset(
                    id=dataset_id,
                    user_id=user_id,
                    name=filename,
                    table_name=table_name,
                    file_path=str(saved_path),
                    file_type=file_ext,
                    row_count=len(df),
                    columns_json=_json.dumps([str(c) for c in df.columns]),
                )
                session.add(ds)
                session.commit()
        except Exception as exc:
            logger.warning("Could not persist dataset metadata: %s", exc)

    # Load into the user's file-based DuckDB (or anonymous in-memory)
    db_manager.load_dataframe(user_id, table_name, df)
    logger.info("Loaded dataframe into DuckDB table '%s': %s", table_name, df.head())

    preview_records = dataframe_to_json_records(df)

    return UploadResponse(
        preview=preview_records,
        row_count=len(df),
        columns=[str(col) for col in df.columns],
        dataset_id=dataset_id,
        table_name=table_name,
    )


MAX_QUERY_LENGTH = 2000


def _resolve_connector_and_schema(connection_id: str | None, user: User | None):
    """Resolve a connector + schema for the given connection_id or fall back to DuckDB file data."""
    user_id = user.id if user else None

    if not connection_id:
        schema = db_manager.get_schema(user_id)
        return None, schema, "duckdb", None

    from .connectors import get_connector
    from .connectors.types import ConnectionConfig
    from .crypto import decrypt
    from .models.connection import DataConnection
    from .models.base import get_session as _gs
    import json

    session = next(_gs())
    try:
        conn_record = session.get(DataConnection, connection_id)
        if conn_record is None:
            raise HTTPException(status_code=404, detail="Connection not found")
        if user and conn_record.user_id != user.id:
            raise HTTPException(status_code=404, detail="Connection not found")

        config = ConnectionConfig(**json.loads(decrypt(conn_record.config_encrypted)))
        connector = get_connector(conn_record.db_type, config)
        dialect = connector.get_dialect()

        # Build schema from connector tables
        from .catalog.cache import get_cached_schema
        tables = get_cached_schema(session, connection_id, connector)
        schema_dicts = []
        for t in tables:
            for c in t.columns:
                schema_dicts.append(c.to_dict())

        return connector, schema_dicts, dialect, tables
    finally:
        session.close()


@v1_router.get("/queries", response_model=QueryResponse, responses={400: {"model": ErrorResponse}})
@limiter.limit("10/minute")
def query_data(
    request: Request,
    nl_query: str = Query(..., max_length=MAX_QUERY_LENGTH),
    connection_id: str | None = Query(default=None),
    user: User | None = Depends(get_optional_user), # From the Authorization header
):
    user_id = user.id if user else None
    
    connector, schema, dialect, tables = _resolve_connector_and_schema(connection_id, user)
    real_tables = list(dict.fromkeys(c.get("table") for c in schema if isinstance(c, dict) and c.get("table")))
    if not real_tables and not connector:
        real_tables = db_manager.get_tables(user_id)
    # Skip LLM call when there's no data source (avoids confusing LLM errors)
    if not connector and not real_tables:
        raise HTTPException(
            status_code=400,
            detail="No dataset available. Upload a file first or connect to a database.",
        )
    
    sql = ""

    try:
        sql = generate_sql(nl_query, schema, dialect=dialect, tables=tables)
        logger.info("Generated SQL (%s): %s", dialect, sql)
        validate_sql(sql)
        sql = fix_phantom_table_data(sql, real_tables)
        sql = ensure_limit(sql)
        if connector:
            df = connector.execute_query(sql)
        else:
            df = db_manager.query(user_id, sql)
    except LLMError as llm_error:
        logger.error("LLM error during SQL generation: %s", llm_error)
        # In development, surface the actual error to help debug (e.g. missing GEMINI_API_KEY)
        detail = str(llm_error) if settings.environment != "production" else "The AI query engine is currently unavailable. Please try again."
        raise HTTPException(status_code=503, detail=detail) from llm_error
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
            # A second attempt to generate a valid SQL query.
            repaired_sql = repair_sql(nl_query, schema, sql, first_error_text, dialect=dialect, tables=tables)
            logger.info("Repaired SQL: %s", repaired_sql)
            validate_sql(repaired_sql)
            repaired_sql = fix_phantom_table_data(repaired_sql, real_tables)
            repaired_sql = ensure_limit(repaired_sql)
            if connector:
                df = connector.execute_query(repaired_sql)
            else:
                df = db_manager.query(user_id, repaired_sql)
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
    finally:
        if connector:
            connector.close()

    insights = generate_insights(df.head(10).to_string())
    chart_html = generate_chart(df)

    explanation = None
    try:
        explanation = explain_result(
            nl_query, sql, df.head(10).to_string(),
            chart_type=None,
        )
    except Exception as exc:
        logger.warning("Failed to generate explanation: %s", exc)

    return QueryResponse(
        sql=sql,
        result=dataframe_to_json_records(df, 50),
        insights=insights,
        chart_html=chart_html,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Direct SQL execution (for edited queries)
# ---------------------------------------------------------------------------

class ExecuteSQLRequest(BaseModel):
    sql: str
    connection_id: str | None = None


@v1_router.post("/query/execute", response_model=QueryResponse, responses={400: {"model": ErrorResponse}})
@limiter.limit("10/minute")
def execute_sql(
    request: Request,
    body: ExecuteSQLRequest,
    user: User | None = Depends(get_optional_user),
):
    """Execute raw SQL directly (for user-edited queries)."""
    validate_sql(body.sql)
    sql = ensure_limit(body.sql)
    user_id = user.id if user else None

    connector = None
    try:
        if body.connection_id:
            connector_inst, _, _, _ = _resolve_connector_and_schema(body.connection_id, user)
            connector = connector_inst
            df = connector.execute_query(sql)
        else:
            df = db_manager.query(user_id, sql)
    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "code": "sql_execution_failed"},
        )
    finally:
        if connector:
            connector.close()

    insights = generate_insights(df.head(10).to_string())
    chart_html = generate_chart(df)

    return QueryResponse(
        sql=sql,
        result=dataframe_to_json_records(df, 50),
        insights=insights,
        chart_html=chart_html,
    )


# ---------------------------------------------------------------------------
# Sandboxed Python execution
# ---------------------------------------------------------------------------

class PythonExecuteRequest(BaseModel):
    code: str
    connection_id: str | None = None


@v1_router.post("/execute/python")
@limiter.limit("5/minute")
def execute_python(
    request: Request,
    body: PythonExecuteRequest,
    user: User | None = Depends(get_optional_user),
):
    """Execute sandboxed Python code against the current dataset."""
    from .analytics.sandbox import execute_python_sandboxed

    user_id = user.id if user else None
    dataframe = None
    if body.connection_id:
        connector, _, _, _ = _resolve_connector_and_schema(body.connection_id, user)
        try:
            tables = connector.get_tables()
            if tables:
                dataframe = connector.sample_table(tables[0].name, limit=1000)
        finally:
            connector.close()
    else:
        try:
            user_tables = db_manager.get_tables(user_id)
            if user_tables:
                dataframe = db_manager.query(user_id, f'SELECT * FROM "{user_tables[0]}" LIMIT 1000')
        except Exception:
            pass

    result = execute_python_sandboxed(body.code, dataframe=dataframe)
    return result

app.include_router(v1_router)
