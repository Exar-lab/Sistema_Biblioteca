"""User management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import AdminOnly
from app.application.services.user_service import UserService, user_service
from app.core.database import get_db
from app.schemas.users import UserActiveToggle, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service() -> UserService:
    """Return the module-level UserService singleton."""

    return user_service


DbSession = Annotated[Session, Depends(get_db)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("/", response_model=list[UserRead])
def list_users(
    db: DbSession,
    service: UserServiceDep,
    _current_user: AdminOnly,
) -> list[UserRead]:
    """Return all users. Requires admin authentication."""

    return service.get_all(db)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: DbSession,
    service: UserServiceDep,
    _current_user: AdminOnly,
) -> UserRead:
    """Return a single user by ID. Requires admin authentication.

    Returns 404 if the user does not exist.
    """

    return service.get_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: DbSession,
    service: UserServiceDep,
    _current_user: AdminOnly,
) -> UserRead:
    """Partially update a user. Requires admin authentication.

    Returns 404 if the user does not exist.
    Password and password_hash are never included in the response.
    """

    return service.update(db, user_id, payload)


@router.patch("/{user_id}/active", response_model=UserRead)
def toggle_user_active(
    user_id: int,
    payload: UserActiveToggle,
    db: DbSession,
    service: UserServiceDep,
    _current_user: AdminOnly,
) -> UserRead:
    """Activate or deactivate a user. Requires admin authentication.

    Returns 404 if the user does not exist.
    """

    return service.set_active(db, user_id, payload.is_active)


__all__ = ["router", "get_user_service"]
