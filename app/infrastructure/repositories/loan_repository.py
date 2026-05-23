"""SQLAlchemy adapter for loan persistence."""

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.application.errors import ConflictError, OutOfStockError
from app.domain.models.loan import Loan
from app.schemas.circulation.loans import LoanCreate, LoanUpdate


class SqlAlchemyLoanRepository:
    """Persist loans and translate Oracle-owned stock failures."""

    def get_by_id(self, session: Session, id: int) -> Loan | None:
        """Return the loan with *id*, or None if it does not exist."""

        return session.scalar(self._with_relationships().where(Loan.id == id))

    def list_all(self, session: Session) -> list[Loan]:
        """Return loans ordered by newest first."""

        return list(session.scalars(self._with_relationships().order_by(Loan.id.desc())).all())

    def create(self, session: Session, data: LoanCreate) -> Loan:
        """Persist a new loan and return it with relationships loaded."""

        loan = Loan(**data.model_dump())
        session.add(loan)
        return self._flush_refresh_and_load(session, loan)

    def update(self, session: Session, id: int, data: LoanUpdate) -> Loan | None:
        """Update the loan with *id*, or return None if missing."""

        loan = self.get_by_id(session, id)
        if loan is None:
            return None
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(loan, field, value)
        return self._flush_refresh_and_load(session, loan)

    def delete(self, session: Session, id: int) -> bool:
        """Delete the loan with *id*. Return True if deleted."""

        loan = self.get_by_id(session, id)
        if loan is None:
            return False
        session.delete(loan)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Loan cannot be deleted because it is in use.") from exc
        return True

    def get_by_user(self, session: Session, user_id: int) -> list[Loan]:
        """Return all loans for the given *user_id*."""

        return list(session.scalars(self._with_relationships().where(Loan.user_id == user_id).order_by(Loan.id.desc())).all())

    def get_by_book(self, session: Session, book_id: int) -> list[Loan]:
        """Return all loans for the given *book_id*."""

        return list(session.scalars(self._with_relationships().where(Loan.book_id == book_id).order_by(Loan.id.desc())).all())

    def has_overdue_loans(self, session: Session, user_id: int) -> bool:
        """Return whether the user has active loans past their due date."""

        statement = select(Loan.id).where(Loan.user_id == user_id, Loan.status == "ACTIVE", Loan.due_date < date.today())
        return session.scalar(statement) is not None

    def _with_relationships(self) -> Any:
        """Build the default query shape for API serialization."""

        return select(Loan).options(selectinload(Loan.user), selectinload(Loan.book))

    def _flush_refresh_and_load(self, session: Session, loan: Loan) -> Loan:
        """Flush changes, translate Oracle trigger failures, and reload relationships."""

        try:
            session.flush()
            session.refresh(loan)
        except DBAPIError as exc:
            if self._is_out_of_stock_error(exc):
                raise OutOfStockError("Book has no available stock for loan.") from exc
            raise ConflictError("Loan violates database constraints.") from exc
        return self.get_by_id(session, loan.id) or loan

    def _is_out_of_stock_error(self, exc: DBAPIError) -> bool:
        """Detect the Oracle stock trigger error through wrapped DBAPI messages."""

        message = str(exc).lower()
        original = getattr(exc, "orig", None)
        if original is not None:
            message = f"{message} {original}".lower()
        return "ora-20001" in message or "no available stock" in message


loan_repository = SqlAlchemyLoanRepository()


__all__ = ["SqlAlchemyLoanRepository", "loan_repository"]
