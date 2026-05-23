"""Author schemas."""

from datetime import date

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema


class AuthorBase(BaseSchema):
    """Shared author fields."""

    model_config = ConfigDict(**BaseSchema.model_config, extra="forbid")

    first_name: str = Field(..., min_length=2, max_length=80, description="Author first name.")
    last_name: str = Field(..., min_length=2, max_length=80, description="Author last name.")
    biography: str | None = Field(default=None, max_length=2000, description="Short author biography.")
    birth_date: date | None = Field(default=None, description="Author birth date.")
    death_date: date | None = Field(default=None, description="Author death date.")
    is_active: bool = Field(default=True, description="Whether the author is active.")


class AuthorCreate(AuthorBase):
    """Payload used to create an author."""


class AuthorUpdate(BaseSchema):
    """Payload used to update an author."""

    model_config = ConfigDict(**BaseSchema.model_config, extra="forbid")

    first_name: str | None = Field(default=None, min_length=2, max_length=80)
    last_name: str | None = Field(default=None, min_length=2, max_length=80)
    biography: str | None = Field(default=None, max_length=2000)
    birth_date: date | None = None
    death_date: date | None = None
    is_active: bool | None = None


class AuthorRead(AuthorBase, IdSchema, TimestampSchema):
    """Author data returned by the API."""


__all__ = ["AuthorBase", "AuthorCreate", "AuthorUpdate", "AuthorRead"]
