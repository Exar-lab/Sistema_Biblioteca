"""Books router — CRUD endpoints including author association."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.book_service import BookService
from app.composition import get_book_service
from app.schemas.catalog.books import BookCreate, BookRead, BookUpdate


class AuthorIdsPayload(BaseModel):
    author_ids: list[int]

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("/", response_model=list[BookRead], status_code=status.HTTP_200_OK)
def list_books(
    db: Session = Depends(get_db),
    service: BookService = Depends(get_book_service),
) -> list[BookRead]:
    """Return all books."""
    return service.list(db)


@router.get("/{book_id}", response_model=BookRead, status_code=status.HTTP_200_OK)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    service: BookService = Depends(get_book_service),
) -> BookRead:
    """Return a single book with its authors (raises 404 if not found)."""
    return service.get_with_authors(db, book_id)


@router.post("/", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    db: Session = Depends(get_db),
    service: BookService = Depends(get_book_service),
) -> BookRead:
    """Create a new book."""
    return service.create(db, payload)


@router.put("/{book_id}", response_model=BookRead, status_code=status.HTTP_200_OK)
def update_book(
    book_id: int,
    payload: BookUpdate,
    db: Session = Depends(get_db),
    service: BookService = Depends(get_book_service),
) -> BookRead:
    """Update an existing book (raises 404 if not found)."""
    return service.update(db, book_id, payload)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    service: BookService = Depends(get_book_service),
) -> None:
    """Delete a book (raises 404 if not found)."""
    service.delete(db, book_id)


@router.put("/{book_id}/authors", response_model=BookRead, status_code=status.HTTP_200_OK)
def set_book_authors(
    book_id: int,
    payload: AuthorIdsPayload,
    db: Session = Depends(get_db),
    service: BookService = Depends(get_book_service),
) -> BookRead:
    """Replace the author associations for a book (raises 404 if book not found)."""
    service.set_authors(db, book_id, payload.author_ids)
    return service.get_with_authors(db, book_id)
