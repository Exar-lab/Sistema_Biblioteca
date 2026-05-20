"""SQLAlchemy adapter for RoleRepository port."""

from app.domain.models.role import Role
from app.infrastructure.repositories.base import SqlRepositoryBase


class RoleRepositorySql(SqlRepositoryBase[Role]):
    """Concrete repository for BIBLIOTECA.roles.

    Structurally satisfies the ``RoleRepository`` typing.Protocol.
    """

    model = Role
