"""LoanRepository outbound port."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoanRepository(Protocol):
    """Contract for loan persistence.

    Extends the base CRUD contract with user/book query methods.
    May raise OutOfStockError from create when Oracle trigger fires -20001.
    """

    def get_by_id(self, session: Any, id: int) -> Any | None:
        """Return the loan with *id*, or None if it does not exist."""
        ...

    def list_all(self, session: Any) -> list[Any]:
        """Return all loans."""
        ...

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new loan and return the created instance.

        Raises OutOfStockError if the book has no available stock.
        """
        ...

    def update(self, session: Any, id: int, data: Any) -> Any:
        """Update the loan with *id* and return the updated instance."""
        ...

    def delete(self, session: Any, id: int) -> bool:
        """Delete the loan with *id*. Return True if deleted, False if not found."""
        ...

    def get_by_user(self, session: Any, user_id: int) -> list[Any]:
        """Return all loans for the given *user_id*."""
        ...

    def get_by_book(self, session: Any, book_id: int) -> list[Any]:
        """Return all loans for the given *book_id*."""
        ...

    def has_overdue_loans(self, session: Any, user_id: int) -> bool:
        """Return True if the user has any ACTIVE loans with due_date before today."""
        ...
