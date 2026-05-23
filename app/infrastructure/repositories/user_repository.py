"""Minimal read-only user adapter used by the circulation layer.

This module only provides the lookup needed to validate borrowers.
Full user management (create, update, delete, password hashing) belongs
to the dedicated users slice.
"""

from sqlalchemy.orm import Session

from app.domain.models.user import LibraryUser


class SqlAlchemyUserRepository:
    """Read library users for borrower validation."""

    def get_by_id(self, session: Session, id: int) -> LibraryUser | None:
        """Return the user with *id*, or None if it does not exist."""

        return session.get(LibraryUser, id)


user_repository = SqlAlchemyUserRepository()


__all__ = ["SqlAlchemyUserRepository", "user_repository"]
