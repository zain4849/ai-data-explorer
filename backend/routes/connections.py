"""Connection management CRUD API."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..analytics.statistics import compute_descriptive_stats
from ..auth.dependencies import get_current_user
from ..connectors import get_connector
from ..connectors.types import ConnectionConfig, ConnectorType
from ..crypto import decrypt, encrypt
from ..logger_config import logger
from ..models.base import get_session
from ..models.connection import DataConnection
from ..models.user import User

router = APIRouter(prefix="/connections", tags=["connections"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ConnectionCreateRequest(BaseModel):
    name: str
    db_type: str  # postgresql, mysql, sqlite
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    file_path: str | None = None
    ssl: bool = False
    allow_ai_access: bool = True
    max_rows_to_ai: int = 100
    mask_columns: str | None = None


class ConnectionResponse(BaseModel):
    id: str
    name: str
    db_type: str
    allow_ai_access: bool
    max_rows_to_ai: int
    mask_columns: str | None
    created_at: str


class ConnectionTestResponse(BaseModel):
    ok: bool
    error: str | None = None


class TableResponse(BaseModel):
    name: str
    schema_name: str | None = None
    row_count: int | None = None


class ColumnResponse(BaseModel):
    name: str
    type: str
    nullable: bool = True
    is_pk: bool = False
    fk_reference: str | None = None
    known_values: list[str] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _encrypt_config(req: ConnectionCreateRequest) -> str:
    config_dict = {
        "host": req.host or "localhost",
        "port": req.port or (5432 if req.db_type == "postgresql" else 3306),
        "database": req.database or "",
        "username": req.username or "",
        "password": req.password or "",
        "file_path": req.file_path,
        "ssl": req.ssl,
    }
    return encrypt(json.dumps(config_dict))


def _decrypt_config(encrypted: str) -> ConnectionConfig:
    raw = json.loads(decrypt(encrypted))
    return ConnectionConfig(**raw)


def _get_user_connection(session: Session, conn_id: str, user: User) -> DataConnection:
    conn = session.get(DataConnection, conn_id)
    if conn is None or conn.user_id != user.id:
        raise HTTPException(status_code=404, detail="Connection not found")
    return conn


def _to_response(conn: DataConnection) -> ConnectionResponse:
    return ConnectionResponse(
        id=conn.id,
        name=conn.name,
        db_type=conn.db_type,
        allow_ai_access=conn.allow_ai_access,
        max_rows_to_ai=conn.max_rows_to_ai,
        mask_columns=conn.mask_columns,
        created_at=conn.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_connection(
    body: ConnectionCreateRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        ConnectorType(body.db_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported db_type: {body.db_type}")

    # Test connectivity before saving
    config = ConnectionConfig(
        host=body.host or "localhost",
        port=body.port or (5432 if body.db_type == "postgresql" else 3306),
        database=body.database or "",
        username=body.username or "",
        password=body.password or "",
        file_path=body.file_path,
        ssl=body.ssl,
    )
    connector = get_connector(body.db_type, config)
    try:
        connector.test_connection()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {exc}")
    finally:
        connector.close()

    db_conn = DataConnection(
        user_id=user.id,
        name=body.name,
        db_type=body.db_type.lower(),
        config_encrypted=_encrypt_config(body),
        allow_ai_access=body.allow_ai_access,
        max_rows_to_ai=body.max_rows_to_ai,
        mask_columns=body.mask_columns,
    )
    session.add(db_conn)
    session.commit()
    session.refresh(db_conn)
    return _to_response(db_conn)


@router.get("", response_model=list[ConnectionResponse])
def list_connections(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    conns = session.execute(
        select(DataConnection).where(DataConnection.user_id == user.id).order_by(DataConnection.created_at.desc())
    ).scalars().all()
    return [_to_response(c) for c in conns]


@router.get("/{conn_id}", response_model=ConnectionResponse)
def get_connection(
    conn_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return _to_response(_get_user_connection(session, conn_id, user))


@router.put("/{conn_id}", response_model=ConnectionResponse)
def update_connection(
    conn_id: str,
    body: ConnectionCreateRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    conn = _get_user_connection(session, conn_id, user)
    conn.name = body.name
    conn.db_type = body.db_type.lower()
    conn.config_encrypted = _encrypt_config(body)
    conn.allow_ai_access = body.allow_ai_access
    conn.max_rows_to_ai = body.max_rows_to_ai
    conn.mask_columns = body.mask_columns
    session.commit()
    session.refresh(conn)
    return _to_response(conn)


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    conn_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    conn = _get_user_connection(session, conn_id, user)
    session.delete(conn)
    session.commit()


@router.post("/{conn_id}/test", response_model=ConnectionTestResponse)
def test_connection(
    conn_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_conn = _get_user_connection(session, conn_id, user)
    config = _decrypt_config(db_conn.config_encrypted)
    connector = get_connector(db_conn.db_type, config)
    try:
        connector.test_connection()
        return ConnectionTestResponse(ok=True)
    except Exception as exc:
        logger.warning("Connection test failed for %s: %s", conn_id, exc)
        return ConnectionTestResponse(ok=False, error=str(exc))
    finally:
        connector.close()


@router.get("/{conn_id}/tables", response_model=list[TableResponse])
def list_tables(
    conn_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_conn = _get_user_connection(session, conn_id, user)
    config = _decrypt_config(db_conn.config_encrypted)
    connector = get_connector(db_conn.db_type, config)
    try:
        tables = connector.get_tables()
        return [
            TableResponse(name=t.name, schema_name=t.schema, row_count=t.row_count)
            for t in tables
        ]
    finally:
        connector.close()


@router.get("/{conn_id}/tables/{table}/schema", response_model=list[ColumnResponse])
def get_table_schema(
    conn_id: str,
    table: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_conn = _get_user_connection(session, conn_id, user)
    config = _decrypt_config(db_conn.config_encrypted)
    connector = get_connector(db_conn.db_type, config)
    try:
        cols = connector.get_table_schema(table)
        return [
            ColumnResponse(
                name=c.name, type=c.data_type, nullable=c.nullable,
                is_pk=c.is_pk, fk_reference=c.fk_reference, known_values=c.known_values,
            )
            for c in cols
        ]
    finally:
        connector.close()


@router.get("/{conn_id}/tables/{table}/sample")
def sample_table_data(
    conn_id: str,
    table: str,
    limit: int = 100,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_conn = _get_user_connection(session, conn_id, user)
    config = _decrypt_config(db_conn.config_encrypted)
    connector = get_connector(db_conn.db_type, config)
    try:
        df = connector.sample_table(table, limit=min(limit, 1000))
        safe_df = df.astype(object).where(df.notna(), None)
        return safe_df.to_dict(orient="records")
    finally:
        connector.close()


@router.get("/{conn_id}/tables/{table}/stats")
def table_stats(
    conn_id: str,
    table: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Compute descriptive statistics for a table."""
    db_conn = _get_user_connection(session, conn_id, user)
    config = _decrypt_config(db_conn.config_encrypted)
    connector = get_connector(db_conn.db_type, config)
    try:
        df = connector.sample_table(table, limit=5000)
        stats = compute_descriptive_stats(df)
        return stats.to_dict()
    finally:
        connector.close()
