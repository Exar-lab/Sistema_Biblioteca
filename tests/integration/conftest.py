"""Integration test fixtures.

Requires a live Oracle XEPDB1 instance.  Tests in this package must be
invoked with:

    python -m pytest tests/integration/ -m integration -v

or simply

    python -m pytest tests/integration/ -v

A session is opened for each test function and rolled back (or closed) after.
The DATABASE_URL env-var must point to the real Oracle instance.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


@pytest.fixture()
def db_session() -> Session:
    """Yield a real Oracle session; rollback and close after the test."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
