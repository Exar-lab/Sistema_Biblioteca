"""Shared FastAPI dependencies for auth and database."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.ports.user_repository import UserRepository
from app.core.database import get_db
from app.core.security import decode_token
from app.infrastructure.repositories.user_repository import user_repository
from app.schemas.users import UserRead

security_scheme = HTTPBearer()


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user_id = int(payload.get("sub", 0))
    user = repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return UserRead.model_validate(user)


def require_role(*allowed_roles: str) -> Callable[[UserRead], UserRead]:
    """Return a dependency that checks the current user has one of *allowed_roles*."""

    def _role_checker(current_user: Annotated[UserRead, Depends(get_current_user)]) -> UserRead:
        if current_user.role is None or current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return _role_checker


AdminOnly = Annotated[UserRead, Depends(require_role("Admin"))]
"""Composite dependency that requires an authenticated admin user."""


__all__ = ["get_db", "get_current_user", "require_role", "AdminOnly", "security_scheme"]
