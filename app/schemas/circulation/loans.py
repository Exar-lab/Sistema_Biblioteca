"""Loan schemas."""

from datetime import date
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema
from app.schemas.catalog.books import BookRead
from app.schemas.users import UserRead

LoanStatus = Literal["ACTIVE", "RETURNED", "OVERDUE", "CANCELLED"]


class LoanBase(BaseSchema):
    """Shared loan fields that map to the Oracle loans table."""

    model_config = ConfigDict(**BaseSchema.model_config, extra="forbid")

    user_id: int = Field(..., gt=0, description="Borrowing user identifier.")
    book_id: int = Field(..., gt=0, description="Borrowed book identifier.")
    loan_date: date = Field(default_factory=date.today, description="Loan start date.")
    due_date: date = Field(..., description="Date when the book must be returned.")

    @model_validator(mode="after")
    def validate_due_date(self) -> "LoanBase":
        """Ensure Oracle's due-date invariant is enforced before persistence."""

        if self.due_date < self.loan_date:
            raise ValueError("due_date must be on or after loan_date")
        return self


class LoanCreate(LoanBase):
    """Payload used to create a loan."""


class LoanUpdate(BaseSchema):
    """Payload used to update a loan's safe admin-editable fields."""

    model_config = ConfigDict(**BaseSchema.model_config, extra="forbid")

    due_date: date | None = None


class LoanRead(LoanBase, IdSchema, TimestampSchema):
    """Loan data returned by the API."""

    return_date: date | None = Field(default=None, description="Date when the book was returned.")
    status: LoanStatus = Field(default="ACTIVE", description="Current loan workflow status.")
    user: UserRead | None = None
    book: BookRead | None = None


__all__ = ["LoanBase", "LoanCreate", "LoanRead", "LoanStatus", "LoanUpdate"]
