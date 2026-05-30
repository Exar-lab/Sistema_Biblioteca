"""Application service for book workflows."""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.book_repository import BookRepository
from app.schemas.catalog.books import BookCreate, BookUpdate


class BookService:
    """Coordinate book use cases without depending on FastAPI or SQLAlchemy."""

    def __init__(self, repository: BookRepository) -> None:
        self._repository = repository

    def list_books(self, session: Any) -> list[Any]:
        """Return all books."""

        return self._repository.list_all(session)

    def get_book(self, session: Any, book_id: int) -> Any:
        """Return a book or raise when it does not exist."""

        book = self._repository.get_with_authors(session, book_id)
        if book is None:
            raise NotFoundError("Book not found.")
        return book

    def create_book(self, session: Any, data: BookCreate) -> Any:
        """Create a book."""

        return self._repository.create(session, data)

    def update_book(self, session: Any, book_id: int, data: BookUpdate) -> Any:
        """Update a book or raise when it does not exist."""

        book = self._repository.update(session, book_id, data)
        if book is None:
            raise NotFoundError("Book not found.")
        return book

    def delete_book(self, session: Any, book_id: int) -> None:
        """Delete a book or raise when it does not exist."""

        deleted = self._repository.delete(session, book_id)
        if deleted is False:
            raise NotFoundError("Book not found.")


__all__ = ["BookService"]
