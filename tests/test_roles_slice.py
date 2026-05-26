"""Tests for the catalog CRUD vertical slice: roles."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1"

import main  # noqa: E402
from app.api.v1.routers.roles import get_role_service  # noqa: E402
from app.application.errors import ConflictError, NotFoundError  # noqa: E402
from app.application.services.role_service import RoleService  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.schemas.roles import RoleCreate, RoleUpdate  # noqa: E402


@dataclass
class RoleStub:
    id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FakeRoleRepository:
    def __init__(self) -> None:
        self.items: dict[int, RoleStub] = {1: RoleStub(id=1, name="Admin")}
        self.next_id = 2

    def get_by_id(self, _session: Any, id: int) -> RoleStub | None:
        return self.items.get(id)

    def list_all(self, _session: Any) -> list[RoleStub]:
        return list(self.items.values())

    def create(self, _session: Any, data: RoleCreate) -> RoleStub:
        if any(item.name == data.name for item in self.items.values()):
            raise ConflictError("Role name already exists.")
        role = RoleStub(id=self.next_id, **data.model_dump())
        self.items[role.id] = role
        self.next_id += 1
        return role

    def update(self, _session: Any, id: int, data: RoleUpdate) -> RoleStub | None:
        role = self.items.get(id)
        if role is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        return role

    def delete(self, _session: Any, id: int) -> bool:
        return self.items.pop(id, None) is not None


def test_role_schema_rejects_is_active_extra_field() -> None:
    with pytest.raises(ValidationError):
        RoleCreate(name="Admin", is_active=True)


def test_role_schema_rejects_name_above_oracle_length() -> None:
    with pytest.raises(ValidationError):
        RoleCreate(name="x" * 31)


def test_role_service_raises_not_found_for_missing_role() -> None:
    service = RoleService(FakeRoleRepository())

    with pytest.raises(NotFoundError, match="Role not found"):
        service.get_role(object(), 999)


def test_role_service_creates_role_through_repository() -> None:
    service = RoleService(FakeRoleRepository())

    role = service.create_role(object(), RoleCreate(name="Usuario", description="Lectores"))

    assert role.id == 2
    assert role.name == "Usuario"
    assert role.description == "Lectores"


def test_roles_router_is_mounted_and_lists_roles() -> None:
    service = RoleService(FakeRoleRepository())

    main.app.dependency_overrides[get_role_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/roles/")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Admin"
    assert "is_active" not in response.json()[0]


def test_roles_router_maps_missing_role_to_404() -> None:
    service = RoleService(FakeRoleRepository())

    main.app.dependency_overrides[get_role_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/roles/999")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Role not found."}
