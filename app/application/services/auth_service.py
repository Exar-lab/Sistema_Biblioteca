"""Application service for authentication workflows."""

from typing import Any

from app.application.errors import InactiveUserError, InvalidCredentialsError
from app.application.ports.user_repository import UserRepository
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import LoginResponse
from app.schemas.users import UserCreate, UserRead


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
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid username or password.")

        if user.is_active is False:
            raise InactiveUserError("User account is inactive.")

        role_name = (user.role.name if user.role else "Usuario").strip()
        token_data = {"sub": str(user.id), "username": user.username, "role": role_name}
        access_token = create_access_token(data=token_data)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserRead.model_validate(user),
        )

    def register(self, session: Any, data: UserCreate) -> UserRead:
        """Create a new user with a hashed password."""

        raw = data.model_dump()
        raw.pop("password", None)
        raw["password_hash"] = hash_password(data.password.get_secret_value())
        user = self._user_repository.create(session, raw)
        return UserRead.model_validate(user)


__all__ = ["AuthService"]
