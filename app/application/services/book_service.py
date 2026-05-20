"""Application service for books.

Thin orchestration layer — no SQLAlchemy or infrastructure imports.
Delegates author-relationship operations to the BookRepository port's
extended contract (get_with_authors, set_authors).
"""

from __future__ import annotations

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.author_repository import AuthorRepository
from app.application.ports.book_repository import BookRepository


class BookService:
    """Orchestrates book operations through the BookRepository port."""

    def __init__(self, repo: BookRepository, author_repo: AuthorRepository) -> None:
        self._repo = repo
        self._author_repo = author_repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session: Any, id: int) -> Any:
        """Return the book with *id*.

        Raises:
            NotFoundError: if no book with that ID exists.
        """
        book = self._repo.get_by_id(session, id)
        if book is None:
            raise NotFoundError(f"Book {id} not found.")
        return book

    def get_with_authors(self, session: Any, id: int) -> Any:
        """Return the book with *id* with its authors eagerly loaded.

        Raises:
            NotFoundError: if no book with that ID exists.
        """
        book = self._repo.get_with_authors(session, id)
        if book is None:
            raise NotFoundError(f"Book {id} not found.")
        return book

    def list(self, session: Any) -> list[Any]:
        """Return all books."""
        return self._repo.list_all(session)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new book and return it."""
        return self._repo.create(session, data)

    def update(self, session: Any, id: int, data: Any) -> Any:
        """Update an existing book and return the updated instance.

        Raises:
            NotFoundError: if no book with that ID exists.
        """
        updated = self._repo.update(session, id, data)
        if updated is None:
            raise NotFoundError(f"Book {id} not found.")
        return updated

    def delete(self, session: Any, id: int) -> None:
        """Delete the book with *id*.

        Raises:
            NotFoundError: if no book with that ID exists.
        """
        deleted = self._repo.delete(session, id)
        if not deleted:
            raise NotFoundError(f"Book {id} not found.")

    def set_authors(self, session: Any, book_id: int, author_ids: list[int]) -> None:
        """Replace the book's author associations.

        Raises:
            NotFoundError: if no book with *book_id* exists.
        """
        book = self._repo.get_by_id(session, book_id)
        if book is None:
            raise NotFoundError(f"Book {book_id} not found.")

        missing_author_ids = [
            author_id
            for author_id in author_ids
            if self._author_repo.get_by_id(session, author_id) is None
        ]
        if missing_author_ids:
            missing = ", ".join(str(author_id) for author_id in missing_author_ids)
            raise NotFoundError(f"Author(s) not found: {missing}.")

        self._repo.set_authors(session, book_id, author_ids)
