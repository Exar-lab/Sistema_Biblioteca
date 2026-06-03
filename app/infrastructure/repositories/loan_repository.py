"""OracleLoanRepository — writes via pkg_loans stored procedures, reads via ORM."""

from typing import Any

import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.application.errors import OutOfStockError
from app.domain.models.loan import Loan
from app.application.ports.loan_repository import LoanRepository as LoanRepositoryPort


class LoanRepository:
    """Concrete implementation of LoanRepositoryPort backed by Oracle.

    Writes delegate exclusively to BIBLIOTECA.pkg_loans stored procedures.
    Reads use SQLAlchemy ORM SELECT. No session.commit() or session.rollback().

    p_insert hardcodes status='ACTIVE' internally and takes no stock params —
    the Oracle trigger trg_loans_decrement_stock owns stock decrement.
    """

    def get_by_id(self, session: Session, id: int) -> Loan | None:
        """Return the Loan with *id*, or None."""
        return session.execute(select(Loan).where(Loan.id == id)).scalar_one_or_none()

    def list_all(self, session: Session) -> list[Loan]:
        """Return all loans."""
        return list(session.execute(select(Loan)).scalars().all())

    def get_by_user(self, session: Session, user_id: int) -> list[Loan]:
        """Return all loans for the given *user_id*."""
        return list(
            session.execute(select(Loan).where(Loan.user_id == user_id)).scalars().all()
        )

    def get_by_book(self, session: Session, book_id: int) -> list[Loan]:
        """Return all loans for the given *book_id*."""
        return list(
            session.execute(select(Loan).where(Loan.book_id == book_id)).scalars().all()
        )

    def create(self, session: Session, data: Any) -> Loan:
        """Insert a loan via pkg_loans.p_insert (OUT param) and return the new instance.

        Raises OutOfStockError if the Oracle trigger fires ORA-20001 (no stock).
        """
        try:
            with session.connection().connection.cursor() as cur:
                out_id = cur.var(int)
                cur.callproc(
                    "BIBLIOTECA.pkg_loans.p_insert",
                    [
                        data.user_id,
                        data.book_id,
                        data.loan_date,
                        data.due_date,
                        out_id,
                    ],
                )
                new_id = out_id.getvalue()
        except Exception as exc:
            if self._is_out_of_stock_error(exc):
                raise OutOfStockError("Book has no available stock for loan.") from exc
            raise
        session.expire_all()
        return self.get_by_id(session, new_id)

    def update(self, session: Session, id: int, data: Any) -> Loan:
        """Update a loan via pkg_loans.p_update and return the refreshed instance."""
        current = self.get_by_id(session, id)

        session.execute(
            text(
                "BEGIN BIBLIOTECA.pkg_loans.p_update("
                ":p_id, :p_user_id, :p_book_id, :p_loan_date, :p_due_date,"
                " :p_return_date, :p_status); END;"
            ),
            {
                "p_id": id,
                "p_user_id": self._value(data, current, "user_id"),
                "p_book_id": self._value(data, current, "book_id"),
                "p_loan_date": self._value(data, current, "loan_date"),
                "p_due_date": self._value(data, current, "due_date"),
                "p_return_date": self._value(data, current, "return_date"),
                "p_status": self._value(data, current, "status", "ACTIVE"),
            },
        )
        session.expire_all()
        return self.get_by_id(session, id)

    def _value(self, data: Any, current: Loan | None, field: str, default: Any = None) -> Any:
        """Return update payload value, falling back to the current row when omitted."""

        fields_set = getattr(data, "model_fields_set", getattr(data, "__fields_set__", None))
        if hasattr(data, field) and (fields_set is None or field in fields_set):
            return getattr(data, field)
        if current is not None:
            return getattr(current, field)
        return default

    def _is_out_of_stock_error(self, exc: Exception) -> bool:
        """Detect the Oracle stock trigger error through wrapped DBAPI messages."""

        message = str(exc).lower()
        original = getattr(exc, "orig", None)
        if original is not None:
            message = f"{message} {original}".lower()
        return "ora-20001" in message or "no available stock" in message

    def delete(self, session: Session, id: int) -> bool:
        """Delete a loan via pkg_loans.p_delete. Returns True if a row was removed."""
        with session.connection().connection.cursor() as cur:
            out_deleted = cur.var(int)
            cur.callproc("BIBLIOTECA.pkg_loans.p_delete", [id, out_deleted])
            return bool(out_deleted.getvalue() == 1)

    def has_overdue_loans(self, session: Session, user_id: int) -> bool:
        """Return True if the user has any ACTIVE loans past their due date."""
        today = datetime.date.today()
        result = session.execute(
            select(Loan).where(
                Loan.user_id == user_id,
                Loan.status == "ACTIVE",
                Loan.due_date < today,
            )
        ).first()
        return result is not None

    def cancel(self, session: Session, loan_id: int) -> bool:
        """Cancel the loan via pkg_loans.p_cancel. Returns True if cancelled.

        Returns False if the loan was not found (p_cancelled == 0).
        Raises DatabaseError (ORA-20002) if the loan is already RETURNED or CANCELLED.
        """
        with session.connection().connection.cursor() as cur:
            out_cancelled = cur.var(int)
            cur.callproc("BIBLIOTECA.pkg_loans.p_cancel", [loan_id, out_cancelled])
            return bool(out_cancelled.getvalue() == 1)


SqlAlchemyLoanRepository = LoanRepository

loan_repository = LoanRepository()


__all__ = ["LoanRepository", "SqlAlchemyLoanRepository", "loan_repository"]
