"""Return schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema
from app.schemas.catalog.books import BookRead
from app.schemas.users import UserRead


class ReturnBase(BaseSchema):
    """Shared return fields."""

    loan_id: int = Field(..., gt=0, description="Loan identifier being closed.")
    return_date: date = Field(default_factory=date.today, description="Date of the return.")
    fine_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Fine applied to the return.",
    )
    notes: str | None = Field(default=None, max_length=500, description="Optional return notes.")


class ReturnCreate(ReturnBase):
    """Payload used to record a return."""


class ReturnUpdate(BaseSchema):
    """Payload used to update a return record."""

    return_date: date | None = None
    fine_amount: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    notes: str | None = Field(default=None, max_length=500)


class ReturnRead(ReturnBase, IdSchema, TimestampSchema):
    """Return data returned by the API."""

    processed_at: datetime | None = Field(default=None, description="Timestamp when the return was registered.")
    user: UserRead | None = None
    book: BookRead | None = None


__all__ = ["ReturnBase", "ReturnCreate", "ReturnUpdate", "ReturnRead"]
