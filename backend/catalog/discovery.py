"""Schema discovery: introspect tables, columns, types, and foreign keys from a connector."""

from ..connectors.base import DataConnector
from ..connectors.types import ColumnInfo, TableInfo
from ..logger_config import logger


def discover_schema(connector: DataConnector) -> list[TableInfo]:
    """Discover full schema from a data source connector.

    Returns a list of TableInfo objects with their columns populated.
    """
    tables = connector.get_tables()
    logger.info("Discovered %d tables/views", len(tables))

    for table in tables:
        try:
            table.columns = connector.get_table_schema(table.qualified_name)
        except Exception as exc:
            logger.warning("Could not introspect schema for %s: %s", table.name, exc)
            table.columns = []

    return tables
