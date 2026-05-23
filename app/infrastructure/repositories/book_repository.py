"""SQLAlchemy adapter for book persistence."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.application.errors import ConflictError, NotFoundError
from app.domain.models.author import Author
from app.domain.models.book import Book
from app.schemas.catalog.books import BookCreate, BookUpdate


class SqlAlchemyBookRepository:
    """Persist books and book-author relationships using SQLAlchemy ORM models."""

    def get_by_id(self, session: Session, id: int) -> Book | None:
        """Return the book with *id*, or None if it does not exist."""

        return session.get(Book, id)

    def get_with_authors(self, session: Session, id: int) -> Book | None:
        """Return the book with authors and category loaded, or None."""

        return session.scalar(self._with_relationships().where(Book.id == id))

    def list_all(self, session: Session) -> list[Book]:
        """Return books ordered by title for stable API responses."""

        return list(session.scalars(self._with_relationships().order_by(Book.title)).all())

    def create(self, session: Session, data: BookCreate) -> Book:
        """Persist a new book and return the created instance."""

        values = data.model_dump()
        author_ids = values.pop("author_ids")
        values["stock_available"] = values["stock_total"]
        book = Book(**values)
        session.add(book)
        if author_ids:
            self._set_author_models(session, book, author_ids)
        return self._flush_refresh_and_load(session, book)

    def update(self, session: Session, id: int, data: BookUpdate) -> Book | None:
        """Update the book with *id* and return it, or None if missing."""

        book = self.get_by_id(session, id)
        if book is None:
            return None

        values = data.model_dump(exclude_unset=True)
        author_ids = values.pop("author_ids", None)
        new_stock_total = values.get("stock_total")
        if new_stock_total is not None and book.stock_available > new_stock_total:
            book.stock_available = new_stock_total
        for field, value in values.items():
            setattr(book, field, value)
        if author_ids is not None:
            self._set_author_models(session, book, author_ids)

        return self._flush_refresh_and_load(session, book)

    def delete(self, session: Session, id: int) -> bool:
        """Delete the book with *id*. Return True if deleted."""

        book = self.get_by_id(session, id)
        if book is None:
            return False

        session.delete(book)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Book cannot be deleted because it is in use.") from exc
        return True

    def set_authors(self, session: Session, book_id: int, author_ids: list[int]) -> None:
        """Replace the book's author associations with the given *author_ids*."""

        book = self.get_by_id(session, book_id)
        if book is None:
            raise NotFoundError("Book not found.")
        self._set_author_models(session, book, author_ids)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Book violates database constraints.") from exc

    def _with_relationships(self):
        """Build the default query shape for API serialization."""

        return select(Book).options(selectinload(Book.authors), selectinload(Book.category))

    def _set_author_models(self, session: Session, book: Book, author_ids: list[int]) -> None:
        """Load and assign author models, rejecting missing identifiers."""

        unique_ids = list(dict.fromkeys(author_ids))
        if not unique_ids:
            book.authors = []
            return

        authors = list(session.scalars(select(Author).where(Author.id.in_(unique_ids))).all())
        authors_by_id = {author.id: author for author in authors}
        if len(authors_by_id) != len(unique_ids):
            raise ConflictError("One or more authors do not exist.")
        book.authors = [authors_by_id[author_id] for author_id in unique_ids]

    def _flush_refresh_and_load(self, session: Session, book: Book) -> Book:
        """Flush changes, translate constraint failures, and load response relationships."""

        try:
            session.flush()
            session.refresh(book)
        except IntegrityError as exc:
            raise ConflictError("Book violates database constraints.") from exc
        return self.get_with_authors(session, book.id) or book


book_repository = SqlAlchemyBookRepository()


__all__ = ["SqlAlchemyBookRepository", "book_repository"]
