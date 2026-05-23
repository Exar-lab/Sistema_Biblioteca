"""Book API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.application.errors import ConflictError, NotFoundError
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
def list_books(db: DbSession, service: BookServiceDep) -> list[object]:
    """List all books."""

    return service.list_books(db)


@router.post("/", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: DbSession, service: BookServiceDep) -> object:
    """Create a book."""

    try:
        return service.create_book(db, payload)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: DbSession, service: BookServiceDep) -> object:
    """Return a book by id."""

    try:
        return service.get_book(db, book_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{book_id}", response_model=BookRead)
def update_book(book_id: int, payload: BookUpdate, db: DbSession, service: BookServiceDep) -> object:
    """Update a book."""

    try:
        return service.update_book(db, book_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: DbSession, service: BookServiceDep) -> Response:
    """Delete a book."""

    try:
        service.delete_book(db, book_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router", "get_book_service"]
