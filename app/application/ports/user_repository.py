"""UserRepository outbound port."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class UserRepository(Protocol):
    """Contract for library-user persistence."""

    def get_by_id(self, session: Any, id: int) -> Any | None:
        """Return the user with *id*, or None if it does not exist."""
        ...

    def list_all(self, session: Any) -> list[Any]:
        """Return all users."""
        ...

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new user and return the created instance."""
        ...

    def update(self, session: Any, id: int, data: Any) -> Any | None:
        """Update the user with *id*, or return None if it does not exist."""
        ...

    def get_by_username(self, session: Any, username: str) -> Any | None:
        """Return the user with *username*, or None if it does not exist."""
        ...

    def delete(self, session: Any, id: int) -> bool:
        """Delete the user with *id*. Return True if deleted, False if not found."""
        ...
