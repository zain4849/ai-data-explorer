"""Connector registry: instantiate the right connector from a type + config."""

from .base import DataConnector
from .types import ConnectionConfig, ConnectorType


def get_connector(db_type: str | ConnectorType, config: ConnectionConfig | None = None) -> DataConnector:
    """Create and return a DataConnector instance for the given type and config."""
    if isinstance(db_type, str):
        db_type = ConnectorType(db_type.lower())

    if db_type == ConnectorType.DUCKDB:
        from .file_connector import FileConnector
        return FileConnector()

    if db_type == ConnectorType.POSTGRESQL:
        from .postgresql import PostgreSQLConnector
        if config is None:
            raise ValueError("ConnectionConfig is required for PostgreSQL")
        return PostgreSQLConnector(config)

    if db_type == ConnectorType.MYSQL:
        from .mysql import MySQLConnector
        if config is None:
            raise ValueError("ConnectionConfig is required for MySQL")
        return MySQLConnector(config)

    if db_type == ConnectorType.SQLITE:
        from .sqlite import SQLiteConnector
        if config is None:
            raise ValueError("ConnectionConfig is required for SQLite")
        return SQLiteConnector(config)

    raise ValueError(f"Unsupported connector type: {db_type}")
