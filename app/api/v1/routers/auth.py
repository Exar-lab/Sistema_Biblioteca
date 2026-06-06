"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.application.services.auth_service import AuthService
from app.core.database import get_db
from app.infrastructure.repositories.user_repository import user_repository
from app.schemas.auth import LoginResponse
from app.schemas.users import UserChangePassword, UserLogin, UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service() -> AuthService:
    """Build the auth service with the SQLAlchemy repository adapter."""

    return AuthService(user_repository)


DbSession = Annotated[Session, Depends(get_db)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/login", response_model=LoginResponse)
def login(payload: UserLogin, db: DbSession, service: AuthServiceDep) -> LoginResponse:
    """Authenticate user and return a JWT token with user profile."""

    return service.authenticate(db, payload.username, payload.password.get_secret_value())


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserRegister, db: DbSession, service: AuthServiceDep) -> UserRead:
    """Register a new user account.

    Returns 201 with UserRead on success.
    Returns 409 if the username is already taken.
    Password and password_hash are never included in the response.
    """

    return service.register(db, payload)


@router.get("/me", response_model=UserRead)
def get_me(current_user: Annotated[UserRead, Depends(get_current_user)]) -> UserRead:
    """Return the authenticated user's profile."""

    return current_user


@router.patch("/me/password", response_model=UserRead)
def change_password(
    payload: UserChangePassword,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: DbSession,
    service: AuthServiceDep,
) -> UserRead:
    """Change the authenticated user's password."""

    return service.change_password(db, current_user.id, payload)


__all__ = ["router", "get_auth_service"]
