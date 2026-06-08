"""OracleCategoryRepository — writes via pkg_categories stored procedures, reads via ORM."""

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.domain.models.category import Category
from app.domain.models.types import bool_to_oracle_char
from app.application.ports.category_repository import CategoryRepository as CategoryRepositoryPort


class CategoryRepository:
    """Concrete implementation of CategoryRepositoryPort backed by Oracle.

    Writes delegate exclusively to BIBLIOTECA.pkg_categories stored procedures.
    Reads use SQLAlchemy ORM SELECT. No session.commit() or session.rollback().
    """

    def get_by_id(self, session: Session, id: int) -> Category | None:
        """Return the Category with *id*, or None."""
        return session.execute(select(Category).where(Category.id == id)).scalar_one_or_none()

    def list_all(self, session: Session) -> list[Category]:
        """Return all categories."""
        return list(session.execute(select(Category)).scalars().all())

    def create(self, session: Session, data: Any) -> Category:
        """Insert a category via pkg_categories.p_insert (OUT param) and return the new instance."""
        with session.connection().connection.cursor() as cur:
            out_id = cur.var(int)
            cur.callproc(
                "BIBLIOTECA.pkg_categories.p_insert",
                [data.name, data.description, bool_to_oracle_char(data.is_active), out_id],
            )
            new_id = out_id.getvalue()
        session.expire_all()
        return self.get_by_id(session, new_id)

    def update(self, session: Session, id: int, data: Any) -> Category:
        """Update a category via pkg_categories.p_update and return the refreshed instance."""
        session.execute(
            text(
                "BEGIN BIBLIOTECA.pkg_categories.p_update("
                ":p_id, :p_name, :p_description, :p_is_active); END;"
            ),
            {
                "p_id": id,
                "p_name": data.name,
                "p_description": data.description,
                "p_is_active": bool_to_oracle_char(data.is_active),
            },
        )
        session.expire_all()
        return self.get_by_id(session, id)

    def delete(self, session: Session, id: int) -> bool:
        """Delete a category via pkg_categories.p_delete. Returns True if a row was removed."""
        with session.connection().connection.cursor() as cur:
            out_deleted = cur.var(int)
            cur.callproc("BIBLIOTECA.pkg_categories.p_delete", [id, out_deleted])
            return bool(out_deleted.getvalue() == 1)


category_repository = CategoryRepository()


__all__ = ["CategoryRepository", "category_repository"]
