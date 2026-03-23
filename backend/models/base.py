from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import settings

_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    pass


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session() -> Session:
    """FastAPI dependency that yields a DB session and closes it after the request."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Create all tables (used for dev/testing; production uses Alembic)."""
    Base.metadata.create_all(bind=get_engine())
