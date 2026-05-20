"""SQLAlchemy adapter for AuthorRepository port."""

from app.domain.models.author import Author
from app.infrastructure.repositories.base import SqlRepositoryBase


class AuthorRepositorySql(SqlRepositoryBase[Author]):
    """Concrete repository for BIBLIOTECA.authors.

    Structurally satisfies the ``AuthorRepository`` typing.Protocol.
    """

    model = Author
