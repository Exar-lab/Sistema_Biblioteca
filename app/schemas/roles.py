"""Role schemas."""

from pydantic import Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema


class RoleBase(BaseSchema):
    """Shared role fields."""

    name: str = Field(..., min_length=2, max_length=50, description="Role name.")
    description: str | None = Field(default=None, max_length=255, description="Role description.")


class RoleCreate(RoleBase):
    """Payload used to create a role."""


class RoleUpdate(BaseSchema):
    """Payload used to update a role."""

    name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)


class RoleRead(RoleBase, IdSchema, TimestampSchema):
    """Role data returned by the API."""


__all__ = ["RoleBase", "RoleCreate", "RoleUpdate", "RoleRead"]
