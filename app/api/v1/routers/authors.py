"""Author API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.application.errors import ConflictError, NotFoundError
from app.application.services.author_service import AuthorService
from app.core.database import get_db
from app.infrastructure.repositories.author_repository import author_repository
from app.schemas.catalog.authors import AuthorCreate, AuthorRead, AuthorUpdate

router = APIRouter(prefix="/authors", tags=["Authors"])


def get_author_service() -> AuthorService:
    """Build the author service with the SQLAlchemy repository adapter."""

    return AuthorService(author_repository)


DbSession = Annotated[Session, Depends(get_db)]
AuthorServiceDep = Annotated[AuthorService, Depends(get_author_service)]


@router.get("/", response_model=list[AuthorRead])
def list_authors(db: DbSession, service: AuthorServiceDep) -> list[object]:
    """List all authors."""

    return service.list_authors(db)


@router.post("/", response_model=AuthorRead, status_code=status.HTTP_201_CREATED)
def create_author(payload: AuthorCreate, db: DbSession, service: AuthorServiceDep) -> object:
    """Create an author."""

    try:
        return service.create_author(db, payload)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{author_id}", response_model=AuthorRead)
def get_author(author_id: int, db: DbSession, service: AuthorServiceDep) -> object:
    """Return an author by id."""

    try:
        return service.get_author(db, author_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{author_id}", response_model=AuthorRead)
def update_author(author_id: int, payload: AuthorUpdate, db: DbSession, service: AuthorServiceDep) -> object:
    """Update an author."""

    try:
        return service.update_author(db, author_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(author_id: int, db: DbSession, service: AuthorServiceDep) -> Response:
    """Delete an author."""

    try:
        service.delete_author(db, author_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router", "get_author_service"]
