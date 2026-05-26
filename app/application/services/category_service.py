"""Application service for category workflows."""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.category_repository import CategoryRepository
from app.schemas.catalog.categories import CategoryCreate, CategoryUpdate


class CategoryService:
    """Coordinate category use cases without depending on FastAPI or SQLAlchemy."""

    def __init__(self, repository: CategoryRepository) -> None:
        self._repository = repository

    def list_categories(self, session: Any) -> list[Any]:
        """Return all categories."""

        return self._repository.list_all(session)

    def get_category(self, session: Any, category_id: int) -> Any:
        """Return a category or raise when it does not exist."""

        category = self._repository.get_by_id(session, category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        return category

    def create_category(self, session: Any, data: CategoryCreate) -> Any:
        """Create a category."""

        return self._repository.create(session, data)

    def update_category(self, session: Any, category_id: int, data: CategoryUpdate) -> Any:
        """Update a category or raise when it does not exist."""

        category = self._repository.update(session, category_id, data)
        if category is None:
            raise NotFoundError("Category not found.")
        return category

    def delete_category(self, session: Any, category_id: int) -> None:
        """Delete a category or raise when it does not exist."""

        deleted = self._repository.delete(session, category_id)
        if deleted is False:
            raise NotFoundError("Category not found.")


__all__ = ["CategoryService"]
