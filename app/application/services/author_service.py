"""Application service for authors.

Thin orchestration layer — no SQLAlchemy or infrastructure imports.
"""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.author_repository import AuthorRepository


class AuthorService:
    """Orchestrates author operations through the AuthorRepository port."""

    def __init__(self, repo: AuthorRepository) -> None:
        self._repo = repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session: Any, id: int) -> Any:
        """Return the author with *id*.

        Raises:
            NotFoundError: if no author with that ID exists.
        """
        author = self._repo.get_by_id(session, id)
        if author is None:
            raise NotFoundError(f"Author {id} not found.")
        return author

    def list(self, session: Any) -> list[Any]:
        """Return all authors."""
        return self._repo.list_all(session)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new author and return it."""
        return self._repo.create(session, data)

    def update(self, session: Any, id: int, data: Any) -> Any:
        """Update an existing author and return the updated instance.

        Raises:
            NotFoundError: if no author with that ID exists.
        """
        updated = self._repo.update(session, id, data)
        if updated is None:
            raise NotFoundError(f"Author {id} not found.")
        return updated

    def delete(self, session: Any, id: int) -> None:
        """Delete the author with *id*.

        Raises:
            NotFoundError: if no author with that ID exists.
        """
        deleted = self._repo.delete(session, id)
        if not deleted:
            raise NotFoundError(f"Author {id} not found.")
