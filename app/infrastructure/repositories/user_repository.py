"""SQLAlchemy adapter for UserRepository port."""

from app.domain.models.user import LibraryUser
from app.infrastructure.repositories.base import SqlRepositoryBase


class UserRepositorySql(SqlRepositoryBase[LibraryUser]):
    """Concrete repository for BIBLIOTECA.library_users.

    Structurally satisfies the ``UserRepository`` typing.Protocol.
    """

    model = LibraryUser
