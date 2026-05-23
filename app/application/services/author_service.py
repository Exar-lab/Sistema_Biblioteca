"""Application service for author workflows."""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.author_repository import AuthorRepository
from app.schemas.catalog.authors import AuthorCreate, AuthorUpdate


class AuthorService:
    """Coordinate author use cases without depending on FastAPI or SQLAlchemy."""

    def __init__(self, repository: AuthorRepository) -> None:
        self._repository = repository

    def list_authors(self, session: Any) -> list[Any]:
        """Return all authors."""

        return self._repository.list_all(session)

    def get_author(self, session: Any, author_id: int) -> Any:
        """Return an author or raise when it does not exist."""

        author = self._repository.get_by_id(session, author_id)
        if author is None:
            raise NotFoundError("Author not found.")
        return author

    def create_author(self, session: Any, data: AuthorCreate) -> Any:
        """Create an author."""

        return self._repository.create(session, data)

    def update_author(self, session: Any, author_id: int, data: AuthorUpdate) -> Any:
        """Update an author or raise when it does not exist."""

        author = self._repository.update(session, author_id, data)
        if author is None:
            raise NotFoundError("Author not found.")
        return author

    def delete_author(self, session: Any, author_id: int) -> None:
        """Delete an author or raise when it does not exist."""

        deleted = self._repository.delete(session, author_id)
        if deleted is False:
            raise NotFoundError("Author not found.")


__all__ = ["AuthorService"]
