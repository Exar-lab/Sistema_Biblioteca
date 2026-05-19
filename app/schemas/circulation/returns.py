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
    condition: str | None = Field(default=None, max_length=120, description="Condition of the returned copy.")
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


class ReturnRead(ReturnBase, IdSchema, TimestampSchema):
    """Return data returned by the API."""

    processed_at: datetime | None = Field(default=None, description="Timestamp when the return was registered.")
    processed_by_user_id: int | None = Field(default=None, gt=0, description="User that processed the return.")
    user: UserRead | None = None
    book: BookRead | None = None


__all__ = ["ReturnBase", "ReturnCreate", "ReturnRead"]
