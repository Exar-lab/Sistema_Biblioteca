"""Shared FastAPI dependencies for auth and database."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.ports.user_repository import UserRepository
from app.core.database import get_db
from app.core.security import decode_token
from app.infrastructure.repositories.user_repository import user_repository
from app.schemas.users import UserRead

security_scheme = HTTPBearer()

INVALID_TOKEN_DETAIL = "Invalid or expired token."
ADMIN_ROLE = "admin"


def _unauthorized(detail: str = INVALID_TOKEN_DETAIL) -> HTTPException:
    """Return the shared 401 response used by auth dependencies."""

    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _normalize_role_name(role_name: str | None) -> str:
    """Normalize role names for policy checks."""

    return (role_name or "").strip().casefold()


def _get_subject(payload: dict) -> int:
    """Return the integer JWT subject or raise 401 for malformed claims."""

    subject = payload.get("sub")
    if subject is None:
        raise _unauthorized()

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise _unauthorized() from exc


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Annotated[Session, Depends(get_db)],
    repo: Annotated[UserRepository, Depends(lambda: user_repository)],
) -> UserRead:
    """Decode the JWT, load the user, and return their profile.

    Raises HTTPException 401 if the token is invalid or the user does not exist.
    """

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise _unauthorized()

    user_id = _get_subject(payload)
    user = repo.get_by_id(db, user_id)
    if user is None:
        raise _unauthorized("User not found.")

    return UserRead.model_validate(user)


def require_role(*allowed_roles: str) -> Callable[[UserRead], UserRead]:
    """Return a dependency that checks the current user has one of *allowed_roles*."""

    normalized_allowed_roles = {_normalize_role_name(role) for role in allowed_roles}

    def _role_checker(current_user: Annotated[UserRead, Depends(get_current_user)]) -> UserRead:
        current_role = _normalize_role_name(current_user.role.name if current_user.role else None)
        if current_role not in normalized_allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return _role_checker


AdminOnly = Annotated[UserRead, Depends(require_role(ADMIN_ROLE))]
"""Composite dependency that requires an authenticated admin user."""


__all__ = ["get_db", "get_current_user", "require_role", "AdminOnly", "security_scheme"]
