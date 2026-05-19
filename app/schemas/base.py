"""Shared Pydantic base schemas.

These classes keep common validation and serialization behavior in one place,
so the domain schemas can stay focused on business data.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema for request and response models."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class CredentialSchema(BaseModel):
    """Base schema for payloads that contain opaque credential values."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=False,
        validate_assignment=True,
    )


class IdSchema(BaseSchema):
    """Schema for models persisted with a numeric identifier."""

    id: int = Field(..., gt=0, description="Unique numeric identifier.")


class TimestampSchema(BaseSchema):
    """Schema for models that expose audit timestamps."""

    created_at: datetime | None = Field(
        default=None,
        description="Date and time when the record was created.",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Date and time when the record was last updated.",
    )
