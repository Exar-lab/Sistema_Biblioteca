"""Regression tests for health endpoint and DB session lifecycle."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1",
)

import main  # noqa: E402
from app.core import database  # noqa: E402


class _FakeContextSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def test_health_returns_503_when_db_down(monkeypatch: pytest.MonkeyPatch) -> None:
    """Health endpoint should expose the agreed DB-down contract."""

    def _raise_db_error(_db):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(main, "SessionLocal", lambda: _FakeContextSession())
    monkeypatch.setattr(main, "run_db_smoke_check", _raise_db_error)

    response = TestClient(main.app).get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "down"}


def test_health_returns_200_when_db_up_simulated(monkeypatch: pytest.MonkeyPatch) -> None:
    """Health endpoint should return 200 when smoke check succeeds."""

    monkeypatch.setattr(main, "SessionLocal", lambda: _FakeContextSession())
    monkeypatch.setattr(main, "run_db_smoke_check", lambda _db: None)

    response = TestClient(main.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


class _FakeLifecycleSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


def test_get_db_commits_and_closes_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_db should commit and close when consumer finishes normally."""

    fake_session = _FakeLifecycleSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: fake_session)

    generator = database.get_db()
    yielded = next(generator)

    assert yielded is fake_session

    with pytest.raises(StopIteration):
        next(generator)

    assert fake_session.committed is True
    assert fake_session.rolled_back is False
    assert fake_session.closed is True


def test_get_db_rolls_back_and_closes_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_db should rollback and close when consumer throws an error."""

    fake_session = _FakeLifecycleSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: fake_session)

    generator = database.get_db()
    next(generator)

    with pytest.raises(RuntimeError, match="boom"):
        generator.throw(RuntimeError("boom"))

    assert fake_session.committed is False
    assert fake_session.rolled_back is True
    assert fake_session.closed is True
