"""DuckDB-backed connector for uploaded file data (CSV, Excel, JSON)."""

import duckdb
import pandas as pd

from .base import DataConnector
from .types import ColumnInfo, TableInfo


class FileConnector(DataConnector):
    """Wraps the existing in-memory DuckDB database used for uploaded files."""

    def __init__(self, conn: duckdb.DuckDBPyConnection | None = None):
        self.conn = conn or duckdb.connect(database=":memory:")

    def test_connection(self) -> bool:
        self.conn.execute("SELECT 1")
        return True

    def load_dataframe(self, df: pd.DataFrame, table_name: str = "data"):
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

    def get_tables(self) -> list[TableInfo]:
        rows = self.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        tables = []
        for (name,) in rows:
            count_row = self.conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()
            tables.append(TableInfo(name=name, row_count=count_row[0] if count_row else None))
        return tables

    def get_table_schema(self, table: str = "data") -> list[ColumnInfo]:
        result = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        columns: list[ColumnInfo] = []
        for row in result:
            col = ColumnInfo(
                name=row[1],
                data_type=row[2],
                nullable=not row[3],
                is_pk=bool(row[5]),
            )
            col_type = col.data_type.upper()
            if any(t in col_type for t in ("CHAR", "TEXT", "VARCHAR")):
                self._populate_known_values(table, col)
            columns.append(col)
        return columns

    def _populate_known_values(self, table: str, col: ColumnInfo):
        ident = f'"{col.name}"'
        distinct_count = self.conn.execute(
            f"SELECT COUNT(DISTINCT {ident}) FROM {table} WHERE {ident} IS NOT NULL"
        ).fetchone()
        if distinct_count and distinct_count[0] <= 30:
            sample_values = self.conn.execute(
                f"SELECT {ident} FROM {table} WHERE {ident} IS NOT NULL "
                f"GROUP BY {ident} ORDER BY COUNT(*) DESC, {ident} LIMIT 20"
            ).fetchall()
            col.known_values = [row[0] for row in sample_values]

    def execute_query(self, sql: str, limit: int = 100) -> pd.DataFrame:
        clean_sql = sql.strip().rstrip(";").strip()
        return self.conn.execute(clean_sql).fetchdf()

    def sample_table(self, table: str, limit: int = 100) -> pd.DataFrame:
        return self.conn.execute(f'SELECT * FROM "{table}" LIMIT {limit}').fetchdf()

    def get_dialect(self) -> str:
        return "duckdb"

    def get_schema_as_dicts(self, table: str = "data") -> list[dict]:
        """Backward-compatible: return schema as list of dicts matching old db.get_schema() format."""
        return [c.to_dict() for c in self.get_table_schema(table)]
