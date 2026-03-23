from dataclasses import dataclass, field
from enum import Enum


class ConnectorType(str, Enum):
    DUCKDB = "duckdb"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool = True
    is_pk: bool = False
    fk_reference: str | None = None
    known_values: list[str] | None = None

    def to_dict(self) -> dict:
        d: dict = {"name": self.name, "type": self.data_type}
        if self.known_values:
            d["known_values"] = self.known_values
        if self.is_pk:
            d["is_pk"] = True
        if self.fk_reference:
            d["fk_reference"] = self.fk_reference
        return d


@dataclass
class TableInfo:
    name: str
    schema: str | None = None
    row_count: int | None = None
    columns: list[ColumnInfo] = field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        if self.schema and self.schema != "public":
            return f"{self.schema}.{self.name}"
        return self.name


@dataclass
class ConnectionConfig:
    """Decrypted connection parameters."""
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    # For SQLite: file path instead of host/port
    file_path: str | None = None
    # Optional extras
    ssl: bool = False
    options: dict | None = None
