"""Unit tests for UserRepository — no live Oracle required."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select

from app.domain.models.user import LibraryUser
from app.infrastructure.repositories.user_repository import UserRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture()
def fake_user() -> LibraryUser:
    u = LibraryUser()
    u.id = 5
    u.username = "jdoe"
    u.full_name = "John Doe"
    u.email = "jdoe@example.com"
    u.phone = "555-1234"
    u.password_hash = "hashed_pw"
    u.is_active = True
    u.role_id = 1
    return u


@pytest.fixture()
def fake_create_data() -> MagicMock:
    d = MagicMock()
    d.username = "jdoe"
    d.full_name = "John Doe"
    d.email = "jdoe@example.com"
    d.phone = "555-1234"
    d.password_hash = "hashed_pw"
    d.is_active = True
    d.role_id = 1
    return d


@pytest.fixture()
def fake_update_data() -> MagicMock:
    d = MagicMock()
    d.username = "jdoe_updated"
    d.full_name = "John Updated Doe"
    d.email = "jdoe_new@example.com"
    d.phone = "555-9999"
    d.password_hash = "new_hash"
    d.is_active = True
    d.role_id = 2
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_cursor(mock_session: MagicMock, out_value: int = 5) -> MagicMock:
    mock_cursor = MagicMock()
    out_var = MagicMock()
    out_var.getvalue.return_value = out_value
    mock_cursor.var.return_value = out_var

    cursor_cm = MagicMock()
    cursor_cm.__enter__ = MagicMock(return_value=mock_cursor)
    cursor_cm.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cursor_cm
    mock_session.connection.return_value.connection = mock_conn

    return mock_cursor


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


def test_create_calls_p_insert_and_returns_id(
    mock_session: MagicMock,
    fake_user: LibraryUser,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=5)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_user

    repo = UserRepository()
    result = repo.create(mock_session, fake_create_data)

    mock_cursor.callproc.assert_called_once()
    proc_name = mock_cursor.callproc.call_args[0][0]
    assert "pkg_library_users.p_insert" in proc_name
    assert result.id == 5


def test_create_binds_correct_params(
    mock_session: MagicMock,
    fake_user: LibraryUser,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=5)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_user

    repo = UserRepository()
    repo.create(mock_session, fake_create_data)

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert bind_args == [
        fake_create_data.username,
        fake_create_data.full_name,
        fake_create_data.email,
        fake_create_data.phone,
        fake_create_data.password_hash,
        fake_create_data.is_active,
        fake_create_data.role_id,
        mock_cursor.var.return_value,
    ]


def test_create_no_commit(
    mock_session: MagicMock,
    fake_user: LibraryUser,
    fake_create_data: MagicMock,
) -> None:
    _setup_cursor(mock_session, out_value=5)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_user

    repo = UserRepository()
    repo.create(mock_session, fake_create_data)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


def test_update_calls_p_update(
    mock_session: MagicMock,
    fake_user: LibraryUser,
    fake_update_data: MagicMock,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_user

    repo = UserRepository()
    repo.update(mock_session, 5, fake_update_data)

    assert mock_session.execute.called
    first_call = mock_session.execute.call_args_list[0]
    sql_text = str(first_call[0][0])
    assert "p_update" in sql_text
    binds = first_call[0][1]
    assert binds["p_id"] == 5


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


def test_delete_returns_true_on_success(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = UserRepository()
    assert repo.delete(mock_session, 5) is True


def test_delete_returns_false_on_not_found(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=0)

    repo = UserRepository()
    assert repo.delete(mock_session, 999) is False


def test_delete_no_commit(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = UserRepository()
    repo.delete(mock_session, 5)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------


def test_get_by_id_uses_select(mock_session: MagicMock, fake_user: LibraryUser) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_user

    repo = UserRepository()
    result = repo.get_by_id(mock_session, 5)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert result is fake_user


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------


def test_list_all_uses_select_no_where(mock_session: MagicMock, fake_user: LibraryUser) -> None:
    mock_session.execute.return_value.scalars.return_value.all.return_value = [fake_user]

    repo = UserRepository()
    results = repo.list_all(mock_session)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert results == [fake_user]
