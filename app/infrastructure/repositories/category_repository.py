"""SQLAlchemy adapter for CategoryRepository port."""

from app.domain.models.category import Category
from app.infrastructure.repositories.base import SqlRepositoryBase


class CategoryRepositorySql(SqlRepositoryBase[Category]):
    """Concrete repository for BIBLIOTECA.categories.

    Structurally satisfies the ``CategoryRepository`` typing.Protocol.
    """

    model = Category
