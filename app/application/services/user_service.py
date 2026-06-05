"""Application service for user management workflows."""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.user_repository import UserRepository
from app.core.security import hash_password
from app.schemas.users import UserActiveToggle, UserRead, UserUpdate


class UserService:
    """Coordinate user CRUD use cases.

    All writes go through the repository layer (stored procedures).
    Reads use the ORM SELECT path. The service never exposes password or password_hash.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_all(self, session: Any) -> list[UserRead]:
        """Return all users as UserRead objects."""

        users = self._user_repository.list_all(session)
        return [UserRead.model_validate(u) for u in users]

    def get_by_id(self, session: Any, user_id: int) -> UserRead:
        """Return a single user.

        Raises NotFoundError if no user with *user_id* exists.
        """

        user = self._user_repository.get_by_id(session, user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return UserRead.model_validate(user)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def update(self, session: Any, user_id: int, data: UserUpdate) -> UserRead:
        """Partially update a user.

        Fields not provided in *data* are kept unchanged from the current record.
        If *data.password* is set, it is hashed before being forwarded to the repository.
        Raises NotFoundError if the user does not exist.
        """

        current = self._user_repository.get_by_id(session, user_id)
        if current is None:
            raise NotFoundError("User not found.")

        # Build an attribute-accessible payload that the repository update() can dot-access.
        # Merge: use incoming value if provided, otherwise fall back to the current record.
        payload = _UpdatePayload(
            username=data.username if data.username is not None else current.username,
            full_name=data.full_name if data.full_name is not None else current.full_name,
            email=data.email if data.email is not None else current.email,
            phone=data.phone if data.phone is not None else current.phone,
            password_hash=(
                hash_password(data.password.get_secret_value())
                if data.password is not None
                else current.password_hash
            ),
            is_active=data.is_active if data.is_active is not None else current.is_active,
            role_id=data.role_id if data.role_id is not None else current.role_id,
        )
        updated = self._user_repository.update(session, user_id, payload)
        if updated is None:
            raise NotFoundError("User not found.")
        return UserRead.model_validate(updated)

    def set_active(self, session: Any, user_id: int, is_active: bool) -> UserRead:
        """Toggle the active state of a user.

        Raises NotFoundError if the user does not exist.
        """

        current = self._user_repository.get_by_id(session, user_id)
        if current is None:
            raise NotFoundError("User not found.")

        payload = _UpdatePayload(
            username=current.username,
            full_name=current.full_name,
            email=current.email,
            phone=current.phone,
            password_hash=current.password_hash,
            is_active=is_active,
            role_id=current.role_id,
        )
        updated = self._user_repository.update(session, user_id, payload)
        if updated is None:
            raise NotFoundError("User not found.")
        return UserRead.model_validate(updated)


class _UpdatePayload:
    """Lightweight attribute carrier for repository update calls.

    UserRepository.update() accesses all fields via dot notation.  This class
    bridges the gap between optional Pydantic update schemas and the fully-
    populated object the stored-procedure wrapper expects.
    """

    __slots__ = ("username", "full_name", "email", "phone", "password_hash", "is_active", "role_id")

    def __init__(
        self,
        *,
        username: str,
        full_name: str,
        email: str,
        phone: str | None,
        password_hash: str,
        is_active: bool,
        role_id: int | None,
    ) -> None:
        self.username = username
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.password_hash = password_hash
        self.is_active = is_active
        self.role_id = role_id


# Module-level singleton — mirrors the pattern used by AuthService and BookService.
from app.infrastructure.repositories.user_repository import user_repository as _user_repo  # noqa: E402

user_service = UserService(_user_repo)

__all__ = ["UserService", "user_service"]
