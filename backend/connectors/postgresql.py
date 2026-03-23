"""PostgreSQL connector using psycopg2."""

import pandas as pd
import psycopg2
import psycopg2.extras

from .base import DataConnector
from .types import ColumnInfo, ConnectionConfig, TableInfo


class PostgreSQLConnector(DataConnector):
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._conn = None

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                dbname=self.config.database,
                user=self.config.username,
                password=self.config.password,
                sslmode="require" if self.config.ssl else "prefer",
                connect_timeout=10,
            )
            self._conn.set_session(readonly=True, autocommit=True)
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
                SELECT t.table_schema, t.table_name,
                       (SELECT reltuples::bigint FROM pg_class
                        WHERE oid = (quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass)
                FROM information_schema.tables t
                WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
                  AND t.table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY t.table_schema, t.table_name
            """)
            return [
                TableInfo(name=row[1], schema=row[0], row_count=max(0, row[2]) if row[2] else None)
                for row in cur.fetchall()
            ]

    def get_table_schema(self, table: str) -> list[ColumnInfo]:
        schema_name, table_name = self._split_table(table)
        conn = self._get_connection()
        columns: list[ColumnInfo] = []

        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.column_name, c.data_type, c.is_nullable,
                       CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END AS is_pk
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                      AND tc.table_schema = %s AND tc.table_name = %s
                ) pk ON c.column_name = pk.column_name
                WHERE c.table_schema = %s AND c.table_name = %s
                ORDER BY c.ordinal_position
            """, (schema_name, table_name, schema_name, table_name))

            for row in cur.fetchall():
                columns.append(ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2] == "YES",
                    is_pk=row[3],
                ))

            # Foreign keys
            cur.execute("""
                SELECT kcu.column_name,
                       ccu.table_schema || '.' || ccu.table_name || '.' || ccu.column_name
                FROM information_schema.referential_constraints rc
                JOIN information_schema.key_column_usage kcu
                  ON rc.constraint_name = kcu.constraint_name AND rc.constraint_schema = kcu.constraint_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON rc.unique_constraint_name = ccu.constraint_name AND rc.unique_constraint_schema = ccu.constraint_schema
                WHERE kcu.table_schema = %s AND kcu.table_name = %s
            """, (schema_name, table_name))

            fk_map = {row[0]: row[1] for row in cur.fetchall()}
            for col in columns:
                col.fk_reference = fk_map.get(col.name)

            # Known values for low-cardinality text columns
            for col in columns:
                if col.data_type in ("text", "character varying", "character", "varchar"):
                    self._populate_known_values(conn, schema_name, table_name, col)

        return columns

    def _populate_known_values(self, conn, schema_name: str, table_name: str, col: ColumnInfo):
        with conn.cursor() as cur:
            fq = f'"{schema_name}"."{table_name}"'
            ident = f'"{col.name}"'
            cur.execute(f"SELECT COUNT(DISTINCT {ident}) FROM {fq} WHERE {ident} IS NOT NULL")
            count = cur.fetchone()[0]
            if count <= 30:
                cur.execute(
                    f"SELECT {ident} FROM {fq} WHERE {ident} IS NOT NULL "
                    f"GROUP BY {ident} ORDER BY COUNT(*) DESC, {ident} LIMIT 20"
                )
                col.known_values = [row[0] for row in cur.fetchall()]

    def execute_query(self, sql: str, limit: int = 100) -> pd.DataFrame:
        conn = self._get_connection()
        clean_sql = sql.strip().rstrip(";").strip()
        return pd.read_sql_query(clean_sql, conn)

    def sample_table(self, table: str, limit: int = 100) -> pd.DataFrame:
        schema_name, table_name = self._split_table(table)
        fq = f'"{schema_name}"."{table_name}"'
        return self.execute_query(f"SELECT * FROM {fq} LIMIT {limit}")

    def get_dialect(self) -> str:
        return "postgresql"

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

    @staticmethod
    def _split_table(table: str) -> tuple[str, str]:
        parts = table.split(".", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return "public", parts[0]
