"""RoleRepository outbound port."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RoleRepository(Protocol):
    """Contract for role persistence.

    No SQLAlchemy, Oracle, or infrastructure imports — structural typing only.
    """

    def get_by_id(self, session: Any, id: int) -> Any | None:
        """Return the role with *id*, or None if it does not exist."""
        ...

    def list_all(self, session: Any) -> list[Any]:
        """Return all roles."""
        ...

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new role and return the created instance."""
        ...

    def update(self, session: Any, id: int, data: Any) -> Any | None:
        """Update the role with *id*, or return None if it does not exist."""
        ...

    def delete(self, session: Any, id: int) -> bool:
        """Delete the role with *id*. Return True if deleted, False if not found."""
        ...
