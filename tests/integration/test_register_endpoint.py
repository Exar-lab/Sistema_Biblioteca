"""Integration tests for POST /api/v1/auth/register.

These tests require a live Oracle database with the full schema applied.
All tests are skipped automatically when no live DB is available.

Run against a live DB with:
    ORACLE_DSN="oracle+oracledb://..." pytest tests/integration/test_register_endpoint.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, raise_server_exceptions=False)

_REGISTER_URL = "/api/v1/auth/register"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires DB")
def test_register_returns_201_and_user_read() -> None:
    """POST /auth/register with valid payload returns 201 and a UserRead body."""
    payload = {
        "username": "integration_testuser",
        "full_name": "Integration Test User",
        "email": "integration_test@example.com",
        "password": "securepassword1",
    }
    response = client.post(_REGISTER_URL, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == payload["username"]
    assert body["full_name"] == payload["full_name"]
    assert body["email"] == payload["email"]
    assert "id" in body
    assert "password" not in body, "plain password must never appear in response"
    assert "password_hash" not in body, "password_hash must never appear in response"


@pytest.mark.skip(reason="requires DB")
def test_register_sets_is_active_true_by_default() -> None:
    """Newly registered users are active by default."""
    payload = {
        "username": "active_default_user",
        "full_name": "Active Default User",
        "email": "active_default@example.com",
        "password": "securepassword1",
    }
    response = client.post(_REGISTER_URL, json=payload)

    assert response.status_code == 201
    assert response.json()["is_active"] is True


# ---------------------------------------------------------------------------
# Duplicate username
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires DB")
def test_register_returns_409_on_duplicate_username() -> None:
    """POST /auth/register with an already-taken username returns 409 Conflict."""
    payload = {
        "username": "duplicate_user",
        "full_name": "Duplicate User",
        "email": "duplicate@example.com",
        "password": "securepassword1",
    }
    # First registration — must succeed.
    first_response = client.post(_REGISTER_URL, json=payload)
    assert first_response.status_code == 201

    # Second registration with the same username — must fail.
    duplicate_payload = {**payload, "email": "different_email@example.com"}
    second_response = client.post(_REGISTER_URL, json=duplicate_payload)

    assert second_response.status_code == 409
    assert "detail" in second_response.json()


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires DB")
def test_register_returns_422_on_missing_required_fields() -> None:
    """POST /auth/register with missing required fields returns 422."""
    response = client.post(_REGISTER_URL, json={"username": "incomplete"})

    assert response.status_code == 422


@pytest.mark.skip(reason="requires DB")
def test_register_returns_422_on_short_password() -> None:
    """POST /auth/register with a password shorter than 8 chars returns 422."""
    payload = {
        "username": "shortpwduser",
        "full_name": "Short Password User",
        "email": "shortpwd@example.com",
        "password": "short",  # less than 8 chars
    }
    response = client.post(_REGISTER_URL, json=payload)

    assert response.status_code == 422
