"""Author schemas."""

from pydantic import Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema


class AuthorBase(BaseSchema):
    """Shared author fields."""

    first_name: str = Field(..., min_length=2, max_length=80, description="Author first name.")
    last_name: str = Field(..., min_length=2, max_length=80, description="Author last name.")
    biography: str | None = Field(default=None, max_length=2000, description="Short author biography.")
    nationality: str | None = Field(default=None, max_length=80, description="Author nationality.")
    is_active: bool = Field(default=True, description="Whether the author is active.")


class AuthorCreate(AuthorBase):
    """Payload used to create an author."""


class AuthorUpdate(BaseSchema):
    """Payload used to update an author."""

    first_name: str | None = Field(default=None, min_length=2, max_length=80)
    last_name: str | None = Field(default=None, min_length=2, max_length=80)
    biography: str | None = Field(default=None, max_length=2000)
    nationality: str | None = Field(default=None, max_length=80)
    is_active: bool | None = None


class AuthorRead(AuthorBase, IdSchema, TimestampSchema):
    """Author data returned by the API."""

    full_name: str | None = Field(default=None, description="Convenience display name.")


__all__ = ["AuthorBase", "AuthorCreate", "AuthorUpdate", "AuthorRead"]
