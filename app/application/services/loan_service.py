"""Application service for loan workflows."""

from typing import Any

from app.application.errors import ConflictError, NotFoundError
from app.application.ports.book_repository import BookRepository
from app.application.ports.loan_repository import LoanRepository
from app.application.ports.user_repository import UserRepository
from app.schemas.circulation.loans import LoanCreate


class LoanService:
    """Coordinate loan use cases without depending on FastAPI or SQLAlchemy."""

    def __init__(self, loan_repository: LoanRepository, user_repository: UserRepository, book_repository: BookRepository) -> None:
        self._loan_repository = loan_repository
        self._user_repository = user_repository
        self._book_repository = book_repository

    def list_loans(self, session: Any) -> list[Any]:
        """Return all loans."""

        return self._loan_repository.list_all(session)

    def get_loan(self, session: Any, loan_id: int) -> Any:
        """Return a loan or raise when it does not exist."""

        loan = self._loan_repository.get_by_id(session, loan_id)
        if loan is None:
            raise NotFoundError("Loan not found.")
        return loan

    def get_loans_by_user(self, session: Any, user_id: int) -> list[Any]:
        """Return a user's loan history after verifying the user exists."""

        self._ensure_user_exists(session, user_id)
        return self._loan_repository.get_by_user(session, user_id)

    def create_loan(self, session: Any, data: LoanCreate) -> Any:
        """Create a loan after application-owned workflow checks."""

        self._ensure_user_exists(session, data.user_id)
        self._ensure_book_exists(session, data.book_id)
        if self._loan_repository.has_overdue_loans(session, data.user_id):
            raise ConflictError("User has overdue loans.")
        return self._loan_repository.create(session, data)

    def _ensure_user_exists(self, session: Any, user_id: int) -> None:
        """Raise NotFoundError when the user does not exist."""

        if self._user_repository.get_by_id(session, user_id) is None:
            raise NotFoundError("User not found.")

    def _ensure_book_exists(self, session: Any, book_id: int) -> None:
        """Raise NotFoundError when the book does not exist."""

        if self._book_repository.get_by_id(session, book_id) is None:
            raise NotFoundError("Book not found.")


__all__ = ["LoanService"]
