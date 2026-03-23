import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SchemaCache(Base):
    __tablename__ = "schema_cache"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    connection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    column_type: Mapped[str] = mapped_column(String(100), nullable=False)
    nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pk: Mapped[bool] = mapped_column(Boolean, default=False)
    fk_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    connection = relationship("DataConnection", back_populates="schema_cache")
