"""Integration tests for ReturnRepositorySql.

Requires a live Oracle XEPDB1 instance with the BIBLIOTECA schema and an
existing ACTIVE loan row that can be returned.

Run with:
    python -m pytest tests/integration/test_return_repository.py -m integration -v
"""

import os

import pytest
from sqlalchemy.orm import Session

from app.domain.models.loan import Loan
from app.domain.models.return_ import Return_
from app.infrastructure.repositories.loan_repository import LoanRepositorySql
from app.infrastructure.repositories.return_repository import ReturnRepositorySql


@pytest.mark.integration
class TestReturnRepositoryCreate:
    """ReturnRepositorySql.create() against a real Oracle database."""

    def test_loan_status_reflects_returned_after_create(
        self,
        db_session: Session,
    ) -> None:
        """After creating a return, the related loan's status should be 'RETURNED'.

        Flow:
        1. Create a new loan (so we control its ID and can return it cleanly).
        2. Create a return for that loan, passing the loan_instance so the
           repository expires the stale ORM attributes.
        3. Access loan.status — SQLAlchemy must re-fetch from Oracle, picking
           up the server-side trigger update.

        Prerequisite: TEST_RETURN_USER_ID and TEST_RETURN_BOOK_ID must point to
        existing rows, and the book must have available stock.
        """
        import datetime

        user_id_env = os.getenv("TEST_RETURN_USER_ID")
        book_id_env = os.getenv("TEST_RETURN_BOOK_ID")
        if not user_id_env or not book_id_env:
            pytest.skip(
                "TEST_RETURN_USER_ID and TEST_RETURN_BOOK_ID must be set for return integration tests"
            )
        user_id = int(user_id_env)
        book_id = int(book_id_env)

        loan_repo = LoanRepositorySql()
        return_repo = ReturnRepositorySql()

        # Step 1: create a fresh loan
        loan_data = {
            "user_id": user_id,
            "book_id": book_id,
            "due_date": datetime.date.today() + datetime.timedelta(days=14),
        }
        loan: Loan = loan_repo.create(db_session, loan_data)
        assert loan.id is not None

        # Step 2: create a return for that loan, passing loan_instance so the
        # repository calls session.expire on the stale attributes
        return_data = {
            "loan_id": loan.id,
        }
        return_obj: Return_ = return_repo.create(
            db_session,
            return_data,
            loan_instance=loan,
        )

        assert isinstance(return_obj, Return_)
        assert return_obj.loan_id == loan.id

        # Step 3: verify loan.status was updated server-side by the trigger.
        # The repository expired [status, return_date] so accessing loan.status
        # forces a fresh SELECT from Oracle.
        assert loan.status == "RETURNED"
