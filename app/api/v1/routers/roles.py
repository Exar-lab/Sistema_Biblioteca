"""Role API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.application.services.role_service import RoleService
from app.core.database import get_db
from app.infrastructure.repositories.role_repository import role_repository
from app.schemas.roles import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_role_service() -> RoleService:
    """Build the role service with the SQLAlchemy repository adapter."""

    return RoleService(role_repository)


DbSession = Annotated[Session, Depends(get_db)]
RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]


@router.get("/", response_model=list[RoleRead])
def list_roles(db: DbSession, service: RoleServiceDep) -> list[object]:
    """List all roles."""

    return service.list_roles(db)


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: DbSession, service: RoleServiceDep) -> object:
    """Create a role."""

    return service.create_role(db, payload)


@router.get("/{role_id}", response_model=RoleRead)
def get_role(role_id: int, db: DbSession, service: RoleServiceDep) -> object:
    """Return a role by id."""

    return service.get_role(db, role_id)


@router.patch("/{role_id}", response_model=RoleRead)
def update_role(role_id: int, payload: RoleUpdate, db: DbSession, service: RoleServiceDep) -> object:
    """Update a role."""

    return service.update_role(db, role_id, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: DbSession, service: RoleServiceDep) -> Response:
    """Delete a role."""

    service.delete_role(db, role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router", "get_role_service"]
