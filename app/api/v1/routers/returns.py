"""Returns router — CRUD endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.return_service import ReturnService
from app.composition import get_return_service
from app.schemas.circulation.returns import ReturnCreate, ReturnRead, ReturnUpdate

router = APIRouter(prefix="/returns", tags=["Returns"])


@router.get("/", response_model=list[ReturnRead], status_code=status.HTTP_200_OK)
def list_returns(
    db: Session = Depends(get_db),
    service: ReturnService = Depends(get_return_service),
) -> list[ReturnRead]:
    """Return all return records."""
    return service.list(db)


@router.get("/{return_id}", response_model=ReturnRead, status_code=status.HTTP_200_OK)
def get_return(
    return_id: int,
    db: Session = Depends(get_db),
    service: ReturnService = Depends(get_return_service),
) -> ReturnRead:
    """Return a single return record by ID (raises 404 if not found)."""
    return service.get(db, return_id)


@router.post("/", response_model=ReturnRead, status_code=status.HTTP_201_CREATED)
def create_return(
    payload: ReturnCreate,
    db: Session = Depends(get_db),
    service: ReturnService = Depends(get_return_service),
) -> ReturnRead:
    """Record a new book return."""
    return service.create(db, payload)


@router.put("/{return_id}", response_model=ReturnRead, status_code=status.HTTP_200_OK)
def update_return(
    return_id: int,
    payload: ReturnUpdate,
    db: Session = Depends(get_db),
    service: ReturnService = Depends(get_return_service),
) -> ReturnRead:
    """Update an existing return record (raises 404 if not found)."""
    return service.update(db, return_id, payload)


@router.delete("/{return_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_return(
    return_id: int,
    db: Session = Depends(get_db),
    service: ReturnService = Depends(get_return_service),
) -> None:
    """Delete a return record (raises 404 if not found)."""
    service.delete(db, return_id)
