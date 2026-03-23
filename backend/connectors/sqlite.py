"""SQLite connector using stdlib sqlite3."""

import sqlite3

import pandas as pd

from .base import DataConnector
from .types import ColumnInfo, ConnectionConfig, TableInfo


class SQLiteConnector(DataConnector):
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._conn = None

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            path = self.config.file_path or self.config.database
            if not path:
                raise ValueError("SQLite requires a file_path or database path")
            self._conn = sqlite3.connect(path, timeout=10)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def test_connection(self) -> bool:
        conn = self._get_connection()
        conn.execute("SELECT 1")
        return True

    def get_tables(self) -> list[TableInfo]:
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables: list[TableInfo] = []
        for (name,) in cur.fetchall():
            count_row = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()
            tables.append(TableInfo(name=name, row_count=count_row[0] if count_row else None))
        return tables

    def get_table_schema(self, table: str) -> list[ColumnInfo]:
        conn = self._get_connection()
        columns: list[ColumnInfo] = []

        cur = conn.execute(f'PRAGMA table_info("{table}")')
        for row in cur.fetchall():
            # cid, name, type, notnull, dflt_value, pk
            columns.append(ColumnInfo(
                name=row[1],
                data_type=row[2] or "TEXT",
                nullable=not row[3],
                is_pk=bool(row[5]),
            ))

        # Foreign keys
        fk_cur = conn.execute(f'PRAGMA foreign_key_list("{table}")')
        for fk in fk_cur.fetchall():
            # id, seq, table, from, to, on_update, on_delete, match
            ref_table = fk[2]
            from_col = fk[3]
            to_col = fk[4]
            for col in columns:
                if col.name == from_col:
                    col.fk_reference = f"{ref_table}.{to_col}"

        for col in columns:
            dtype = (col.data_type or "").upper()
            if any(t in dtype for t in ("TEXT", "CHAR", "VARCHAR", "CLOB")):
                self._populate_known_values(conn, table, col)

        return columns

    def _populate_known_values(self, conn: sqlite3.Connection, table: str, col: ColumnInfo):
        ident = f'"{col.name}"'
        row = conn.execute(
            f'SELECT COUNT(DISTINCT {ident}) FROM "{table}" WHERE {ident} IS NOT NULL'
        ).fetchone()
        count = row[0] if row else 0
        if count <= 30:
            rows = conn.execute(
                f'SELECT {ident} FROM "{table}" WHERE {ident} IS NOT NULL '
                f'GROUP BY {ident} ORDER BY COUNT(*) DESC, {ident} LIMIT 20'
            ).fetchall()
            col.known_values = [r[0] for r in rows]

    def execute_query(self, sql: str, limit: int = 100) -> pd.DataFrame:
        conn = self._get_connection()
        clean_sql = sql.strip().rstrip(";").strip()
        return pd.read_sql_query(clean_sql, conn)

    def sample_table(self, table: str, limit: int = 100) -> pd.DataFrame:
        return self.execute_query(f'SELECT * FROM "{table}" LIMIT {limit}')

    def get_dialect(self) -> str:
        return "sqlite"

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
