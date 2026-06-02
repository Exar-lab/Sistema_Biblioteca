"""OracleReturnRepository — create via pkg_returns.p_process, reads via ORM."""

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.domain.models.return_ import Return_
from app.application.ports.return_repository import ReturnRepository as ReturnRepositoryPort


class ReturnRepository:
    """Concrete implementation of ReturnRepositoryPort backed by Oracle.

    create() calls pkg_returns.p_process (thin INSERT; Oracle trigger
    trg_returns_restore_stock owns loan status update and stock restoration).
    Reads use SQLAlchemy ORM SELECT. No session.commit() or session.rollback().
    """

    def get_by_id(self, session: Session, id: int) -> Return_ | None:
        """Return the Return_ record with *id*, or None."""
        return session.execute(select(Return_).where(Return_.id == id)).scalar_one_or_none()

    def list_all(self, session: Session) -> list[Return_]:
        """Return all return records."""
        return list(session.execute(select(Return_)).scalars().all())

    def create(self, session: Session, data: Any) -> Return_:
        """Insert a return record via pkg_returns.p_process (OUT id) and return the new instance.

        The Oracle trigger trg_returns_restore_stock fires after INSERT and updates
        the loan's status to RETURNED and restores book stock. session.expire_all()
        ensures subsequent reads see the trigger-updated state.
        """
        with session.connection().connection.cursor() as cur:
            out_id = cur.var(int)
            cur.callproc(
                "BIBLIOTECA.pkg_returns.p_process",
                [
                    data.loan_id,
                    data.return_date,
                    data.fine_amount,
                    data.notes,
                    out_id,
                ],
            )
            new_id = out_id.getvalue()
        session.expire_all()
        return self.get_by_id(session, new_id)

    def update(self, session: Session, id: int, data: Any) -> Return_:
        """Update a return record via pkg_returns.p_update and return the refreshed instance."""
        session.execute(
            text(
                "BEGIN BIBLIOTECA.pkg_returns.p_update("
                ":p_id, :p_loan_id, :p_return_date, :p_fine_amount, :p_notes); END;"
            ),
            {
                "p_id": id,
                "p_loan_id": data.loan_id,
                "p_return_date": data.return_date,
                "p_fine_amount": data.fine_amount,
                "p_notes": data.notes,
            },
        )
        session.expire_all()
        return self.get_by_id(session, id)

    def delete(self, session: Session, id: int) -> bool:
        """Delete a return record via pkg_returns.p_delete. Returns True if a row was removed."""
        with session.connection().connection.cursor() as cur:
            out_deleted = cur.var(int)
            cur.callproc("BIBLIOTECA.pkg_returns.p_delete", [id, out_deleted])
            return bool(out_deleted.getvalue() == 1)
