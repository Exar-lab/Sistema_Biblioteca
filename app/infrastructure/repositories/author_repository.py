"""OracleAuthorRepository — writes via pkg_authors stored procedures, reads via ORM."""

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.domain.models.author import Author
from app.application.ports.author_repository import AuthorRepository as AuthorRepositoryPort


class AuthorRepository:
    """Concrete implementation of AuthorRepositoryPort backed by Oracle.

    Writes delegate exclusively to BIBLIOTECA.pkg_authors stored procedures.
    Reads use SQLAlchemy ORM SELECT. No session.commit() or session.rollback().
    """

    def get_by_id(self, session: Session, id: int) -> Author | None:
        """Return the Author with *id*, or None."""
        return session.execute(select(Author).where(Author.id == id)).scalar_one_or_none()

    def list_all(self, session: Session) -> list[Author]:
        """Return all authors."""
        return list(session.execute(select(Author)).scalars().all())

    def create(self, session: Session, data: Any) -> Author:
        """Insert an author via pkg_authors.p_insert (OUT param) and return the new instance."""
        with session.connection().connection.cursor() as cur:
            out_id = cur.var(int)
            cur.callproc(
                "BIBLIOTECA.pkg_authors.p_insert",
                [
                    data.first_name,
                    data.last_name,
                    data.biography,
                    data.birth_date,
                    data.death_date,
                    data.is_active,
                    out_id,
                ],
            )
            new_id = out_id.getvalue()
        session.expire_all()
        return self.get_by_id(session, new_id)

    def update(self, session: Session, id: int, data: Any) -> Author:
        """Update an author via pkg_authors.p_update and return the refreshed instance."""
        session.execute(
            text(
                "BEGIN BIBLIOTECA.pkg_authors.p_update("
                ":p_id, :p_first_name, :p_last_name, :p_biography,"
                " :p_birth_date, :p_death_date, :p_is_active); END;"
            ),
            {
                "p_id": id,
                "p_first_name": data.first_name,
                "p_last_name": data.last_name,
                "p_biography": data.biography,
                "p_birth_date": data.birth_date,
                "p_death_date": data.death_date,
                "p_is_active": data.is_active,
            },
        )
        session.expire_all()
        return self.get_by_id(session, id)

    def delete(self, session: Session, id: int) -> bool:
        """Delete an author via pkg_authors.p_delete. Returns True if a row was removed."""
        with session.connection().connection.cursor() as cur:
            out_deleted = cur.var(int)
            cur.callproc("BIBLIOTECA.pkg_authors.p_delete", [id, out_deleted])
            return bool(out_deleted.getvalue() == 1)


author_repository = AuthorRepository()


__all__ = ["AuthorRepository", "author_repository"]
