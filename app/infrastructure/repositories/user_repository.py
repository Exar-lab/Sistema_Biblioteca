"""SQLAlchemy adapter for minimal library-user persistence needed by circulation."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.user import LibraryUser


class SqlAlchemyUserRepository:
    """Persist library users using SQLAlchemy ORM models."""

    def get_by_id(self, session: Session, id: int) -> LibraryUser | None:
        """Return the user with *id*, or None if it does not exist."""

        return session.get(LibraryUser, id)

    def list_all(self, session: Session) -> list[LibraryUser]:
        """Return users ordered by username for stable API responses."""

        return list(session.scalars(select(LibraryUser).order_by(LibraryUser.username)).all())

    def create(self, session: Session, data: Any) -> LibraryUser:
        """Persist a new user and return it."""

        values = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        user = LibraryUser(**values)
        session.add(user)
        session.flush()
        session.refresh(user)
        return user

    def update(self, session: Session, id: int, data: Any) -> LibraryUser | None:
        """Update a user, or return None if missing."""

        user = self.get_by_id(session, id)
        if user is None:
            return None
        values = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else dict(data)
        for field, value in values.items():
            setattr(user, field, value)
        session.flush()
        session.refresh(user)
        return user

    def delete(self, session: Session, id: int) -> bool:
        """Delete a user. Return True if deleted, False if not found."""

        user = self.get_by_id(session, id)
        if user is None:
            return False
        session.delete(user)
        session.flush()
        return True


user_repository = SqlAlchemyUserRepository()


__all__ = ["SqlAlchemyUserRepository", "user_repository"]
