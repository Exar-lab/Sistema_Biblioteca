"""Tests for JWT authentication dependencies and routes."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient

import main
from app.api import dependencies
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
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FakeUserRepository:
    def __init__(self, user: UserStub | None) -> None:
        self.user = user

    def get_by_id(self, _session: Any, id: int) -> UserStub | None:
        if self.user is not None and self.user.id == id:
            return self.user
        return None


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
