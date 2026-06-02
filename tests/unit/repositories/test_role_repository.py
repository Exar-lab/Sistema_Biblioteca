"""Unit tests for RoleRepository — no live Oracle required."""

from unittest.mock import MagicMock, call

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select

from app.domain.models.role import Role
from app.infrastructure.repositories.role_repository import RoleRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_session() -> MagicMock:
    """Fresh MagicMock-based Session for each test."""
    return MagicMock(spec=Session)


@pytest.fixture()
def fake_role() -> Role:
    """A minimal Role instance with predictable field values."""
    r = Role()
    r.id = 42
    r.name = "librarian"
    r.description = "Library staff role"
    return r


@pytest.fixture()
def fake_create_data() -> MagicMock:
    """Data object passed to create()."""
    d = MagicMock()
    d.name = "librarian"
    d.description = "Library staff role"
    return d


@pytest.fixture()
def fake_update_data() -> MagicMock:
    """Data object passed to update()."""
    d = MagicMock()
    d.name = "senior librarian"
    d.description = "Updated role"
    return d


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


def _setup_cursor_for_create(mock_session: MagicMock, out_value: int = 42) -> MagicMock:
    """Wire up the cursor mock chain used by create() and delete()."""
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


def test_create_calls_p_insert_and_returns_id(
    mock_session: MagicMock,
    fake_role: Role,
    fake_create_data: MagicMock,
) -> None:
    """create() must call pkg_roles.p_insert via callproc and return entity with new id."""
    mock_cursor = _setup_cursor_for_create(mock_session, out_value=42)
    # ORM get_by_id path after expire_all
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_role

    repo = RoleRepository()
    result = repo.create(mock_session, fake_create_data)

    mock_cursor.callproc.assert_called_once()
    proc_name = mock_cursor.callproc.call_args[0][0]
    assert "pkg_roles.p_insert" in proc_name

    assert result.id == 42


def test_create_binds_correct_params(
    mock_session: MagicMock,
    fake_role: Role,
    fake_create_data: MagicMock,
) -> None:
    """create() must pass name and description in the callproc bind list."""
    mock_cursor = _setup_cursor_for_create(mock_session, out_value=42)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_role

    repo = RoleRepository()
    repo.create(mock_session, fake_create_data)

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert fake_create_data.name in bind_args
    assert fake_create_data.description in bind_args


def test_create_no_commit(
    mock_session: MagicMock,
    fake_role: Role,
    fake_create_data: MagicMock,
) -> None:
    """create() must NOT call session.commit."""
    _setup_cursor_for_create(mock_session, out_value=42)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_role

    repo = RoleRepository()
    repo.create(mock_session, fake_create_data)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


def test_update_calls_p_update(
    mock_session: MagicMock,
    fake_role: Role,
    fake_update_data: MagicMock,
) -> None:
    """update() must call session.execute with SQL text containing pkg_roles.p_update."""
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_role

    repo = RoleRepository()
    repo.update(mock_session, 42, fake_update_data)

    assert mock_session.execute.called
    first_call = mock_session.execute.call_args_list[0]
    sql_text = str(first_call[0][0])
    assert "p_update" in sql_text

    binds = first_call[0][1]
    assert binds["p_id"] == 42


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


def _setup_cursor_for_delete(mock_session: MagicMock, found: bool = True) -> MagicMock:
    mock_cursor = MagicMock()
    out_var = MagicMock()
    out_var.getvalue.return_value = 1 if found else 0
    mock_cursor.var.return_value = out_var

    cursor_cm = MagicMock()
    cursor_cm.__enter__ = MagicMock(return_value=mock_cursor)
    cursor_cm.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cursor_cm
    mock_session.connection.return_value.connection = mock_conn

    return mock_cursor


def test_delete_returns_true_on_success(mock_session: MagicMock) -> None:
    """delete() must return True when p_delete OUT param == 1."""
    _setup_cursor_for_delete(mock_session, found=True)

    repo = RoleRepository()
    assert repo.delete(mock_session, 42) is True


def test_delete_returns_false_on_not_found(mock_session: MagicMock) -> None:
    """delete() must return False when p_delete OUT param == 0."""
    _setup_cursor_for_delete(mock_session, found=False)

    repo = RoleRepository()
    assert repo.delete(mock_session, 999) is False


def test_delete_no_commit(mock_session: MagicMock) -> None:
    """delete() must NOT call session.commit."""
    _setup_cursor_for_delete(mock_session, found=True)

    repo = RoleRepository()
    repo.delete(mock_session, 42)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------


def test_get_by_id_uses_select(mock_session: MagicMock, fake_role: Role) -> None:
    """get_by_id() must issue a SQLAlchemy Select, not a TextClause."""
    from sqlalchemy.sql.selectable import Select

    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_role

    repo = RoleRepository()
    result = repo.get_by_id(mock_session, 42)

    assert mock_session.execute.called
    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert result is fake_role


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------


def test_list_all_uses_select_no_where(mock_session: MagicMock, fake_role: Role) -> None:
    """list_all() must issue a Select and return all mocked rows."""
    from sqlalchemy.sql.selectable import Select

    mock_session.execute.return_value.scalars.return_value.all.return_value = [fake_role]

    repo = RoleRepository()
    results = repo.list_all(mock_session)

    assert mock_session.execute.called
    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert results == [fake_role]
