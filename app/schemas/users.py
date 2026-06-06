"""User and authentication schemas."""

from pydantic import ConfigDict, Field, SecretStr

from app.schemas.base import BaseSchema, CredentialSchema, IdSchema, TimestampSchema
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
    """Payload used by administrators to create a user."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=False,
        validate_assignment=True,
    )

    password: SecretStr = Field(..., min_length=8, max_length=128, description="Plain password.")


class UserRegister(CredentialSchema):
    """Public self-registration payload.

    Role and active-state fields are intentionally excluded so public clients
    cannot request elevated privileges or inactive-account state.
    """

    model_config = ConfigDict(**CredentialSchema.model_config, extra="forbid")

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
    password: SecretStr = Field(..., min_length=8, max_length=128, description="Plain password.")


class UserUpdate(BaseSchema):
    """Payload used to update a user."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=False,
        validate_assignment=True,
    )

    username: str | None = Field(default=None, min_length=3, max_length=50)
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    email: str | None = Field(default=None, min_length=5, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None
    role_id: int | None = Field(default=None, gt=0)
    password: SecretStr | None = Field(default=None, min_length=8, max_length=128)


class UserRead(UserBase, IdSchema, TimestampSchema):
    """User data returned by the API."""

    role: RoleRead | None = None


class UserCreateWithHash(BaseSchema):
    """Internal schema used to pass a hashed-password user record to the repository.

    This schema must NOT be exposed in any API response. It exists solely to carry
    attribute access (data.username, data.password_hash, etc.) into the repository
    layer without exposing a plain-text password field.
    """

    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
    )
    phone: str | None = Field(default=None, max_length=30)
    password_hash: str = Field(..., description="Bcrypt hash — never return in API responses.")
    is_active: bool = Field(default=True)
    role_id: int = Field(default=2, gt=0)


class UserActiveToggle(BaseSchema):
    """Payload used to toggle the active state of a user."""

    is_active: bool = Field(..., description="Set to true to activate, false to deactivate.")


class UserLogin(CredentialSchema):
    """Login payload."""

    username: str = Field(..., min_length=3, max_length=50)
    password: SecretStr = Field(..., min_length=1, max_length=128)


class UserChangePassword(CredentialSchema):
    """Password change payload."""

    current_password: SecretStr = Field(..., min_length=1, max_length=128)
    new_password: SecretStr = Field(..., min_length=8, max_length=128)


__all__ = [
    "UserBase",
    "UserCreate",
    "UserRegister",
    "UserCreateWithHash",
    "UserActiveToggle",
    "UserUpdate",
    "UserRead",
    "UserLogin",
    "UserChangePassword",
]
