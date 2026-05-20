"""Loan schemas."""

from datetime import date

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
    status: str = Field(default="ACTIVE", description="Loan status: ACTIVE or RETURNED.")


class LoanCreate(LoanBase):
    """Payload used to create a loan."""


class LoanUpdate(BaseSchema):
    """Payload used to update a loan."""

    due_date: date | None = None
    status: str | None = Field(default=None, description="Updated loan status.")


class LoanRead(LoanBase, IdSchema, TimestampSchema):
    """Loan data returned by the API."""

    return_date: date | None = Field(default=None, description="Date when the book was returned.")
    user: UserRead | None = None
    book: BookRead | None = None


__all__ = ["LoanBase", "LoanCreate", "LoanUpdate", "LoanRead"]
