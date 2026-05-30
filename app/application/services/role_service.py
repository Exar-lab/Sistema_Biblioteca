"""Application service for role workflows."""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.role_repository import RoleRepository
from app.schemas.roles import RoleCreate, RoleUpdate


class RoleService:
    """Coordinate role use cases without depending on FastAPI or SQLAlchemy."""

    def __init__(self, repository: RoleRepository) -> None:
        self._repository = repository

    def list_roles(self, session: Any) -> list[Any]:
        """Return all roles."""

        return self._repository.list_all(session)

    def get_role(self, session: Any, role_id: int) -> Any:
        """Return a role or raise when it does not exist."""

        role = self._repository.get_by_id(session, role_id)
        if role is None:
            raise NotFoundError("Role not found.")
        return role

    def create_role(self, session: Any, data: RoleCreate) -> Any:
        """Create a role."""

        return self._repository.create(session, data)

    def update_role(self, session: Any, role_id: int, data: RoleUpdate) -> Any:
        """Update a role or raise when it does not exist."""

        role = self._repository.update(session, role_id, data)
        if role is None:
            raise NotFoundError("Role not found.")
        return role

    def delete_role(self, session: Any, role_id: int) -> None:
        """Delete a role or raise when it does not exist."""

        deleted = self._repository.delete(session, role_id)
        if deleted is False:
            raise NotFoundError("Role not found.")


__all__ = ["RoleService"]
