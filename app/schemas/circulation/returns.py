"""Return schemas."""

from datetime import date
from decimal import Decimal

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema


class ReturnBase(BaseSchema):
    """Shared return fields that map to the Oracle returns table."""

    model_config = ConfigDict(**BaseSchema.model_config, extra="forbid")

    loan_id: int = Field(..., gt=0, description="Loan identifier being closed.")
    fine_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Fine applied to the return.",
    )
    notes: str | None = Field(default=None, max_length=1000, description="Optional return notes.")


class ReturnCreate(ReturnBase):
    """Payload used to record a return."""


class ReturnUpdate(BaseSchema):
    """Payload used to update a return record."""

    model_config = ConfigDict(**BaseSchema.model_config, extra="forbid")

    fine_amount: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    notes: str | None = Field(default=None, max_length=1000)


class ReturnRead(ReturnBase, IdSchema, TimestampSchema):
    """Return data returned by the API."""

    return_date: date | None = None


__all__ = ["ReturnBase", "ReturnCreate", "ReturnRead", "ReturnUpdate"]
