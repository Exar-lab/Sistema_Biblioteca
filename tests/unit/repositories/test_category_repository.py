"""Unit tests for CategoryRepository — no live Oracle required."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select

from app.domain.models.category import Category
from app.infrastructure.repositories.category_repository import CategoryRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture()
def fake_category() -> Category:
    c = Category()
    c.id = 10
    c.name = "Fiction"
    c.description = "Fictional works"
    c.is_active = True
    return c


@pytest.fixture()
def fake_create_data() -> MagicMock:
    d = MagicMock()
    d.name = "Fiction"
    d.description = "Fictional works"
    d.is_active = True
    return d


@pytest.fixture()
def fake_update_data() -> MagicMock:
    d = MagicMock()
    d.name = "Science Fiction"
    d.description = "Updated description"
    d.is_active = True
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_cursor(mock_session: MagicMock, out_value: int = 10) -> MagicMock:
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
    fake_category: Category,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=10)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_category

    repo = CategoryRepository()
    result = repo.create(mock_session, fake_create_data)

    mock_cursor.callproc.assert_called_once()
    proc_name = mock_cursor.callproc.call_args[0][0]
    assert "pkg_categories.p_insert" in proc_name
    assert result.id == 10


def test_create_binds_correct_params(
    mock_session: MagicMock,
    fake_category: Category,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=10)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_category

    repo = CategoryRepository()
    repo.create(mock_session, fake_create_data)

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert bind_args == [
        fake_create_data.name,
        fake_create_data.description,
        "Y",
        mock_cursor.var.return_value,
    ]


def test_create_binds_inactive_bool_as_oracle_char(
    mock_session: MagicMock,
    fake_category: Category,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=10)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_category
    fake_create_data.is_active = False

    repo = CategoryRepository()
    repo.create(mock_session, fake_create_data)

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert bind_args[2] == "N"


def test_create_no_commit(
    mock_session: MagicMock,
    fake_category: Category,
    fake_create_data: MagicMock,
) -> None:
    _setup_cursor(mock_session, out_value=10)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_category

    repo = CategoryRepository()
    repo.create(mock_session, fake_create_data)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


def test_update_calls_p_update(
    mock_session: MagicMock,
    fake_category: Category,
    fake_update_data: MagicMock,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_category

    repo = CategoryRepository()
    repo.update(mock_session, 10, fake_update_data)

    assert mock_session.execute.called
    first_call = mock_session.execute.call_args_list[0]
    sql_text = str(first_call[0][0])
    assert "p_update" in sql_text
    binds = first_call[0][1]
    assert binds["p_id"] == 10
    assert binds["p_is_active"] == "Y"


def test_update_binds_inactive_bool_as_oracle_char(
    mock_session: MagicMock,
    fake_category: Category,
    fake_update_data: MagicMock,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_category
    fake_update_data.is_active = False

    repo = CategoryRepository()
    repo.update(mock_session, 10, fake_update_data)

    binds = mock_session.execute.call_args_list[0][0][1]
    assert binds["p_is_active"] == "N"


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


def test_delete_returns_true_on_success(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = CategoryRepository()
    assert repo.delete(mock_session, 10) is True


def test_delete_returns_false_on_not_found(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=0)

    repo = CategoryRepository()
    assert repo.delete(mock_session, 999) is False


def test_delete_no_commit(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = CategoryRepository()
    repo.delete(mock_session, 10)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------


def test_get_by_id_uses_select(mock_session: MagicMock, fake_category: Category) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_category

    repo = CategoryRepository()
    result = repo.get_by_id(mock_session, 10)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert result is fake_category


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------


def test_list_all_uses_select_no_where(mock_session: MagicMock, fake_category: Category) -> None:
    mock_session.execute.return_value.scalars.return_value.all.return_value = [fake_category]

    repo = CategoryRepository()
    results = repo.list_all(mock_session)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert results == [fake_category]
