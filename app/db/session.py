"""Database engine/session utilities for SQLite (Unit 5)."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base


def get_engine():
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, future=True, connect_args=connect_args)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create DB schema if missing."""
    import app.models.analysis  # noqa: F401
    import app.models.feedback  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

