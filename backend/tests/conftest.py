"""Shared test fixtures and isolated API database setup."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

os.environ["DATABASE_URL"] = "sqlite://"

from job_search_assistant.database.base import Base
from job_search_assistant.database.session import create_database_engine, get_db
from job_search_assistant.main import app

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_resume() -> str:
    """Return the synthetic sample resume."""

    return (FIXTURE_DIR / "sample_resume.txt").read_text(encoding="utf-8")


@pytest.fixture
def sample_job() -> str:
    """Return the synthetic sample job description."""

    return (FIXTURE_DIR / "sample_job_description.txt").read_text(encoding="utf-8")


@pytest.fixture
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    """Provide an isolated SQLite session."""

    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide an API client whose application repository uses the test database."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
