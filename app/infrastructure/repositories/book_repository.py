"""SQLAlchemy adapter for BookRepository port.

Extends the generic base with author-relationship operations:
- ``get_with_authors``: loads the book together with its authors via selectinload.
- ``set_authors``: transactional replace of book_authors association rows.
"""

from typing import Any

from sqlalchemy import delete, insert
from sqlalchemy.orm import Session, selectinload

from app.domain.models.book import Book, book_authors
from app.infrastructure.repositories.base import SqlRepositoryBase


class BookRepositorySql(SqlRepositoryBase[Book]):
    """Concrete repository for BIBLIOTECA.books.

    Structurally satisfies the ``BookRepository`` typing.Protocol.
    """

    model = Book

    # ------------------------------------------------------------------
    # Author-relationship operations
    # ------------------------------------------------------------------

    def get_with_authors(self, session: Session, id: int) -> Book | None:
        """Return the book with *id* with its authors eagerly loaded.

        Uses ``selectinload`` (surgical — avoids touching the default lazy
        strategy on the relationship definition).
        """
        return (
            session.query(Book)
            .options(selectinload(Book.authors))
            .filter(Book.id == id)
            .first()
        )

    def set_authors(
        self, session: Session, book_id: int, author_ids: list[int]
    ) -> None:
        """Replace all author associations for *book_id* with *author_ids*.

        Executes DELETE + bulk INSERT then flushes within the current session.
        """
        author_ids = list(dict.fromkeys(author_ids))  # deduplicate preserving order
        # Delete existing associations
        session.execute(
            delete(book_authors).where(book_authors.c.book_id == book_id)
        )
        # Bulk insert new associations
        if author_ids:
            session.execute(
                insert(book_authors),
                [{"book_id": book_id, "author_id": aid} for aid in author_ids],
            )
        session.flush()

    # ------------------------------------------------------------------
    # Override list to include authors by default
    # ------------------------------------------------------------------

    def list_all(self, session: Session) -> list[Book]:
        """Return all books with authors pre-loaded."""
        return (
            session.query(Book)
            .options(selectinload(Book.authors))
            .order_by(Book.id)
            .all()
        )
