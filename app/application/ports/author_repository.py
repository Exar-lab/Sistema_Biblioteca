"""AuthorRepository outbound port."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AuthorRepository(Protocol):
    """Contract for author persistence."""

    def get_by_id(self, session: Any, id: int) -> Any | None:
        """Return the author with *id*, or None if it does not exist."""
        ...

    def list_all(self, session: Any) -> list[Any]:
        """Return all authors."""
        ...

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new author and return the created instance."""
        ...

    def update(self, session: Any, id: int, data: Any) -> Any | None:
        """Update the author with *id*, or return None if it does not exist."""
        ...

    def delete(self, session: Any, id: int) -> bool:
        """Delete the author with *id*. Return True if deleted, False if not found."""
        ...
