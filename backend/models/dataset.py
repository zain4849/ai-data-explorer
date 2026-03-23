"""Dataset model: tracks uploaded files and their DuckDB tables per user."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: str = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: str = Column(String, ForeignKey("users.id"), nullable=False)
    name: str = Column(String, nullable=False)
    table_name: str = Column(String, nullable=False)
    file_path: str = Column(String, nullable=False)
    file_type: str = Column(String, nullable=False)
    row_count: int = Column(Integer, default=0)
    columns_json: str = Column(Text, default="[]")
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    owner = relationship("User", backref="datasets")
