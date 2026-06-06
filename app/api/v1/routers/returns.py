"""Returns API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import AdminOnly
from app.application.services.return_service import ReturnService
from app.core.database import get_db
from app.infrastructure.repositories.loan_repository import loan_repository
from app.infrastructure.repositories.return_repository import return_repository
from app.schemas.circulation.returns import ReturnCreate, ReturnRead, ReturnUpdate

router = APIRouter(prefix="/returns", tags=["Returns"])


def get_return_service() -> ReturnService:
    """Build the return service with SQLAlchemy repository adapters."""

    return ReturnService(return_repository, loan_repository)


DbSession = Annotated[Session, Depends(get_db)]
ReturnServiceDep = Annotated[ReturnService, Depends(get_return_service)]


@router.get("/", response_model=list[ReturnRead])
def list_returns(db: DbSession, service: ReturnServiceDep, _current_user: AdminOnly) -> list[object]:
    """List all return records."""

    return service.list_returns(db)


@router.post("/", response_model=ReturnRead, status_code=status.HTTP_201_CREATED)
def create_return(
    payload: ReturnCreate,
    db: DbSession,
    service: ReturnServiceDep,
    _current_user: AdminOnly,
) -> object:
    """Record a book return."""

    return service.create_return(db, payload)


@router.get("/{return_id}", response_model=ReturnRead)
def get_return(return_id: int, db: DbSession, service: ReturnServiceDep, _current_user: AdminOnly) -> object:
    """Return a return record by id."""

    return service.get_return(db, return_id)


@router.patch("/{return_id}", response_model=ReturnRead)
def update_return(
    return_id: int,
    payload: ReturnUpdate,
    db: DbSession,
    service: ReturnServiceDep,
    _current_user: AdminOnly,
) -> object:
    """Update a return record (fine amount or notes)."""

    return service.update_return(db, return_id, payload)


__all__ = ["router", "get_return_service"]
