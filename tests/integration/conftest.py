"""Integration test fixtures.

Requires a live Oracle XEPDB1 instance.  Tests in this package must be
invoked with:

    python -m pytest tests/integration/ -m integration -v

or simply

    python -m pytest tests/integration/ -v

A session is opened for each test function and rolled back (or closed) after.
Set RUN_ORACLE_INTEGRATION_TESTS=1 and DATABASE_URL to opt in; otherwise
integration tests are skipped automatically.
"""

import os

import pytest
from sqlalchemy.orm import Session


@pytest.fixture()
def db_session() -> Session:
    """Yield a real Oracle session; rollback and close after the test."""
    if os.getenv("RUN_ORACLE_INTEGRATION_TESTS") != "1":
        pytest.skip(
            "RUN_ORACLE_INTEGRATION_TESTS=1 is required for Oracle integration tests"
        )
    if not os.getenv("DATABASE_URL"):
        pytest.skip("Oracle DATABASE_URL not set — skipping integration tests")

    from app.core.database import SessionLocal

    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
