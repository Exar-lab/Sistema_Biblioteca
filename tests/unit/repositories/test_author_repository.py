"""Unit tests for AuthorRepository — no live Oracle required."""

import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select

from app.domain.models.author import Author
from app.infrastructure.repositories.author_repository import AuthorRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture()
def fake_author() -> Author:
    a = Author()
    a.id = 7
    a.first_name = "Gabriel"
    a.last_name = "Garcia Marquez"
    a.biography = "Colombian novelist"
    a.birth_date = datetime.date(1927, 3, 6)
    a.death_date = datetime.date(2014, 4, 17)
    a.is_active = True
    return a


@pytest.fixture()
def fake_create_data() -> MagicMock:
    d = MagicMock()
    d.first_name = "Gabriel"
    d.last_name = "Garcia Marquez"
    d.biography = "Colombian novelist"
    d.birth_date = datetime.date(1927, 3, 6)
    d.death_date = datetime.date(2014, 4, 17)
    d.is_active = True
    return d


@pytest.fixture()
def fake_update_data() -> MagicMock:
    d = MagicMock()
    d.first_name = "Gabriel"
    d.last_name = "Garcia Marquez"
    d.biography = "Updated bio"
    d.birth_date = datetime.date(1927, 3, 6)
    d.death_date = None
    d.is_active = True
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_cursor(mock_session: MagicMock, out_value: int = 7) -> MagicMock:
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
    fake_author: Author,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=7)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_author

    repo = AuthorRepository()
    result = repo.create(mock_session, fake_create_data)

    mock_cursor.callproc.assert_called_once()
    proc_name = mock_cursor.callproc.call_args[0][0]
    assert "pkg_authors.p_insert" in proc_name
    assert result.id == 7


def test_create_binds_correct_params(
    mock_session: MagicMock,
    fake_author: Author,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=7)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_author

    repo = AuthorRepository()
    repo.create(mock_session, fake_create_data)

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert bind_args == [
        fake_create_data.first_name,
        fake_create_data.last_name,
        fake_create_data.biography,
        fake_create_data.birth_date,
        fake_create_data.death_date,
        fake_create_data.is_active,
        mock_cursor.var.return_value,
    ]


def test_create_no_commit(
    mock_session: MagicMock,
    fake_author: Author,
    fake_create_data: MagicMock,
) -> None:
    _setup_cursor(mock_session, out_value=7)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_author

    repo = AuthorRepository()
    repo.create(mock_session, fake_create_data)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


def test_update_calls_p_update(
    mock_session: MagicMock,
    fake_author: Author,
    fake_update_data: MagicMock,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_author

    repo = AuthorRepository()
    repo.update(mock_session, 7, fake_update_data)

    assert mock_session.execute.called
    first_call = mock_session.execute.call_args_list[0]
    sql_text = str(first_call[0][0])
    assert "p_update" in sql_text
    binds = first_call[0][1]
    assert binds["p_id"] == 7


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


def test_delete_returns_true_on_success(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = AuthorRepository()
    assert repo.delete(mock_session, 7) is True


def test_delete_returns_false_on_not_found(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=0)

    repo = AuthorRepository()
    assert repo.delete(mock_session, 999) is False


def test_delete_no_commit(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = AuthorRepository()
    repo.delete(mock_session, 7)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------


def test_get_by_id_uses_select(mock_session: MagicMock, fake_author: Author) -> None:
    """get_by_id must issue a SQLAlchemy Select (not TextClause)."""
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_author

    repo = AuthorRepository()
    result = repo.get_by_id(mock_session, 7)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert result is fake_author


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------


def test_list_all_uses_select_no_where(mock_session: MagicMock, fake_author: Author) -> None:
    mock_session.execute.return_value.scalars.return_value.all.return_value = [fake_author]

    repo = AuthorRepository()
    results = repo.list_all(mock_session)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert results == [fake_author]
