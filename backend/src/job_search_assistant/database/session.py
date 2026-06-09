"""Database engine and request-scoped session dependency."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from job_search_assistant.core.settings import get_settings


def create_database_engine(database_url: str) -> Engine:
    """Create an engine with SQLite-specific thread support when needed."""

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine = create_database_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one SQLAlchemy session per API request."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
