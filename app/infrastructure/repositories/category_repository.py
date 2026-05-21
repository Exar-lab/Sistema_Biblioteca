"""SQLAlchemy adapter for category persistence."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.errors import ConflictError
from app.domain.models.category import Category
from app.schemas.catalog.categories import CategoryCreate, CategoryUpdate


class SqlAlchemyCategoryRepository:
    """Persist categories using SQLAlchemy ORM models."""

    def get_by_id(self, session: Session, id: int) -> Category | None:
        """Return the category with *id*, or None if it does not exist."""

        return session.get(Category, id)

    def list_all(self, session: Session) -> list[Category]:
        """Return categories ordered by name for stable API responses."""

        return list(session.scalars(select(Category).order_by(Category.name)).all())

    def create(self, session: Session, data: CategoryCreate) -> Category:
        """Persist a new category and return the created instance."""

        category = Category(**data.model_dump())
        session.add(category)
        return self._flush_and_refresh(session, category)

    def update(self, session: Session, id: int, data: CategoryUpdate) -> Category | None:
        """Update the category with *id* and return it, or None if missing."""

        category = self.get_by_id(session, id)
        if category is None:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)

        return self._flush_and_refresh(session, category)

    def delete(self, session: Session, id: int) -> bool:
        """Delete the category with *id*. Return True if deleted."""

        category = self.get_by_id(session, id)
        if category is None:
            return False

        session.delete(category)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Category cannot be deleted because it is in use.") from exc
        return True

    def _flush_and_refresh(self, session: Session, category: Category) -> Category:
        """Flush changes and translate uniqueness failures to domain conflicts."""

        try:
            session.flush()
            session.refresh(category)
        except IntegrityError as exc:
            raise ConflictError("Category name already exists.") from exc
        return category


category_repository = SqlAlchemyCategoryRepository()


__all__ = ["SqlAlchemyCategoryRepository", "category_repository"]
