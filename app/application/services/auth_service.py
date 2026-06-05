"""Application service for authentication workflows."""

from typing import Any

from app.application.errors import ConflictError, InactiveUserError, InvalidCredentialsError
from app.application.ports.user_repository import UserRepository
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import LoginResponse
from app.schemas.users import UserCreate, UserCreateWithHash, UserRead

# Role ID for the default "Usuario" role as seeded in the roles table.
# Centralized here so registration logic has a single place to update if the seed changes.
_DEFAULT_REGISTRATION_ROLE_ID: int = 2


class AuthService:
    """Coordinate authentication use cases."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def authenticate(self, session: Any, username: str, password: str) -> LoginResponse:
        """Validate credentials and return a signed JWT with user profile.

        Raises InvalidCredentialsError if the user does not exist or password is wrong.
        Raises InactiveUserError if the user account is disabled.
        """

        user = self._user_repository.get_by_username(session, username)
        if user is None:
            raise InvalidCredentialsError("Invalid username or password.")

        if user.is_active is False:
            raise InactiveUserError("User account is inactive.")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid username or password.")

        role_name = (user.role.name if user.role else "Usuario").strip()
        token_data = {"sub": str(user.id), "username": user.username, "role": role_name}
        access_token = create_access_token(data=token_data)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserRead.model_validate(user),
        )

    def register(self, session: Any, data: UserCreate) -> UserRead:
        """Create a new user with a hashed password.

        Raises ConflictError if a user with the same username already exists.
        """

        existing = self._user_repository.get_by_username(session, data.username)
        if existing is not None:
            raise ConflictError("Username already registered.")

        # Build an attribute-accessible object so the repository can use dot notation.
        # Using a dict would cause AttributeError in user_repository.create().
        payload = UserCreateWithHash(
            username=data.username,
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password.get_secret_value()),
            is_active=True,
            role_id=_DEFAULT_REGISTRATION_ROLE_ID,
        )
        user = self._user_repository.create(session, payload)
        if user is None:
            raise RuntimeError("User creation succeeded in Oracle but could not be retrieved.")
        return UserRead.model_validate(user)


__all__ = ["AuthService"]
