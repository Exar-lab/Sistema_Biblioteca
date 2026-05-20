"""Categories router — CRUD endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.category_service import CategoryService
from app.composition import get_category_service
from app.schemas.catalog.categories import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[CategoryRead], status_code=status.HTTP_200_OK)
def list_categories(
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
) -> list[CategoryRead]:
    """Return all categories."""
    return service.list(db)


@router.get("/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    """Return a single category by ID (raises 404 if not found)."""
    return service.get(db, category_id)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    """Create a new category."""
    return service.create(db, payload)


@router.put("/{category_id}", response_model=CategoryRead, status_code=status.HTTP_200_OK)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
) -> CategoryRead:
    """Update an existing category (raises 404 if not found)."""
    return service.update(db, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
) -> None:
    """Delete a category (raises 404 if not found)."""
    service.delete(db, category_id)
