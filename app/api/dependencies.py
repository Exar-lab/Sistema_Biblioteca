"""Shared FastAPI dependencies for auth and database."""

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


__all__ = ["get_db", "get_current_user", "security_scheme"]
