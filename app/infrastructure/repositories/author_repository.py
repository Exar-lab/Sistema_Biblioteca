"""SQLAlchemy adapter for author persistence."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.errors import ConflictError
from app.domain.models.author import Author
from app.schemas.catalog.authors import AuthorCreate, AuthorUpdate


class SqlAlchemyAuthorRepository:
    """Persist authors using SQLAlchemy ORM models."""

    def get_by_id(self, session: Session, id: int) -> Author | None:
        """Return the author with *id*, or None if it does not exist."""

        return session.get(Author, id)

    def list_all(self, session: Session) -> list[Author]:
        """Return authors ordered by last and first name for stable API responses."""

        return list(session.scalars(select(Author).order_by(Author.last_name, Author.first_name)).all())

    def create(self, session: Session, data: AuthorCreate) -> Author:
        """Persist a new author and return the created instance."""

        author = Author(**data.model_dump())
        session.add(author)
        return self._flush_and_refresh(session, author)

    def update(self, session: Session, id: int, data: AuthorUpdate) -> Author | None:
        """Update the author with *id* and return it, or None if missing."""

        author = self.get_by_id(session, id)
        if author is None:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(author, field, value)

        return self._flush_and_refresh(session, author)

    def delete(self, session: Session, id: int) -> bool:
        """Delete the author with *id*. Return True if deleted."""

        author = self.get_by_id(session, id)
        if author is None:
            return False

        session.delete(author)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Author cannot be deleted because it is in use.") from exc
        return True

    def _flush_and_refresh(self, session: Session, author: Author) -> Author:
        """Flush changes and translate database constraint failures to domain conflicts."""

        try:
            session.flush()
            session.refresh(author)
        except IntegrityError as exc:
            raise ConflictError("Author violates database constraints.") from exc
        return author


author_repository = SqlAlchemyAuthorRepository()


__all__ = ["SqlAlchemyAuthorRepository", "author_repository"]
