"""BookRepository outbound port."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BookRepository(Protocol):
    """Contract for book persistence.

    Extends the base CRUD contract with author-relationship operations.
    """

    def get_by_id(self, session: Any, id: int) -> Any | None:
        """Return the book with *id*, or None if it does not exist."""
        ...

    def list_all(self, session: Any) -> list[Any]:
        """Return all books."""
        ...

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new book and return the created instance."""
        ...

    def update(self, session: Any, id: int, data: Any) -> Any | None:
        """Update the book with *id*, or return None if it does not exist."""
        ...

    def delete(self, session: Any, id: int) -> bool:
        """Delete the book with *id*. Return True if deleted, False if not found."""
        ...

    def get_with_authors(self, session: Any, id: int) -> Any | None:
        """Return the book with *id* with its authors pre-loaded, or None."""
        ...

    def set_authors(self, session: Any, book_id: int, author_ids: list[int]) -> None:
        """Replace the book's author associations with the given *author_ids*."""
        ...
