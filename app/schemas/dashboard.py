"""Dashboard and report schemas."""

from datetime import date

from pydantic import Field

from app.schemas.base import BaseSchema


class DashboardSummary(BaseSchema):
    """High-level dashboard counters."""

    total_books: int = Field(default=0, ge=0)
    total_users: int = Field(default=0, ge=0)
    active_loans: int = Field(default=0, ge=0)
    pending_returns: int = Field(default=0, ge=0)
    overdue_loans: int = Field(default=0, ge=0)
    low_stock_books: int = Field(default=0, ge=0)


class TopBookItem(BaseSchema):
    """Most borrowed book entry."""

    book_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=2, max_length=200)
    total_loans: int = Field(default=0, ge=0)


class MonthlyLoanItem(BaseSchema):
    """Loans grouped by month."""

    month: date
    total_loans: int = Field(default=0, ge=0)


class TopUserItem(BaseSchema):
    """User with the highest loan count."""

    user_id: int = Field(..., gt=0)
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=120)
    total_loans: int = Field(default=0, ge=0)


class LowStockBookItem(BaseSchema):
    """Book with a low available stock."""

    book_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=2, max_length=200)
    stock_available: int = Field(default=0, ge=0)
    stock_total: int = Field(default=0, ge=0)


class ReportsDashboard(BaseSchema):
    """Combined report payload for the admin dashboard."""

    summary: DashboardSummary
    top_books: list[TopBookItem] = Field(default_factory=list)
    loans_by_month: list[MonthlyLoanItem] = Field(default_factory=list)
    top_users: list[TopUserItem] = Field(default_factory=list)
    low_stock_books: list[LowStockBookItem] = Field(default_factory=list)


__all__ = [
    "DashboardSummary",
    "TopBookItem",
    "MonthlyLoanItem",
    "TopUserItem",
    "LowStockBookItem",
    "ReportsDashboard",
]
