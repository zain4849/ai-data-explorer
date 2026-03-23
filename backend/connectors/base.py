from abc import ABC, abstractmethod

import pandas as pd

from .types import ColumnInfo, TableInfo


class DataConnector(ABC):
    """Abstract base class for all data source connectors."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Return True if the connection is working, raise on failure."""
        ...

    @abstractmethod
    def get_tables(self) -> list[TableInfo]:
        """List all accessible tables/views."""
        ...

    @abstractmethod
    def get_table_schema(self, table: str) -> list[ColumnInfo]:
        """Return column metadata for a specific table."""
        ...

    @abstractmethod
    def execute_query(self, sql: str, limit: int = 100) -> pd.DataFrame:
        """Execute a SQL query and return results as a DataFrame."""
        ...

    @abstractmethod
    def sample_table(self, table: str, limit: int = 100) -> pd.DataFrame:
        """Return a sample of rows from the given table."""
        ...

    @abstractmethod
    def get_dialect(self) -> str:
        """Return the SQL dialect name (e.g. 'duckdb', 'postgresql', 'mysql')."""
        ...

    def close(self):
        """Release resources. Override if the connector holds a persistent connection."""
        pass
