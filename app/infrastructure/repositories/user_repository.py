"""OracleUserRepository — writes via pkg_library_users stored procedures, reads via ORM."""

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.domain.models.user import LibraryUser
from app.application.ports.user_repository import UserRepository as UserRepositoryPort


class UserRepository:
    """Concrete implementation of UserRepositoryPort backed by Oracle.

    Writes delegate exclusively to BIBLIOTECA.pkg_library_users stored procedures.
    Reads use SQLAlchemy ORM SELECT. No session.commit() or session.rollback().
    """

    def get_by_id(self, session: Session, id: int) -> LibraryUser | None:
        """Return the LibraryUser with *id*, or None."""
        return session.execute(select(LibraryUser).where(LibraryUser.id == id)).scalar_one_or_none()

    def list_all(self, session: Session) -> list[LibraryUser]:
        """Return all library users."""
        return list(session.execute(select(LibraryUser)).scalars().all())

    def create(self, session: Session, data: Any) -> LibraryUser:
        """Insert a user via pkg_library_users.p_insert (OUT param) and return the new instance."""
        with session.connection().connection.cursor() as cur:
            out_id = cur.var(int)
            cur.callproc(
                "BIBLIOTECA.pkg_library_users.p_insert",
                [
                    data.username,
                    data.full_name,
                    data.email,
                    data.phone,
                    data.password_hash,
                    data.is_active,
                    data.role_id,
                    out_id,
                ],
            )
            new_id = out_id.getvalue()
        session.expire_all()
        return self.get_by_id(session, new_id)

    def update(self, session: Session, id: int, data: Any) -> LibraryUser:
        """Update a user via pkg_library_users.p_update and return the refreshed instance."""
        session.execute(
            text(
                "BEGIN BIBLIOTECA.pkg_library_users.p_update("
                ":p_id, :p_username, :p_full_name, :p_email,"
                " :p_phone, :p_password_hash, :p_is_active, :p_role_id); END;"
            ),
            {
                "p_id": id,
                "p_username": data.username,
                "p_full_name": data.full_name,
                "p_email": data.email,
                "p_phone": data.phone,
                "p_password_hash": data.password_hash,
                "p_is_active": data.is_active,
                "p_role_id": data.role_id,
            },
        )
        session.expire_all()
        return self.get_by_id(session, id)

    def delete(self, session: Session, id: int) -> bool:
        """Delete a user via pkg_library_users.p_delete. Returns True if a row was removed."""
        with session.connection().connection.cursor() as cur:
            out_deleted = cur.var(int)
            cur.callproc("BIBLIOTECA.pkg_library_users.p_delete", [id, out_deleted])
            return bool(out_deleted.getvalue() == 1)
