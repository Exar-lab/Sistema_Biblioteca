"""Roles router — CRUD endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.role_service import RoleService
from app.composition import get_role_service
from app.schemas.roles import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/", response_model=list[RoleRead], status_code=status.HTTP_200_OK)
def list_roles(
    db: Session = Depends(get_db),
    service: RoleService = Depends(get_role_service),
) -> list[RoleRead]:
    """Return all roles."""
    return service.list(db)


@router.get("/{role_id}", response_model=RoleRead, status_code=status.HTTP_200_OK)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """Return a single role by ID (raises 404 if not found)."""
    return service.get(db, role_id)


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """Create a new role."""
    return service.create(db, payload)


@router.put("/{role_id}", response_model=RoleRead, status_code=status.HTTP_200_OK)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """Update an existing role (raises 404 if not found)."""
    return service.update(db, role_id, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    service: RoleService = Depends(get_role_service),
) -> None:
    """Delete a role (raises 404 if not found)."""
    service.delete(db, role_id)
