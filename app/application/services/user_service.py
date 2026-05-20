"""Application service for library users.

Thin orchestration layer — no SQLAlchemy or infrastructure imports.
"""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.user_repository import UserRepository


class UserService:
    """Orchestrates library-user operations through the UserRepository port."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session: Any, id: int) -> Any:
        """Return the user with *id*.

        Raises:
            NotFoundError: if no user with that ID exists.
        """
        user = self._repo.get_by_id(session, id)
        if user is None:
            raise NotFoundError(f"User {id} not found.")
        return user

    def list(self, session: Any) -> list[Any]:
        """Return all users."""
        return self._repo.list_all(session)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new user and return it."""
        return self._repo.create(session, data)

    def update(self, session: Any, id: int, data: Any) -> Any:
        """Update an existing user and return the updated instance.

        Raises:
            NotFoundError: if no user with that ID exists.
        """
        updated = self._repo.update(session, id, data)
        if updated is None:
            raise NotFoundError(f"User {id} not found.")
        return updated

    def delete(self, session: Any, id: int) -> None:
        """Delete the user with *id*.

        Raises:
            NotFoundError: if no user with that ID exists.
        """
        deleted = self._repo.delete(session, id)
        if not deleted:
            raise NotFoundError(f"User {id} not found.")
