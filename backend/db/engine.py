"""SQLAlchemy engine and session factory.

- Default DB: SQLite (sqlite:///app.db). Override via DATABASE_URL for Postgres.
- Exposes get_engine(), SessionLocal, and init_db() to create tables.
- Auto-initializes tables on import for a smooth first-run experience.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///app.db")


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite://")


DATABASE_URL = get_database_url()
_engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if _is_sqlite(DATABASE_URL) else {},
)
SessionLocal = sessionmaker(
    bind=_engine, autoflush=False, autocommit=False, future=True
)


def get_engine():
    return _engine


def init_db() -> None:
    # Import models inside function to avoid circular imports
    from backend.db import models  # noqa: F401

    models.Base.metadata.create_all(bind=_engine)


# Auto-initialize tables for simple setup (esp. for SQLite)
try:
    if _is_sqlite(DATABASE_URL):
        init_db()
except Exception:
    # Avoid crashing on import, initialization can be called explicitly by app startup if needed
    pass
