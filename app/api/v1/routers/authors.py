"""Authors router — CRUD endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.author_service import AuthorService
from app.composition import get_author_service
from app.schemas.catalog.authors import AuthorCreate, AuthorRead, AuthorUpdate

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.get("/", response_model=list[AuthorRead], status_code=status.HTTP_200_OK)
def list_authors(
    db: Session = Depends(get_db),
    service: AuthorService = Depends(get_author_service),
) -> list[AuthorRead]:
    """Return all authors."""
    return service.list(db)


@router.get("/{author_id}", response_model=AuthorRead, status_code=status.HTTP_200_OK)
def get_author(
    author_id: int,
    db: Session = Depends(get_db),
    service: AuthorService = Depends(get_author_service),
) -> AuthorRead:
    """Return a single author by ID (raises 404 if not found)."""
    return service.get(db, author_id)


@router.post("/", response_model=AuthorRead, status_code=status.HTTP_201_CREATED)
def create_author(
    payload: AuthorCreate,
    db: Session = Depends(get_db),
    service: AuthorService = Depends(get_author_service),
) -> AuthorRead:
    """Create a new author."""
    return service.create(db, payload)


@router.put("/{author_id}", response_model=AuthorRead, status_code=status.HTTP_200_OK)
def update_author(
    author_id: int,
    payload: AuthorUpdate,
    db: Session = Depends(get_db),
    service: AuthorService = Depends(get_author_service),
) -> AuthorRead:
    """Update an existing author (raises 404 if not found)."""
    return service.update(db, author_id, payload)


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    service: AuthorService = Depends(get_author_service),
) -> None:
    """Delete an author (raises 404 if not found)."""
    service.delete(db, author_id)
