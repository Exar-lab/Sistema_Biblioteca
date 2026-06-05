"""Book API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.application.services.book_service import BookService
from app.core.database import get_db
from app.infrastructure.repositories.book_repository import book_repository
from app.schemas.catalog.books import BookCreate, BookRead, BookUpdate

router = APIRouter(prefix="/books", tags=["Books"])


def get_book_service() -> BookService:
    """Build the book service with the SQLAlchemy repository adapter."""

    return BookService(book_repository)


DbSession = Annotated[Session, Depends(get_db)]
BookServiceDep = Annotated[BookService, Depends(get_book_service)]


@router.get("/", response_model=list[BookRead])
def list_books(
    db: DbSession,
    service: BookServiceDep,
    title: str | None = Query(default=None, description="Case-insensitive substring match on book title."),
    author: str | None = Query(default=None, description="Case-insensitive substring match on author full name."),
    category: str | None = Query(default=None, description="Case-insensitive substring match on category name."),
) -> list[object]:
    """List all books, optionally filtered by title, author, and/or category."""

    return service.list_books(db, title=title, author=author, category=category)


@router.post("/", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: DbSession, service: BookServiceDep) -> object:
    """Create a book."""

    return service.create_book(db, payload)


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: DbSession, service: BookServiceDep) -> object:
    """Return a book by id."""

    return service.get_book(db, book_id)


@router.patch("/{book_id}", response_model=BookRead)
def update_book(book_id: int, payload: BookUpdate, db: DbSession, service: BookServiceDep) -> object:
    """Update a book."""

    return service.update_book(db, book_id, payload)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: DbSession, service: BookServiceDep) -> Response:
    """Delete a book."""

    service.delete_book(db, book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router", "get_book_service"]
