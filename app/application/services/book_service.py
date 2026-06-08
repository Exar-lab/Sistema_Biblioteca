"""Application service for book workflows."""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.book_repository import BookRepository
from app.schemas.catalog.books import BookCreate, BookUpdate


class BookService:
    """Coordinate book use cases without depending on FastAPI or SQLAlchemy."""

    def __init__(self, repository: BookRepository) -> None:
        self._repository = repository

    def list_books(
        self,
        session: Any,
        *,
        title: str | None = None,
        author: str | None = None,
        category: str | None = None,
    ) -> list[Any]:
        """Return all books, forwarding optional filters to the repository."""

        return self._repository.list_all(
            session, title=title, author=author, category=category
        )

    def get_book(self, session: Any, book_id: int) -> Any:
        """Return a book or raise when it does not exist."""

        book = self._repository.get_with_authors(session, book_id)
        if book is None:
            raise NotFoundError("Book not found.")
        return book

    def create_book(self, session: Any, data: BookCreate) -> Any:
        """Create a book."""

        book = self._repository.create(session, data)
        self._repository.set_authors(session, book.id, data.author_ids)
        return self._repository.get_with_authors(session, book.id) or book

    def update_book(self, session: Any, book_id: int, data: BookUpdate) -> Any:
        """Update a book or raise when it does not exist."""

        book = self._repository.update(session, book_id, data)
        if book is None:
            raise NotFoundError("Book not found.")
        if data.author_ids is not None:
            self._repository.set_authors(session, book_id, data.author_ids)
        return self._repository.get_with_authors(session, book_id) or book

    def delete_book(self, session: Any, book_id: int) -> None:
        """Delete a book or raise when it does not exist."""

        deleted = self._repository.delete(session, book_id)
        if deleted is False:
            raise NotFoundError("Book not found.")


__all__ = ["BookService"]
