import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tiles = relationship("DashboardTile", back_populates="dashboard", cascade="all, delete-orphan")


class DashboardTile(Base):
    __tablename__ = "dashboard_tiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dashboard_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tile_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # JSON-encoded configuration: query, chart_type, connection_id, etc.
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    # Grid layout: x, y, width, height
    grid_x: Mapped[int] = mapped_column(Integer, default=0)
    grid_y: Mapped[int] = mapped_column(Integer, default=0)
    grid_w: Mapped[int] = mapped_column(Integer, default=4)
    grid_h: Mapped[int] = mapped_column(Integer, default=3)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    dashboard = relationship("Dashboard", back_populates="tiles")
