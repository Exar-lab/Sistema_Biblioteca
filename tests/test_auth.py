"""Tests for JWT authentication dependencies and routes."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient

import main
from app.api import dependencies
from app.api.v1.routers.auth import get_auth_service
from app.application.services.auth_service import AuthService
from app.core.security import hash_password
from app.core.database import get_db


@dataclass
class RoleStub:
    id: int = 1
    name: str = "Admin"
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class UserStub:
    id: int = 1
    username: str = "admin"
    full_name: str = "Admin User"
    email: str = "admin@example.com"
    phone: str | None = None
    is_active: bool = True
    role_id: int = 1
    role: RoleStub | None = None
    password_hash: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FakeUserRepository:
    def __init__(self, user: UserStub | None) -> None:
        self.user = user

    def get_by_id(self, _session: Any, id: int) -> UserStub | None:
        if self.user is not None and self.user.id == id:
            return self.user
        return None


class FakePasswordRepository(FakeUserRepository):
    def update(self, _session: Any, id: int, data: Any) -> UserStub | None:
        if self.user is None or self.user.id != id:
            return None

        self.user.username = data.username
        self.user.full_name = data.full_name
        self.user.email = data.email
        self.user.phone = data.phone
        self.user.is_active = data.is_active
        self.user.role_id = data.role_id
        self.user.password_hash = data.password_hash
        return self.user


def _client_with_auth_repo(monkeypatch: Any, payload: dict | None, user: UserStub | None = None) -> TestClient:
    monkeypatch.setattr(dependencies, "decode_token", lambda _token: payload)
    monkeypatch.setattr(dependencies, "user_repository", FakeUserRepository(user))
    main.app.dependency_overrides[get_db] = lambda: object()
    return TestClient(main.app)


def test_me_returns_401_when_token_payload_is_missing_subject(monkeypatch: Any) -> None:
    client = _client_with_auth_repo(monkeypatch, {"username": "admin"})
    try:
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token"})
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token."}


def test_me_returns_401_for_invalid_token_with_real_decoder(monkeypatch: Any) -> None:
    monkeypatch.setattr(dependencies, "user_repository", FakeUserRepository(UserStub(role=RoleStub())))
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token."}


def test_me_returns_401_when_token_subject_is_not_an_integer(monkeypatch: Any) -> None:
    client = _client_with_auth_repo(monkeypatch, {"sub": "not-a-number"})
    try:
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token"})
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token."}


def test_me_returns_current_user_for_valid_token_subject(monkeypatch: Any) -> None:
    client = _client_with_auth_repo(monkeypatch, {"sub": "1"}, UserStub(role=RoleStub()))
    try:
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token"})
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert response.json()["role"]["name"] == "Admin"


def test_me_returns_403_for_inactive_user(monkeypatch: Any) -> None:
    client = _client_with_auth_repo(monkeypatch, {"sub": "1"}, UserStub(role=RoleStub(), is_active=False))
    try:
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token"})
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "User account is inactive."}


def test_register_rejects_public_role_and_active_fields() -> None:
    payload = {
        "username": "newuser",
        "full_name": "New User",
        "email": "newuser@example.com",
        "password": "secret1234",
        "role_id": 1,
        "is_active": False,
    }

    response = TestClient(main.app).post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422


def test_change_password_returns_updated_user(monkeypatch: Any) -> None:
    user = UserStub(role=RoleStub())
    user.password_hash = hash_password("secret123")
    repo = FakePasswordRepository(user)
    client = _client_with_auth_repo(monkeypatch, {"sub": "1"}, user)
    main.app.dependency_overrides[get_auth_service] = lambda: AuthService(repo)
    try:
        response = client.patch(
            "/api/v1/auth/me/password",
            headers={"Authorization": "Bearer token"},
            json={"current_password": "secret123", "new_password": "newsecret123"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
