"""OracleRoleRepository — writes via pkg_roles stored procedures, reads via ORM."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.role import Role
from app.application.ports.role_repository import RoleRepository as RoleRepositoryPort


class RoleRepository:
    """Concrete implementation of RoleRepositoryPort backed by Oracle.

    Writes delegate exclusively to BIBLIOTECA.pkg_roles stored procedures.
    Reads use SQLAlchemy ORM SELECT. No session.commit() or session.rollback()
    here — the caller (get_db dependency) owns transaction boundaries.
    """

    def get_by_id(self, session: Session, id: int) -> Role | None:
        """Return the Role with *id*, or None."""
        return session.execute(select(Role).where(Role.id == id)).scalar_one_or_none()

    def list_all(self, session: Session) -> list[Role]:
        """Return all roles."""
        return list(session.execute(select(Role)).scalars().all())

    def create(self, session: Session, data: Any) -> Role:
        """Insert a role via pkg_roles.p_insert (OUT param) and return the new instance."""
        with session.connection().connection.cursor() as cur:
            out_id = cur.var(int)
            cur.callproc(
                "BIBLIOTECA.pkg_roles.p_insert",
                [data.name, data.description, out_id],
            )
            new_id = out_id.getvalue()
        session.expire_all()
        return self.get_by_id(session, new_id)

    def update(self, session: Session, id: int, data: Any) -> Role:
        """Update a role via pkg_roles.p_update and return the refreshed instance."""
        from sqlalchemy import text

        session.execute(
            text("BEGIN BIBLIOTECA.pkg_roles.p_update(:p_id, :p_name, :p_description); END;"),
            {"p_id": id, "p_name": data.name, "p_description": data.description},
        )
        session.expire_all()
        return self.get_by_id(session, id)

    def delete(self, session: Session, id: int) -> bool:
        """Delete a role via pkg_roles.p_delete. Returns True if a row was removed."""
        with session.connection().connection.cursor() as cur:
            out_deleted = cur.var(int)
            cur.callproc("BIBLIOTECA.pkg_roles.p_delete", [id, out_deleted])
            return bool(out_deleted.getvalue() == 1)
