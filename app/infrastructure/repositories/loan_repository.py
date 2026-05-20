"""SQLAlchemy adapter for LoanRepository port.

Traps Oracle trigger error ORA-20001 (out-of-stock) and re-raises it as
the domain-level ``OutOfStockError`` so no infrastructure exception ever
leaks past the adapter boundary.
"""

from typing import Any

from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.application.errors import OutOfStockError
from app.domain.models.loan import Loan
from app.infrastructure.repositories.base import SqlRepositoryBase

# Oracle user-defined error code raised by the BEFORE INSERT trigger on loans
_ORA_OUT_OF_STOCK = 20001


class LoanRepositorySql(SqlRepositoryBase[Loan]):
    """Concrete repository for BIBLIOTECA.loans.

    Structurally satisfies the ``LoanRepository`` typing.Protocol.
    """

    model = Loan

    # ------------------------------------------------------------------
    # Additional query methods
    # ------------------------------------------------------------------

    def get_by_user(self, session: Session, user_id: int) -> list[Loan]:
        """Return all loans for the given *user_id*."""
        return (
            session.query(Loan)
            .filter(Loan.user_id == user_id)
            .order_by(Loan.id)
            .all()
        )

    def get_by_book(self, session: Session, book_id: int) -> list[Loan]:
        """Return all loans for the given *book_id*."""
        return (
            session.query(Loan)
            .filter(Loan.book_id == book_id)
            .order_by(Loan.id)
            .all()
        )

    # ------------------------------------------------------------------
    # Override create — translate Oracle -20001 → OutOfStockError
    # ------------------------------------------------------------------

    def create(self, session: Session, data: Any) -> Loan:
        """Persist a new loan row.

        Raises:
            OutOfStockError: when Oracle fires ORA-20001 (no available stock).
        """
        try:
            return super().create(session, data)
        except DBAPIError as exc:
            if _is_out_of_stock_error(exc):
                raise OutOfStockError() from exc
            raise

    # ------------------------------------------------------------------
    # Override delete — flush needs care; keep it consistent with base
    # ------------------------------------------------------------------


def _is_out_of_stock_error(exc: DBAPIError) -> bool:
    """Return True if *exc* represents Oracle ORA-20001.

    Tries the structured ``orig.args[0].code`` attribute first (cx_Oracle /
    python-oracledb), then falls back to parsing the string representation.
    """
    orig = getattr(exc, "orig", None)
    if orig is None:
        return False

    # python-oracledb / cx_Oracle: orig is an ``oracledb.Error`` instance.
    # The first element of its args is an ``_Error`` object with a ``.code``.
    try:
        if orig.args and orig.args[0].code == _ORA_OUT_OF_STOCK:
            return True
    except AttributeError:
        pass

    # Fallback: string inspection
    return f"ORA-{_ORA_OUT_OF_STOCK:05d}" in str(orig)
