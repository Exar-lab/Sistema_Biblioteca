"""Authentication schemas."""

from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.users import UserRead


class Token(BaseSchema):
    """Access token response."""

    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field(default="bearer", description="Token type.")


class TokenPayload(BaseSchema):
    """Decoded token data."""

    sub: int | None = Field(default=None, description="User identifier.")
    username: str | None = Field(default=None, description="Username in the token.")
    role: str | None = Field(default=None, description="Role name in the token.")


class LoginResponse(BaseSchema):
    """Login response with user profile."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead


__all__ = ["Token", "TokenPayload", "LoginResponse"]
