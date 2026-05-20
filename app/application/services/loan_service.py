"""Application service for loans.

Thin orchestration layer — verifies user/book existence before creating a
loan, then delegates to the LoanRepository port.
No SQLAlchemy or infrastructure imports.
"""

from datetime import date
from typing import Any

from app.application.errors import ConflictError, NotFoundError
from app.application.ports.book_repository import BookRepository
from app.application.ports.loan_repository import LoanRepository
from app.application.ports.user_repository import UserRepository


class LoanService:
    """Orchestrates loan operations through the LoanRepository port.

    Also accepts UserRepository and BookRepository ports to validate FK
    existence before creating a loan (fail-fast, clear error messages).
    """

    def __init__(
        self,
        repo: LoanRepository,
        user_repo: UserRepository,
        book_repo: BookRepository,
    ) -> None:
        self._repo = repo
        self._user_repo = user_repo
        self._book_repo = book_repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session: Any, id: int) -> Any:
        """Return the loan with *id*.

        Raises:
            NotFoundError: if no loan with that ID exists.
        """
        loan = self._repo.get_by_id(session, id)
        if loan is None:
            raise NotFoundError(f"Loan {id} not found.")
        return loan

    def list(self, session: Any) -> list[Any]:
        """Return all loans."""
        return self._repo.list_all(session)

    def get_by_user(self, session: Any, user_id: int) -> list[Any]:
        """Return all loans for *user_id*."""
        return self._repo.get_by_user(session, user_id)

    def get_by_book(self, session: Any, book_id: int) -> list[Any]:
        """Return all loans for *book_id*."""
        return self._repo.get_by_book(session, book_id)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new loan after verifying user and book existence.

        Raises:
            NotFoundError: if the referenced user or book does not exist.
            ConflictError: if the user has any active overdue loans.
            OutOfStockError: (propagated from the repo) if book stock = 0.
        """
        user_id = data.get("user_id") if isinstance(data, dict) else getattr(data, "user_id", None)
        book_id = data.get("book_id") if isinstance(data, dict) else getattr(data, "book_id", None)

        if user_id is not None and self._user_repo.get_by_id(session, user_id) is None:
            raise NotFoundError(f"User {user_id} not found.")
        if book_id is not None and self._book_repo.get_by_id(session, book_id) is None:
            raise NotFoundError(f"Book {book_id} not found.")

        if user_id is not None:
            today = date.today()
            overdue = [
                loan for loan in self._repo.get_by_user(session, user_id)
                if getattr(loan, "status", None) == "ACTIVE"
                and getattr(loan, "due_date", None) is not None
                and loan.due_date < today
            ]
            if overdue:
                raise ConflictError(
                    f"User {user_id} has {len(overdue)} overdue loan(s) and cannot borrow."
                )

        return self._repo.create(session, data)

    def update(self, session: Any, id: int, data: Any) -> Any:
        """Update an existing loan and return the updated instance.

        Raises:
            NotFoundError: if no loan with that ID exists.
        """
        updated = self._repo.update(session, id, data)
        if updated is None:
            raise NotFoundError(f"Loan {id} not found.")
        return updated

    def delete(self, session: Any, id: int) -> None:
        """Delete the loan with *id*.

        Raises:
            NotFoundError: if no loan with that ID exists.
        """
        deleted = self._repo.delete(session, id)
        if not deleted:
            raise NotFoundError(f"Loan {id} not found.")
