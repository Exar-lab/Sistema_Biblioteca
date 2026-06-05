"""Unit tests for AuthService.register().

These tests use MagicMock to isolate the service from the database.
No live Oracle connection is required.

Run with:
    pytest tests/unit/test_auth_service_register.py -v
"""

from unittest.mock import MagicMock

import pytest

from app.application.errors import ConflictError
from app.application.services.auth_service import AuthService
from app.schemas.users import UserCreate, UserCreateWithHash


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_service(repo: MagicMock) -> AuthService:
    return AuthService(repo)


def _make_user_create(
    *,
    username: str = "johndoe",
    full_name: str = "John Doe",
    email: str = "john@example.com",
    password: str = "secret1234",
) -> UserCreate:
    return UserCreate(
        username=username,
        full_name=full_name,
        email=email,
        password=password,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAuthServiceRegister:
    """AuthService.register() — unit suite."""

    def test_register_passes_object_with_password_hash_attribute(self) -> None:
        """Repo.create() receives an object (not a dict) with .password_hash."""
        repo = MagicMock()
        repo.get_by_username.return_value = None  # no duplicate

        # Repo.create() returns a user-like object with expected fields.
        fake_user = MagicMock()
        fake_user.id = 1
        fake_user.username = "johndoe"
        fake_user.full_name = "John Doe"
        fake_user.email = "john@example.com"
        fake_user.phone = None
        fake_user.is_active = True
        fake_user.role_id = 2
        fake_user.role = None
        fake_user.created_at = None
        fake_user.updated_at = None
        repo.create.return_value = fake_user

        service = _make_service(repo)
        session = MagicMock()
        payload = _make_user_create()

        service.register(session, payload)

        # Verify create() was called once.
        repo.create.assert_called_once()
        _, call_args = repo.create.call_args
        # Second positional arg is the data object.
        positional_args = repo.create.call_args.args
        data_arg = positional_args[1]  # (session, data)

        # Must be an object with attribute access — NOT a plain dict.
        assert not isinstance(data_arg, dict), "create() must receive an object, not a dict"
        assert hasattr(data_arg, "password_hash"), "data must expose .password_hash attribute"
        assert hasattr(data_arg, "username"), "data must expose .username attribute"
        assert not hasattr(data_arg, "password") or data_arg.password_hash, (
            "plain-text password must not be the primary credential on the payload"
        )

    def test_register_hashes_password_before_persisting(self) -> None:
        """password_hash must differ from the plain-text password."""
        repo = MagicMock()
        repo.get_by_username.return_value = None

        fake_user = MagicMock()
        fake_user.id = 1
        fake_user.username = "johndoe"
        fake_user.full_name = "John Doe"
        fake_user.email = "john@example.com"
        fake_user.phone = None
        fake_user.is_active = True
        fake_user.role_id = 2
        fake_user.role = None
        fake_user.created_at = None
        fake_user.updated_at = None
        repo.create.return_value = fake_user

        service = _make_service(repo)
        plain_password = "plainpassword99"
        payload = _make_user_create(password=plain_password)

        service.register(MagicMock(), payload)

        data_arg = repo.create.call_args.args[1]
        assert data_arg.password_hash != plain_password, (
            "password_hash must be the bcrypt hash, not the plain text password"
        )
        # Bcrypt hashes start with $2b$
        assert data_arg.password_hash.startswith("$2b$"), (
            "password_hash must be a valid bcrypt hash"
        )

    def test_register_returns_user_out_compatible_object(self) -> None:
        """register() returns a UserRead-compatible object without password fields."""
        repo = MagicMock()
        repo.get_by_username.return_value = None

        fake_user = MagicMock()
        fake_user.id = 42
        fake_user.username = "janedoe"
        fake_user.full_name = "Jane Doe"
        fake_user.email = "jane@example.com"
        fake_user.phone = None
        fake_user.is_active = True
        fake_user.role_id = 2
        fake_user.role = None
        fake_user.created_at = None
        fake_user.updated_at = None
        repo.create.return_value = fake_user

        service = _make_service(repo)
        result = service.register(MagicMock(), _make_user_create(username="janedoe", email="jane@example.com"))

        # Must return a UserRead — has id, username, no password field.
        assert result.id == 42
        assert result.username == "janedoe"
        assert not hasattr(result, "password"), "UserRead must not expose plain password"
        assert not hasattr(result, "password_hash"), "UserRead must not expose password_hash"

    def test_register_raises_conflict_error_on_duplicate_username(self) -> None:
        """register() raises ConflictError when the username already exists."""
        repo = MagicMock()

        # Simulate an existing user found by get_by_username.
        existing_user = MagicMock()
        existing_user.username = "johndoe"
        repo.get_by_username.return_value = existing_user

        service = _make_service(repo)
        session = MagicMock()

        with pytest.raises(ConflictError):
            service.register(session, _make_user_create())

        # create() must NOT be called when a duplicate is detected.
        repo.create.assert_not_called()

    def test_register_checks_username_before_creating(self) -> None:
        """get_by_username() is called before create() — guard runs first."""
        repo = MagicMock()
        repo.get_by_username.return_value = None

        fake_user = MagicMock()
        fake_user.id = 1
        fake_user.username = "newuser"
        fake_user.full_name = "New User"
        fake_user.email = "new@example.com"
        fake_user.phone = None
        fake_user.is_active = True
        fake_user.role_id = 2
        fake_user.role = None
        fake_user.created_at = None
        fake_user.updated_at = None
        repo.create.return_value = fake_user

        call_order: list[str] = []
        repo.get_by_username.side_effect = lambda *_: (call_order.append("get_by_username"), None)[1]
        repo.create.side_effect = lambda *_: (call_order.append("create"), fake_user)[1]

        service = _make_service(repo)
        service.register(MagicMock(), _make_user_create(username="newuser", email="new@example.com"))

        assert call_order.index("get_by_username") < call_order.index("create"), (
            "duplicate check must happen before create()"
        )
