"""Integration tests for LoanRepositorySql.

Requires a live Oracle XEPDB1 instance with the BIBLIOTECA schema and
seed data (at minimum one library_user row and one book row with
available_stock > 0).

Run with:
    python -m pytest tests/integration/test_loan_repository.py -m integration -v
"""

import datetime

import pytest
from sqlalchemy.orm import Session

from app.application.errors import OutOfStockError
from app.domain.models.loan import Loan
from app.infrastructure.repositories.loan_repository import LoanRepositorySql


@pytest.mark.integration
class TestLoanRepositoryCreate:
    """LoanRepositorySql.create() against a real Oracle database."""

    def test_create_with_valid_stock_inserts_row_and_returns_loan(
        self,
        db_session: Session,
    ) -> None:
        """Creating a loan against a book with stock returns a persisted Loan."""
        repo = LoanRepositorySql()

        # These IDs must exist in the seed data of the target Oracle instance.
        data = {
            "user_id": 1,
            "book_id": 1,
            "due_date": datetime.date.today() + datetime.timedelta(days=14),
        }

        loan = repo.create(db_session, data)

        assert isinstance(loan, Loan)
        assert loan.id is not None
        assert loan.user_id == data["user_id"]
        assert loan.book_id == data["book_id"]
        assert loan.status is not None  # server default 'ACTIVE' was applied

    def test_create_raises_out_of_stock_when_trigger_fires(
        self,
        db_session: Session,
    ) -> None:
        """When Oracle trigger ORA-20001 fires, OutOfStockError must bubble up.

        To trigger ORA-20001 reliably we use a book_id whose available_stock
        is 0.  If no such book exists in the seed data, this test is expected
        to be skipped by the test author when configuring the integration suite.
        Adjust ``zero_stock_book_id`` to match the real seed.
        """
        repo = LoanRepositorySql()

        # Set this to a book_id whose available_stock is 0 in the test DB.
        zero_stock_book_id = 999  # adjust to match test-DB seed data

        data = {
            "user_id": 1,
            "book_id": zero_stock_book_id,
            "due_date": datetime.date.today() + datetime.timedelta(days=14),
        }

        with pytest.raises(OutOfStockError):
            repo.create(db_session, data)
