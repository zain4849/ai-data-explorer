"""Schema cache: store and retrieve discovered schemas using the app database."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..connectors.base import DataConnector
from ..connectors.types import ColumnInfo, TableInfo
from ..logger_config import logger
from ..models.schema_cache import SchemaCache
from .descriptions import generate_descriptions
from .discovery import discover_schema

CACHE_TTL = timedelta(hours=1)


def get_cached_schema(
    session: Session,
    connection_id: str,
    connector: DataConnector | None = None,
    force_refresh: bool = False,
) -> list[TableInfo]:
    """Get schema from cache or discover + cache if stale/missing."""
    if not force_refresh:
        cached = _load_from_cache(session, connection_id)
        if cached is not None:
            return cached

    if connector is None:
        return []

    return refresh_schema_cache(session, connection_id, connector)


def refresh_schema_cache(
    session: Session,
    connection_id: str,
    connector: DataConnector,
) -> list[TableInfo]:
    """Discover schema, generate descriptions, and store in cache."""
    tables = discover_schema(connector)

    # Generate AI descriptions
    descriptions = {}
    try:
        descriptions = generate_descriptions(tables)
    except Exception as exc:
        logger.warning("Failed to generate descriptions for connection %s: %s", connection_id, exc)

    # Clear old cache
    session.execute(delete(SchemaCache).where(SchemaCache.connection_id == connection_id))

    # Insert new cache entries
    for table in tables:
        table_descs = descriptions.get(table.name, descriptions.get(table.qualified_name, {}))
        for col in table.columns:
            entry = SchemaCache(
                connection_id=connection_id,
                table_name=table.qualified_name,
                column_name=col.name,
                column_type=col.data_type,
                nullable=col.nullable,
                is_pk=col.is_pk,
                fk_reference=col.fk_reference,
                ai_description=table_descs.get(col.name),
            )
            session.add(entry)

    session.commit()
    logger.info("Refreshed schema cache for connection %s: %d tables", connection_id, len(tables))
    return tables


def _load_from_cache(session: Session, connection_id: str) -> list[TableInfo] | None:
    """Load schema from the DB cache if entries exist and are not stale."""
    entries = session.execute(
        select(SchemaCache)
        .where(SchemaCache.connection_id == connection_id)
        .order_by(SchemaCache.table_name, SchemaCache.column_name)
    ).scalars().all()

    if not entries:
        return None

    cutoff = datetime.now(timezone.utc) - CACHE_TTL
    if entries[0].discovered_at.replace(tzinfo=timezone.utc) < cutoff:
        return None

    tables_map: dict[str, TableInfo] = {}
    for e in entries:
        if e.table_name not in tables_map:
            tables_map[e.table_name] = TableInfo(name=e.table_name)
        tables_map[e.table_name].columns.append(
            ColumnInfo(
                name=e.column_name,
                data_type=e.column_type,
                nullable=e.nullable,
                is_pk=e.is_pk,
                fk_reference=e.fk_reference,
            )
        )

    return list(tables_map.values())
