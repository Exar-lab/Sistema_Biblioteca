"""Integration smoke tests for all 7 repositories.

REQUIREMENTS
------------
These tests require a live Oracle XE instance with the PR 1 schema applied.
Set the ``ORACLE_DSN`` environment variable before running:

    export ORACLE_DSN="BIBLIOTECA/<password>@localhost:1521/FREEPDB1"

All tests in this module are **automatically skipped** when ``ORACLE_DSN`` is
not set, so the CI pipeline passes without Oracle.

SCHEMA PRE-CONDITION
--------------------
PR 1 (``database/oracle_schema.sql``) must have been executed against the
target Oracle instance:

    sqlplus BIBLIOTECA/<pwd>@<dsn> @database/oracle_schema.sql

Verify all packages are VALID before running:

    SELECT object_name, object_type, status
      FROM user_objects
     WHERE object_type IN ('PACKAGE', 'PACKAGE BODY');
"""

from __future__ import annotations

import datetime
import os
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.infrastructure.repositories.role_repository import RoleRepository
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.infrastructure.repositories.author_repository import AuthorRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.book_repository import BookRepository
from app.infrastructure.repositories.loan_repository import LoanRepository
from app.infrastructure.repositories.return_repository import ReturnRepository

# ---------------------------------------------------------------------------
# Module-level skip guard
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    not os.getenv("ORACLE_DSN"),
    reason="ORACLE_DSN not set — integration tests require a live Oracle XE instance",
)

# ---------------------------------------------------------------------------
# Session fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def db_session():
    """Create a SQLAlchemy Session connected to the Oracle instance defined by ORACLE_DSN."""
    dsn = os.getenv("ORACLE_DSN", "")
    engine = create_engine(f"oracle+oracledb://{dsn}", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# RoleRepository integration smoke
# ---------------------------------------------------------------------------


class TestRoleRepositoryIntegration:
    def test_list_all(self, db_session) -> None:
        """list_all() should return a list (may be empty on a fresh schema)."""
        repo = RoleRepository()
        results = repo.list_all(db_session)
        assert isinstance(results, list)

    def test_create_get_delete_round_trip(self, db_session) -> None:
        """create → get_by_id → delete full round-trip."""
        from unittest.mock import MagicMock

        data = MagicMock()
        data.name = f"test_role_{os.getpid()}"
        data.description = "Integration test role"

        repo = RoleRepository()
        created = repo.create(db_session, data)
        assert created.id is not None

        fetched = repo.get_by_id(db_session, created.id)
        assert fetched is not None
        assert fetched.name == data.name

        deleted = repo.delete(db_session, created.id)
        assert deleted is True

        gone = repo.get_by_id(db_session, created.id)
        assert gone is None

    def test_delete_returns_false_for_missing_id(self, db_session) -> None:
        repo = RoleRepository()
        assert repo.delete(db_session, -999999) is False


# ---------------------------------------------------------------------------
# CategoryRepository integration smoke
# ---------------------------------------------------------------------------


class TestCategoryRepositoryIntegration:
    def test_list_all(self, db_session) -> None:
        repo = CategoryRepository()
        results = repo.list_all(db_session)
        assert isinstance(results, list)

    def test_create_get_delete_round_trip(self, db_session) -> None:
        from unittest.mock import MagicMock

        data = MagicMock()
        data.name = f"test_cat_{os.getpid()}"
        data.description = "Integration test category"
        data.is_active = True

        repo = CategoryRepository()
        created = repo.create(db_session, data)
        assert created.id is not None

        fetched = repo.get_by_id(db_session, created.id)
        assert fetched is not None

        deleted = repo.delete(db_session, created.id)
        assert deleted is True


# ---------------------------------------------------------------------------
# AuthorRepository integration smoke
# ---------------------------------------------------------------------------


class TestAuthorRepositoryIntegration:
    def test_list_all(self, db_session) -> None:
        repo = AuthorRepository()
        results = repo.list_all(db_session)
        assert isinstance(results, list)

    def test_create_get_delete_round_trip(self, db_session) -> None:
        from unittest.mock import MagicMock

        data = MagicMock()
        data.first_name = "Integration"
        data.last_name = f"Author_{os.getpid()}"
        data.biography = "Integration test author"
        data.birth_date = datetime.date(1980, 1, 1)
        data.death_date = None
        data.is_active = True

        repo = AuthorRepository()
        created = repo.create(db_session, data)
        assert created.id is not None

        deleted = repo.delete(db_session, created.id)
        assert deleted is True


# ---------------------------------------------------------------------------
# UserRepository integration smoke
# ---------------------------------------------------------------------------


class TestUserRepositoryIntegration:
    def test_list_all(self, db_session) -> None:
        repo = UserRepository()
        results = repo.list_all(db_session)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# BookRepository integration smoke
# ---------------------------------------------------------------------------


class TestBookRepositoryIntegration:
    def test_list_all(self, db_session) -> None:
        repo = BookRepository()
        results = repo.list_all(db_session)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# LoanRepository integration smoke
# ---------------------------------------------------------------------------


class TestLoanRepositoryIntegration:
    def test_list_all(self, db_session) -> None:
        repo = LoanRepository()
        results = repo.list_all(db_session)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# ReturnRepository integration smoke
# ---------------------------------------------------------------------------


class TestReturnRepositoryIntegration:
    def test_list_all(self, db_session) -> None:
        repo = ReturnRepository()
        results = repo.list_all(db_session)
        assert isinstance(results, list)
