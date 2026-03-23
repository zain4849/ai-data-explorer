"""Per-user file-based DuckDB manager.

Each authenticated user gets their own DuckDB file under .app_state/duckdb/.
Uploaded datasets persist as named tables across sessions.
An anonymous fallback (in-memory) is kept for unauthenticated / health-check use.
"""

import re
import threading
from pathlib import Path

import duckdb
import pandas as pd

from .connectors.file_connector import FileConnector

APP_STATE_DIR = Path(".app_state") # Path(".app_state") creates a Path object pointing to a directory called .app_state in the current working directory. The "." means it's a hidden folder on Unix-like systems (Linux/macOS)
DUCKDB_DIR = APP_STATE_DIR / "duckdb"
UPLOADS_DIR = APP_STATE_DIR / "uploads" # UPLOADS_DIR points to .app_state/uploads

# Ensure directories exist at import time
DUCKDB_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

_SAFE_NAME_RE = re.compile(r"[^a-z0-9_]")


def sanitize_table_name(filename: str) -> str: # similar to normalize_column_names in dataset_upload.py
    """Derive a safe DuckDB table name from an uploaded filename."""
    stem = Path(filename).stem.lower().strip()
    name = _SAFE_NAME_RE.sub("_", stem)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name or name[0].isdigit():
        name = f"t_{name}"
    return name[:63]


class UserDatabaseManager:
    """Thread-safe registry of per-user DuckDB connections (file-backed)."""

    def __init__(self):
        self._connections: dict[str, duckdb.DuckDBPyConnection] = {} # [user_id, duckdb.DuckDBPyConnection objects]      
        self._lock = threading.Lock()
        # Anonymous in-memory fallback for health checks / unauthenticated access
        self._anon = duckdb.connect(database=":memory:")

    def _db_path(self, user_id: str) -> Path:
        return DUCKDB_DIR / f"{user_id}.duckdb"

    def get_connection(self, user_id: str | None) -> duckdb.DuckDBPyConnection:
        if not user_id:
            return self._anon
        with self._lock: # Acquire a lock b4 below code
            if user_id not in self._connections:
                self._connections[user_id] = duckdb.connect(
                    str(self._db_path(user_id))
                )
            return self._connections[user_id]

    def get_connector(self, user_id: str | None) -> FileConnector:
        return FileConnector(self.get_connection(user_id))

    def load_dataframe(
        self, user_id: str, table_name: str, df: pd.DataFrame
    ) -> None:
        conn = self.get_connection(user_id)
        safe = f'"{table_name}"'
        conn.execute(f"CREATE OR REPLACE TABLE {safe} AS SELECT * FROM df")

    def query(self, user_id: str | None, sql: str) -> pd.DataFrame:
        conn = self.get_connection(user_id)
        return conn.execute(sql.strip().rstrip(";").strip()).fetchdf()

    def get_tables(self, user_id: str | None) -> list[str]:
        conn = self.get_connection(user_id)
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main'"
        ).fetchall()
        return [r[0] for r in rows]

    def get_schema(self, user_id: str | None) -> list[dict]:
        """Return a flat list of column dicts across all of a user's tables."""
        connector = self.get_connector(user_id)
        tables = connector.get_tables()
        all_columns: list[dict] = []
        for t in tables:
            for col in connector.get_table_schema(t.name):
                d = col.to_dict()
                d["table"] = t.name
                all_columns.append(d)
        return all_columns

    def get_full_schema(self, user_id: str | None) -> list[dict]:
        """Return per-table schema groups for display / LLM context."""
        connector = self.get_connector(user_id)
        tables = connector.get_tables()
        result = []
        for t in tables:
            cols = connector.get_table_schema(t.name)
            result.append({
                "table": t.name,
                "row_count": t.row_count,
                "columns": [c.to_dict() for c in cols],
            })
        return result

    def close_user(self, user_id: str) -> None:
        with self._lock:
            conn = self._connections.pop(user_id, None)
            if conn:
                conn.close()

    def uploads_dir_for(self, user_id: str) -> Path:
        d = UPLOADS_DIR / user_id # d points to .app_state/uploads/123
        # No directories are created on disk so far (well UPLOADS dir is created above in db.py); these are just Path objects
        d.mkdir(parents=True, exist_ok=True)
        return d


db_manager = UserDatabaseManager()


class Database:
    """Legacy compatibility wrapper for tests. Uses in-memory DuckDB with table 'data'."""
    def __init__(self):
        self._conn = duckdb.connect(database=":memory:")

    def load_dataframe(self, df: pd.DataFrame, table_name: str = "data") -> None:
        self._conn.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM df')

    def query(self, sql: str) -> pd.DataFrame:
        return self._conn.execute(sql.strip().rstrip(";").strip()).fetchdf()

    def get_schema(self) -> list[dict]:
        connector = FileConnector(self._conn)
        tables = connector.get_tables()
        all_columns: list[dict] = []
        for t in tables:
            for col in connector.get_table_schema(t.name):
                d = col.to_dict()
                d["table"] = t.name
                all_columns.append(d)
        return all_columns
