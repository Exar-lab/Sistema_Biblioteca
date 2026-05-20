"""Application service for roles.

Thin orchestration layer: validates existence, delegates persistence to the
injected port, and translates missing-entity cases to domain errors.
No SQLAlchemy or infrastructure imports.
"""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.role_repository import RoleRepository


class RoleService:
    """Orchestrates role operations through the RoleRepository port."""

    def __init__(self, repo: RoleRepository) -> None:
        self._repo = repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session: Any, id: int) -> Any:
        """Return the role with *id*.

        Raises:
            NotFoundError: if no role with that ID exists.
        """
        role = self._repo.get_by_id(session, id)
        if role is None:
            raise NotFoundError(f"Role {id} not found.")
        return role

    def list(self, session: Any) -> list[Any]:
        """Return all roles."""
        return self._repo.list_all(session)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new role and return it."""
        return self._repo.create(session, data)

    def update(self, session: Any, id: int, data: Any) -> Any:
        """Update an existing role and return the updated instance.

        Raises:
            NotFoundError: if no role with that ID exists.
        """
        updated = self._repo.update(session, id, data)
        if updated is None:
            raise NotFoundError(f"Role {id} not found.")
        return updated

    def delete(self, session: Any, id: int) -> None:
        """Delete the role with *id*.

        Raises:
            NotFoundError: if no role with that ID exists.
        """
        deleted = self._repo.delete(session, id)
        if not deleted:
            raise NotFoundError(f"Role {id} not found.")
