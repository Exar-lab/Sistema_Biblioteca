"""Loan schemas."""

from datetime import date, datetime

from pydantic import Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema
from app.schemas.catalog.books import BookRead
from app.schemas.users import UserRead


class LoanBase(BaseSchema):
    """Shared loan fields."""

    user_id: int = Field(..., gt=0, description="Borrowing user identifier.")
    book_id: int = Field(..., gt=0, description="Borrowed book identifier.")
    loan_date: date = Field(default_factory=date.today, description="Loan start date.")
    due_date: date = Field(..., description="Date when the book must be returned.")
    notes: str | None = Field(default=None, max_length=500, description="Optional loan notes.")
    is_active: bool = Field(default=True, description="Whether the loan is open.")


class LoanCreate(LoanBase):
    """Payload used to create a loan."""


class LoanUpdate(BaseSchema):
    """Payload used to update a loan."""

    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class LoanRead(LoanBase, IdSchema, TimestampSchema):
    """Loan data returned by the API."""

    returned_at: datetime | None = Field(default=None, description="Return timestamp when the book was returned.")
    is_overdue: bool = Field(default=False, description="Whether the loan is overdue.")
    user: UserRead | None = None
    book: BookRead | None = None


__all__ = ["LoanBase", "LoanCreate", "LoanUpdate", "LoanRead"]
