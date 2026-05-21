"""Category API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.application.errors import ConflictError, NotFoundError
from app.application.services.category_service import CategoryService
from app.core.database import get_db
from app.infrastructure.repositories.category_repository import category_repository
from app.schemas.catalog.categories import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])


def get_category_service() -> CategoryService:
    """Build the category service with the SQLAlchemy repository adapter."""

    return CategoryService(category_repository)


DbSession = Annotated[Session, Depends(get_db)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]


@router.get("/", response_model=list[CategoryRead])
def list_categories(db: DbSession, service: CategoryServiceDep) -> list[object]:
    """List all categories."""

    return service.list_categories(db)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: DbSession,
    service: CategoryServiceDep,
) -> object:
    """Create a category."""

    try:
        return service.create_category(db, payload)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: DbSession, service: CategoryServiceDep) -> object:
    """Return a category by id."""

    try:
        return service.get_category(db, category_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: DbSession,
    service: CategoryServiceDep,
) -> object:
    """Update a category."""

    try:
        return service.update_category(db, category_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession, service: CategoryServiceDep) -> Response:
    """Delete a category."""

    try:
        service.delete_category(db, category_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router", "get_category_service"]
