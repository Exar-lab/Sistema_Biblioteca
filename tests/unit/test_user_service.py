"""Unit tests for UserService.

Tests use MagicMock to isolate the service from the database.
No live Oracle connection is required.

Run with:
    pytest tests/unit/test_user_service.py -v
"""

from unittest.mock import MagicMock, call

import pytest

from app.application.errors import NotFoundError
from app.application.services.user_service import UserService
from app.schemas.users import UserActiveToggle, UserUpdate


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_service(repo: MagicMock) -> UserService:
    return UserService(repo)


def _make_fake_user(
    *,
    user_id: int = 1,
    username: str = "testuser",
    full_name: str = "Test User",
    email: str = "test@example.com",
    phone: str | None = None,
    is_active: bool = True,
    role_id: int = 2,
    password_hash: str = "$2b$12$fakehashvalue",
) -> MagicMock:
    """Return a MagicMock that mimics a User ORM model."""
    user = MagicMock()
    user.id = user_id
    user.username = username
    user.full_name = full_name
    user.email = email
    user.phone = phone
    user.is_active = is_active
    user.role_id = role_id
    user.password_hash = password_hash
    user.role = None
    user.created_at = None
    user.updated_at = None
    return user


# ---------------------------------------------------------------------------
# get_by_id() tests
# ---------------------------------------------------------------------------

class TestUserServiceGetById:
    """UserService.get_by_id() — unit suite."""

    def test_get_by_id_raises_not_found_when_repo_returns_none(self) -> None:
        """NotFoundError is raised when the repository returns None."""
        repo = MagicMock()
        repo.get_by_id.return_value = None

        service = _make_service(repo)

        with pytest.raises(NotFoundError):
            service.get_by_id(MagicMock(), user_id=999)

    def test_get_by_id_returns_user_read_when_found(self) -> None:
        """UserRead is returned when the user exists."""
        repo = MagicMock()
        repo.get_by_id.return_value = _make_fake_user(user_id=7, username="alice")

        service = _make_service(repo)
        result = service.get_by_id(MagicMock(), user_id=7)

        assert result.id == 7
        assert result.username == "alice"

    def test_get_by_id_calls_repo_with_correct_id(self) -> None:
        """repo.get_by_id() is called with the exact user_id provided."""
        repo = MagicMock()
        repo.get_by_id.return_value = _make_fake_user(user_id=42)

        service = _make_service(repo)
        session = MagicMock()
        service.get_by_id(session, user_id=42)

        repo.get_by_id.assert_called_once_with(session, 42)


# ---------------------------------------------------------------------------
# set_active() tests
# ---------------------------------------------------------------------------

class TestUserServiceSetActive:
    """UserService.set_active() — unit suite."""

    def test_set_active_calls_repo_update_with_toggled_is_active(self) -> None:
        """repo.update() is called with the is_active flag set to the new value."""
        repo = MagicMock()
        existing_user = _make_fake_user(user_id=5, is_active=True)
        updated_user = _make_fake_user(user_id=5, is_active=False)

        repo.get_by_id.return_value = existing_user
        repo.update.return_value = updated_user

        service = _make_service(repo)
        session = MagicMock()
        result = service.set_active(session, user_id=5, is_active=False)

        # Verify update() was called once.
        repo.update.assert_called_once()
        _, update_call_args = repo.update.call_args.args[0], repo.update.call_args.args
        data_payload = repo.update.call_args.args[2]  # (session, user_id, payload)

        assert data_payload.is_active is False, "Payload must carry the new is_active value"
        assert result.is_active is False

    def test_set_active_activate_user(self) -> None:
        """set_active(True) calls repo.update() with is_active=True."""
        repo = MagicMock()
        existing_user = _make_fake_user(user_id=3, is_active=False)
        updated_user = _make_fake_user(user_id=3, is_active=True)

        repo.get_by_id.return_value = existing_user
        repo.update.return_value = updated_user

        service = _make_service(repo)
        result = service.set_active(MagicMock(), user_id=3, is_active=True)

        data_payload = repo.update.call_args.args[2]
        assert data_payload.is_active is True
        assert result.is_active is True

    def test_set_active_raises_not_found_when_user_missing(self) -> None:
        """NotFoundError is raised when the user does not exist."""
        repo = MagicMock()
        repo.get_by_id.return_value = None

        service = _make_service(repo)

        with pytest.raises(NotFoundError):
            service.set_active(MagicMock(), user_id=999, is_active=False)

        repo.update.assert_not_called()

    def test_set_active_preserves_other_user_fields(self) -> None:
        """The payload passed to repo.update() carries all other fields unchanged."""
        repo = MagicMock()
        existing_user = _make_fake_user(
            user_id=10,
            username="preserved_user",
            full_name="Preserved User",
            email="preserved@example.com",
            phone="555-1234",
            is_active=True,
            role_id=3,
            password_hash="$2b$12$existinghash",
        )
        repo.get_by_id.return_value = existing_user
        repo.update.return_value = _make_fake_user(user_id=10, is_active=False)

        service = _make_service(repo)
        service.set_active(MagicMock(), user_id=10, is_active=False)

        payload = repo.update.call_args.args[2]
        assert payload.username == "preserved_user"
        assert payload.full_name == "Preserved User"
        assert payload.email == "preserved@example.com"
        assert payload.phone == "555-1234"
        assert payload.password_hash == "$2b$12$existinghash"
        assert payload.role_id == 3
