"""User and authentication schemas."""

from pydantic import Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema
from app.schemas.roles import RoleRead


class UserBase(BaseSchema):
    """Shared user fields."""

    username: str = Field(..., min_length=3, max_length=50, description="Login username.")
    full_name: str = Field(..., min_length=2, max_length=120, description="User full name.")
    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
        description="Email address.",
    )
    phone: str | None = Field(default=None, max_length=30, description="Phone number.")
    is_active: bool = Field(default=True, description="Whether the user can log in.")
    role_id: int | None = Field(default=None, gt=0, description="Assigned role identifier.")


class UserCreate(UserBase):
    """Payload used to create a user."""

    password: str = Field(..., min_length=8, max_length=128, description="Plain password.")


class UserUpdate(BaseSchema):
    """Payload used to update a user."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: str | None = Field(default=None, min_length=5, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None
    role_id: int | None = Field(default=None, gt=0)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(UserBase, IdSchema, TimestampSchema):
    """User data returned by the API."""

    role: RoleRead | None = None


class UserLogin(BaseSchema):
    """Login payload."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class UserChangePassword(BaseSchema):
    """Password change payload."""

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserLogin",
    "UserChangePassword",
]
