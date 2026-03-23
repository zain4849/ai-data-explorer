import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class DataConnection(Base):
    __tablename__ = "data_connections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    db_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Fernet-encrypted JSON blob with host, port, database, username, password, etc.
    config_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    # AI policy controls
    allow_ai_access: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_rows_to_ai: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    # Comma-separated column names to mask before sending to AI
    mask_columns: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = relationship("User", back_populates="connections")
    schema_cache = relationship("SchemaCache", back_populates="connection", cascade="all, delete-orphan")
