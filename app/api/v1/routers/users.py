"""Users router — CRUD endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.user_service import UserService
from app.composition import get_user_service
from app.schemas.users import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserRead], status_code=status.HTTP_200_OK)
def list_users(
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    """Return all users."""
    return service.list(db)


@router.get("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Return a single user by ID (raises 404 if not found)."""
    return service.get(db, user_id)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Create a new user."""
    return service.create(db, payload)


@router.put("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Update an existing user (raises 404 if not found)."""
    return service.update(db, user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> None:
    """Delete a user (raises 404 if not found)."""
    service.delete(db, user_id)
