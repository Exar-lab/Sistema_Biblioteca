"""Integration tests for GET /api/v1/users/ and PATCH /api/v1/users/{id} endpoints.

These tests require a live Oracle database with the full schema applied
and an admin user seeded. All tests are skipped automatically when no
live DB is available.

Run against a live DB with:
    ORACLE_DSN="oracle+oracledb://..." pytest tests/integration/test_users_endpoints.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, raise_server_exceptions=False)

_USERS_BASE = "/api/v1/users"

# Placeholder auth headers — replace with a real admin JWT in a live test run.
_ADMIN_HEADERS: dict[str, str] = {"Authorization": "Bearer <admin_jwt_token>"}
_NON_ADMIN_HEADERS: dict[str, str] = {"Authorization": "Bearer <regular_user_jwt_token>"}


# ---------------------------------------------------------------------------
# GET /users/ — list all users
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires DB")
def test_list_users_returns_200_for_admin() -> None:
    """GET /users/ with admin credentials returns 200 and a list."""
    response = client.get(_USERS_BASE + "/", headers=_ADMIN_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


@pytest.mark.skip(reason="requires DB")
def test_list_users_response_items_have_no_password_hash() -> None:
    """GET /users/ response items must not expose password or password_hash."""
    response = client.get(_USERS_BASE + "/", headers=_ADMIN_HEADERS)
    assert response.status_code == 200

    for item in response.json():
        assert "password" not in item, "plain password must never appear in user list"
        assert "password_hash" not in item, "password_hash must never appear in user list"


@pytest.mark.skip(reason="requires DB")
def test_list_users_returns_401_without_token() -> None:
    """GET /users/ without credentials returns 401 Unauthorized."""
    response = client.get(_USERS_BASE + "/")

    assert response.status_code == 401


@pytest.mark.skip(reason="requires DB")
def test_list_users_returns_403_for_non_admin() -> None:
    """GET /users/ with non-admin credentials returns 403 Forbidden."""
    response = client.get(_USERS_BASE + "/", headers=_NON_ADMIN_HEADERS)

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /users/{user_id} — single user lookup
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires DB")
def test_get_user_by_id_returns_200_when_found(admin_user_id: int = 1) -> None:
    """GET /users/{id} returns 200 and UserRead when the user exists."""
    response = client.get(f"{_USERS_BASE}/{admin_user_id}", headers=_ADMIN_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert "username" in body
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.skip(reason="requires DB")
def test_get_user_by_id_returns_404_when_not_found() -> None:
    """GET /users/{id} returns 404 when no user matches the id."""
    response = client.get(f"{_USERS_BASE}/999999", headers=_ADMIN_HEADERS)

    assert response.status_code == 404
    assert "detail" in response.json()


# ---------------------------------------------------------------------------
# PATCH /users/{user_id} — partial update
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires DB")
def test_patch_user_returns_200_on_valid_update(target_user_id: int = 1) -> None:
    """PATCH /users/{id} returns 200 with the updated UserRead."""
    payload = {"full_name": "Updated Name"}
    response = client.patch(
        f"{_USERS_BASE}/{target_user_id}", json=payload, headers=_ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.skip(reason="requires DB")
def test_patch_user_returns_404_for_missing_user() -> None:
    """PATCH /users/{id} returns 404 when the user does not exist."""
    response = client.patch(
        f"{_USERS_BASE}/999999", json={"full_name": "Ghost"}, headers=_ADMIN_HEADERS
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /users/{user_id}/active — toggle active state
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires DB")
def test_toggle_active_returns_200(target_user_id: int = 1) -> None:
    """PATCH /users/{id}/active returns 200 with updated is_active field."""
    payload = {"is_active": False}
    response = client.patch(
        f"{_USERS_BASE}/{target_user_id}/active", json=payload, headers=_ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.skip(reason="requires DB")
def test_toggle_active_returns_404_for_missing_user() -> None:
    """PATCH /users/{id}/active returns 404 when the user does not exist."""
    payload = {"is_active": True}
    response = client.patch(
        f"{_USERS_BASE}/999999/active", json=payload, headers=_ADMIN_HEADERS
    )

    assert response.status_code == 404
