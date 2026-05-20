"""Application service for categories.

Thin orchestration layer — no SQLAlchemy or infrastructure imports.
"""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.category_repository import CategoryRepository


class CategoryService:
    """Orchestrates category operations through the CategoryRepository port."""

    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session: Any, id: int) -> Any:
        """Return the category with *id*.

        Raises:
            NotFoundError: if no category with that ID exists.
        """
        category = self._repo.get_by_id(session, id)
        if category is None:
            raise NotFoundError(f"Category {id} not found.")
        return category

    def list(self, session: Any) -> list[Any]:
        """Return all categories."""
        return self._repo.list_all(session)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new category and return it."""
        return self._repo.create(session, data)

    def update(self, session: Any, id: int, data: Any) -> Any:
        """Update an existing category and return the updated instance.

        Raises:
            NotFoundError: if no category with that ID exists.
        """
        updated = self._repo.update(session, id, data)
        if updated is None:
            raise NotFoundError(f"Category {id} not found.")
        return updated

    def delete(self, session: Any, id: int) -> None:
        """Delete the category with *id*.

        Raises:
            NotFoundError: if no category with that ID exists.
        """
        deleted = self._repo.delete(session, id)
        if not deleted:
            raise NotFoundError(f"Category {id} not found.")
