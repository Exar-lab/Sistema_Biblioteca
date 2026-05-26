"""SQLAlchemy adapter for dashboard reports."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.domain.models.book import Book
from app.domain.models.loan import Loan
from app.domain.models.user import LibraryUser
from app.schemas.dashboard import (
    DashboardSummary,
    LowStockBookItem,
    MonthlyLoanItem,
    ReportsDashboard,
    TopBookItem,
    TopUserItem,
)

LOW_STOCK_THRESHOLD = 2
REPORT_LIMIT = 5


class SqlAlchemyReportRepository:
    """Build read-only aggregate reports from SQLAlchemy models."""

    def get_dashboard(self, session: Session) -> ReportsDashboard:
        """Return dashboard counters and top-N report lists."""

        return ReportsDashboard(
            summary=self._get_summary(session),
            top_books=self._get_top_books(session),
            loans_by_month=self._get_loans_by_month(session),
            top_users=self._get_top_users(session),
            low_stock_books=self._get_low_stock_books(session),
        )

    def _get_summary(self, session: Session) -> DashboardSummary:
        active_loans = self._count(session, select(func.count(Loan.id)).where(Loan.status == "ACTIVE"))
        low_stock_books = self._count(
            session,
            select(func.count(Book.id)).where(Book.stock_available <= LOW_STOCK_THRESHOLD),
        )
        return DashboardSummary(
            total_books=self._count(session, select(func.count(Book.id))),
            total_users=self._count(session, select(func.count(LibraryUser.id))),
            active_loans=active_loans,
            pending_returns=active_loans,
            overdue_loans=self._count(
                session,
                select(func.count(Loan.id)).where(Loan.status == "ACTIVE", Loan.due_date < date.today()),
            ),
            low_stock_books=low_stock_books,
        )

    def _get_top_books(self, session: Session) -> list[TopBookItem]:
        total_loans = func.count(Loan.id).label("total_loans")
        rows = session.execute(
            select(Book.id, Book.title, total_loans)
            .join(Loan, Loan.book_id == Book.id)
            .group_by(Book.id, Book.title)
            .order_by(desc(total_loans))
            .limit(REPORT_LIMIT)
        ).all()
        return [TopBookItem(book_id=row.id, title=row.title, total_loans=row.total_loans) for row in rows]

    def _get_loans_by_month(self, session: Session) -> list[MonthlyLoanItem]:
        # Oracle owns date semantics; TRUNC(date, 'MM') groups all loans by calendar month.
        month = func.trunc(Loan.loan_date, "MM").label("month")
        total_loans = func.count(Loan.id).label("total_loans")
        rows = session.execute(
            select(month, total_loans)
            .group_by(month)
            .order_by(desc(month))
            .limit(REPORT_LIMIT)
        ).all()
        return [MonthlyLoanItem(month=self._as_date(row.month), total_loans=row.total_loans) for row in rows]

    def _get_top_users(self, session: Session) -> list[TopUserItem]:
        total_loans = func.count(Loan.id).label("total_loans")
        rows = session.execute(
            select(LibraryUser.id, LibraryUser.username, LibraryUser.full_name, total_loans)
            .join(Loan, Loan.user_id == LibraryUser.id)
            .group_by(LibraryUser.id, LibraryUser.username, LibraryUser.full_name)
            .order_by(desc(total_loans))
            .limit(REPORT_LIMIT)
        ).all()
        return [
            TopUserItem(
                user_id=row.id,
                username=row.username,
                full_name=row.full_name,
                total_loans=row.total_loans,
            )
            for row in rows
        ]

    def _get_low_stock_books(self, session: Session) -> list[LowStockBookItem]:
        rows = session.execute(
            select(Book.id, Book.title, Book.stock_available, Book.stock_total)
            .where(Book.stock_available <= LOW_STOCK_THRESHOLD)
            .order_by(Book.stock_available.asc(), Book.title.asc())
            .limit(REPORT_LIMIT)
        ).all()
        return [
            LowStockBookItem(
                book_id=row.id,
                title=row.title,
                stock_available=row.stock_available,
                stock_total=row.stock_total,
            )
            for row in rows
        ]

    def _count(self, session: Session, statement: Any) -> int:
        """Run a count statement and normalize NULL to zero."""

        return int(session.scalar(statement) or 0)

    def _as_date(self, value: Any) -> date:
        """Normalize Oracle date/datetime values for the Pydantic report schema."""

        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return value.date()


report_repository = SqlAlchemyReportRepository()


__all__ = ["LOW_STOCK_THRESHOLD", "SqlAlchemyReportRepository", "report_repository"]
