"""Unit tests for RoleService.

Uses a plain in-memory fake repository — zero SQLAlchemy / Oracle dependency.
The fake mirrors the actual calling convention used in role_service.py where
the session is passed as the first positional argument to every repo method.
"""

import pytest

from app.application.errors import NotFoundError
from app.application.services.role_service import RoleService


# ---------------------------------------------------------------------------
# Fake / in-memory repository
# ---------------------------------------------------------------------------

class _FakeRole:
    """Minimal stand-in for a Role ORM instance."""

    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name


class _FakeRoleRepository:
    """In-memory role store that satisfies the calling contract of RoleService.

    RoleService calls: repo.get_by_id(session, id)  / repo.create(session, data)
    The Protocol signature omits session, but the service adds it — so the fake
    accepts it (and ignores it) to avoid TypeError.
    """

    def __init__(self, roles: list[_FakeRole] | None = None) -> None:
        self._store: dict[int, _FakeRole] = {r.id: r for r in (roles or [])}
        self.create_call_count = 0
        self.last_create_data: object = None

    def get_by_id(self, session: object, id: int) -> _FakeRole | None:  # noqa: A002
        return self._store.get(id)

    def list_all(self, session: object) -> list[_FakeRole]:
        return list(self._store.values())

    def create(self, session: object, data: object) -> _FakeRole:
        self.create_call_count += 1
        self.last_create_data = data
        # Build a minimal role from the data dict
        role_id = len(self._store) + 1
        name = data.get("name", "role") if isinstance(data, dict) else "role"
        new_role = _FakeRole(id=role_id, name=name)
        self._store[role_id] = new_role
        return new_role

    def update(self, session: object, id: int, data: object) -> _FakeRole | None:  # noqa: A002
        role = self._store.get(id)
        if role is None:
            return None
        if isinstance(data, dict):
            for k, v in data.items():
                setattr(role, k, v)
        return role

    def delete(self, session: object, id: int) -> bool:  # noqa: A002
        if id in self._store:
            del self._store[id]
            return True
        return False


# ---------------------------------------------------------------------------
# Sentinel for a fake session — the service just passes it through
# ---------------------------------------------------------------------------

_FAKE_SESSION = object()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRoleServiceGet:
    def test_returns_entity_when_found(self) -> None:
        role = _FakeRole(id=1, name="admin")
        service = RoleService(repo=_FakeRoleRepository(roles=[role]))

        result = service.get(_FAKE_SESSION, 1)

        assert result is role

    def test_raises_not_found_when_missing(self) -> None:
        service = RoleService(repo=_FakeRoleRepository(roles=[]))

        with pytest.raises(NotFoundError):
            service.get(_FAKE_SESSION, 99)

    def test_not_found_message_contains_id(self) -> None:
        service = RoleService(repo=_FakeRoleRepository(roles=[]))

        with pytest.raises(NotFoundError, match="99"):
            service.get(_FAKE_SESSION, 99)


class TestRoleServiceCreate:
    def test_delegates_to_repo_create_exactly_once(self) -> None:
        fake_repo = _FakeRoleRepository()
        service = RoleService(repo=fake_repo)
        data = {"name": "editor"}

        service.create(_FAKE_SESSION, data)

        assert fake_repo.create_call_count == 1

    def test_passes_data_to_repo_unchanged(self) -> None:
        fake_repo = _FakeRoleRepository()
        service = RoleService(repo=fake_repo)
        data = {"name": "viewer"}

        service.create(_FAKE_SESSION, data)

        assert fake_repo.last_create_data is data

    def test_returns_repo_result(self) -> None:
        fake_repo = _FakeRoleRepository()
        service = RoleService(repo=fake_repo)

        result = service.create(_FAKE_SESSION, {"name": "reader"})

        assert isinstance(result, _FakeRole)
        assert result.name == "reader"
