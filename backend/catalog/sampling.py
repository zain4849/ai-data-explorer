"""Data sampling and DuckDB-based caching for remote data sources.

Pulls sample data from remote connectors into a local DuckDB instance
with namespaced table names (conn_{id}_{table}) and TTL-based invalidation.
"""

import time
from datetime import timedelta

import duckdb
import pandas as pd

from ..connectors.base import DataConnector
from ..logger_config import logger

DEFAULT_SAMPLE_SIZE = 1000
DEFAULT_TTL = timedelta(minutes=15)

# Global DuckDB instance for sample caching
_cache_conn = duckdb.connect(database=":memory:")
_cache_meta: dict[str, float] = {}  # cache_key -> timestamp


def _cache_key(connection_id: str, table: str) -> str:
    safe_table = table.replace(".", "_").replace('"', "").replace("'", "")
    return f"conn_{connection_id}_{safe_table}"


def is_cached(connection_id: str, table: str, ttl: timedelta = DEFAULT_TTL) -> bool:
    key = _cache_key(connection_id, table)
    ts = _cache_meta.get(key)
    if ts is None:
        return False
    return (time.time() - ts) < ttl.total_seconds()


def cache_sample(
    connector: DataConnector,
    connection_id: str,
    table: str,
    limit: int = DEFAULT_SAMPLE_SIZE,
    ttl: timedelta = DEFAULT_TTL,
    force: bool = False,
) -> pd.DataFrame:
    """Pull a sample from a remote table into the local DuckDB cache.

    Returns the cached DataFrame.
    """
    key = _cache_key(connection_id, table)

    if not force and is_cached(connection_id, table, ttl):
        logger.info("Cache hit for %s", key)
        return _cache_conn.execute(f'SELECT * FROM "{key}"').fetchdf()

    logger.info("Cache miss for %s, fetching sample from remote", key)
    df = connector.sample_table(table, limit=limit)

    _cache_conn.execute(f'CREATE OR REPLACE TABLE "{key}" AS SELECT * FROM df')
    _cache_meta[key] = time.time()

    logger.info("Cached %d rows for %s", len(df), key)
    return df


def get_cached_sample(connection_id: str, table: str) -> pd.DataFrame | None:
    """Get a cached sample without hitting the remote source. Returns None if not cached."""
    key = _cache_key(connection_id, table)
    if key not in _cache_meta:
        return None
    try:
        return _cache_conn.execute(f'SELECT * FROM "{key}"').fetchdf()
    except Exception:
        return None


def invalidate_cache(connection_id: str, table: str | None = None):
    """Invalidate cached samples for a connection (optionally a specific table)."""
    if table:
        key = _cache_key(connection_id, table)
        _cache_meta.pop(key, None)
        try:
            _cache_conn.execute(f'DROP TABLE IF EXISTS "{key}"')
        except Exception:
            pass
    else:
        # Invalidate all tables for a connection
        prefix = f"conn_{connection_id}_"
        keys_to_remove = [k for k in _cache_meta if k.startswith(prefix)]
        for key in keys_to_remove:
            _cache_meta.pop(key, None)
            try:
                _cache_conn.execute(f'DROP TABLE IF EXISTS "{key}"')
            except Exception:
                pass


def get_cache_stats() -> dict:
    """Return cache statistics."""
    return {
        "cached_tables": len(_cache_meta),
        "entries": {
            key: {
                "age_seconds": time.time() - ts,
            }
            for key, ts in _cache_meta.items()
        },
    }
