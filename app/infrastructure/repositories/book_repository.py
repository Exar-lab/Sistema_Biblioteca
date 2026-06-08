"""OracleBookRepository — writes via pkg_books stored procedures, reads via ORM."""

from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from app.domain.models.author import Author
from app.domain.models.book import Book
from app.domain.models.category import Category
from app.application.ports.book_repository import BookRepository as BookRepositoryPort


class BookRepository:
    """Concrete implementation of BookRepositoryPort backed by Oracle.

    Writes delegate exclusively to BIBLIOTECA.pkg_books stored procedures.
    Reads use SQLAlchemy ORM SELECT. No session.commit() or session.rollback().
    """

    def get_by_id(self, session: Session, id: int) -> Book | None:
        """Return the Book with *id*, or None."""
        return session.execute(select(Book).where(Book.id == id)).scalar_one_or_none()

    def list_all(
        self,
        session: Session,
        *,
        title: str | None = None,
        author: str | None = None,
        category: str | None = None,
    ) -> list[Book]:
        """Return all books, optionally filtered by title, author, or category.

        Filtering uses UPPER(...) LIKE UPPER(:param) with %value% wrapping —
        Oracle-safe case-insensitive substring match (no ILIKE).
        Author filter joins through the book_authors association and uses
        .distinct() to prevent row duplication.
        """
        stmt = select(Book)

        if author is not None:
            stmt = stmt.join(Book.authors).where(
                func.upper(Author.first_name + " " + Author.last_name).like(
                    func.upper(f"%{author}%")
                )
            ).distinct()

        if category is not None:
            stmt = stmt.join(Book.category).where(
                func.upper(Category.name).like(func.upper(f"%{category}%"))
            )

        if title is not None:
            stmt = stmt.where(
                func.upper(Book.title).like(func.upper(f"%{title}%"))
            )

        return list(session.execute(stmt).scalars().all())

    def get_with_authors(self, session: Session, id: int) -> Book | None:
        """Return the Book with *id* with its authors eagerly loaded, or None."""
        return session.execute(
            select(Book).where(Book.id == id).options(selectinload(Book.authors))
        ).scalar_one_or_none()

    def create(self, session: Session, data: Any) -> Book:
        """Insert a book via pkg_books.p_insert (OUT param) and return the new instance."""
        with session.connection().connection.cursor() as cur:
            out_id = cur.var(int)
            cur.callproc(
                "BIBLIOTECA.pkg_books.p_insert",
                [
                    data.title,
                    data.isbn,
                    data.description,
                    data.publication_date,
                    data.publisher,
                    data.edition,
                    data.pages,
                    data.stock_total,
                    data.stock_total,  # stock_available starts equal to stock_total on creation
                    data.is_active,
                    data.category_id,
                    out_id,
                ],
            )
            new_id = out_id.getvalue()
        session.expire_all()
        return self.get_by_id(session, new_id)

    def update(self, session: Session, id: int, data: Any) -> Book:
        """Update a book via pkg_books.p_update and return the refreshed instance."""
        current = self.get_by_id(session, id)
        if current is None:
            return None

        values = data.model_dump(exclude_unset=True, exclude_none=True)
        stock_total = values.get("stock_total", current.stock_total)
        stock_available = min(current.stock_available, stock_total)
        session.execute(
            text(
                "BEGIN BIBLIOTECA.pkg_books.p_update("
                ":p_id, :p_title, :p_isbn, :p_description, :p_publication_date,"
                " :p_publisher, :p_edition, :p_pages, :p_stock_total,"
                " :p_stock_available, :p_is_active, :p_category_id); END;"
            ),
            {
                "p_id": id,
                "p_title": values.get("title", current.title),
                "p_isbn": values.get("isbn", current.isbn),
                "p_description": values.get("description", current.description),
                "p_publication_date": values.get("publication_date", current.publication_date),
                "p_publisher": values.get("publisher", current.publisher),
                "p_edition": values.get("edition", current.edition),
                "p_pages": values.get("pages", current.pages),
                "p_stock_total": stock_total,
                "p_stock_available": stock_available,
                "p_is_active": values.get("is_active", current.is_active),
                "p_category_id": values.get("category_id", current.category_id),
            },
        )
        session.expire_all()
        return self.get_by_id(session, id)

    def delete(self, session: Session, id: int) -> bool:
        """Delete a book via pkg_books.p_delete. Returns True if a row was removed."""
        with session.connection().connection.cursor() as cur:
            out_deleted = cur.var(int)
            cur.callproc("BIBLIOTECA.pkg_books.p_delete", [id, out_deleted])
            return bool(out_deleted.getvalue() == 1)

    def set_authors(self, session: Session, book_id: int, author_ids: list[int]) -> None:
        """Replace all author associations: clear existing, then add each id in order."""
        with session.connection().connection.cursor() as cur:
            cur.callproc("BIBLIOTECA.pkg_books.p_clear_authors", [book_id])
            for author_id in author_ids:
                cur.callproc("BIBLIOTECA.pkg_books.p_add_author", [book_id, author_id])
        session.expire_all()


book_repository = BookRepository()


__all__ = ["BookRepository", "book_repository"]
