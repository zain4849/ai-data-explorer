"""MySQL connector using PyMySQL."""

import pandas as pd
import pymysql

from .base import DataConnector
from .types import ColumnInfo, ConnectionConfig, TableInfo


class MySQLConnector(DataConnector):
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._conn = None

    def _get_connection(self):
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(
                host=self.config.host,
                port=self.config.port or 3306,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                ssl={"ssl": True} if self.config.ssl else None,
                connect_timeout=10,
                read_timeout=30,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
        return self._conn

    def test_connection(self) -> bool:
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True

    def get_tables(self) -> list[TableInfo]:
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_ROWS
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
                ORDER BY TABLE_NAME
            """, (self.config.database,))
            return [
                TableInfo(
                    name=row["TABLE_NAME"],
                    schema=row["TABLE_SCHEMA"],
                    row_count=row["TABLE_ROWS"],
                )
                for row in cur.fetchall()
            ]

    def get_table_schema(self, table: str) -> list[ColumnInfo]:
        conn = self._get_connection()
        columns: list[ColumnInfo] = []

        with conn.cursor() as cur:
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (self.config.database, table))

            for row in cur.fetchall():
                columns.append(ColumnInfo(
                    name=row["COLUMN_NAME"],
                    data_type=row["DATA_TYPE"],
                    nullable=row["IS_NULLABLE"] == "YES",
                    is_pk=row["COLUMN_KEY"] == "PRI",
                ))

            # Foreign keys
            cur.execute("""
                SELECT COLUMN_NAME,
                       CONCAT(REFERENCED_TABLE_SCHEMA, '.', REFERENCED_TABLE_NAME, '.', REFERENCED_COLUMN_NAME)
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                  AND REFERENCED_TABLE_NAME IS NOT NULL
            """, (self.config.database, table))

            fk_map = {row["COLUMN_NAME"]: row[list(row.keys())[1]] for row in cur.fetchall()}
            for col in columns:
                col.fk_reference = fk_map.get(col.name)

            for col in columns:
                if col.data_type in ("varchar", "char", "text", "enum", "set"):
                    self._populate_known_values(conn, table, col)

        return columns

    def _populate_known_values(self, conn, table: str, col: ColumnInfo):
        with conn.cursor() as cur:
            ident = f"`{col.name}`"
            cur.execute(
                f"SELECT COUNT(DISTINCT {ident}) FROM `{table}` WHERE {ident} IS NOT NULL"
            )
            result = cur.fetchone()
            count = list(result.values())[0] if result else 0
            if count <= 30:
                cur.execute(
                    f"SELECT {ident} FROM `{table}` WHERE {ident} IS NOT NULL "
                    f"GROUP BY {ident} ORDER BY COUNT(*) DESC, {ident} LIMIT 20"
                )
                col.known_values = [list(row.values())[0] for row in cur.fetchall()]

    def execute_query(self, sql: str, limit: int = 100) -> pd.DataFrame:
        conn = self._get_connection()
        clean_sql = sql.strip().rstrip(";").strip()
        return pd.read_sql_query(clean_sql, conn)

    def sample_table(self, table: str, limit: int = 100) -> pd.DataFrame:
        return self.execute_query(f"SELECT * FROM `{table}` LIMIT {limit}")

    def get_dialect(self) -> str:
        return "mysql"

    def close(self):
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None
