"""Unit tests for ReturnRepository — no live Oracle required."""

import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select

from app.domain.models.return_ import Return_
from app.infrastructure.repositories.return_repository import ReturnRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture()
def fake_return() -> Return_:
    r = Return_()
    r.id = 30
    r.loan_id = 15
    r.return_date = datetime.date(2024, 1, 25)
    r.fine_amount = Decimal("0.00")
    r.notes = "Returned on time"
    return r


@pytest.fixture()
def fake_create_data() -> MagicMock:
    d = MagicMock()
    d.loan_id = 15
    d.return_date = datetime.date(2024, 1, 25)
    d.fine_amount = Decimal("0.00")
    d.notes = "Returned on time"
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_cursor(mock_session: MagicMock, out_value: int = 30) -> MagicMock:
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
# create() → p_process
# ---------------------------------------------------------------------------


def test_create_calls_p_process_and_returns_id(
    mock_session: MagicMock,
    fake_return: Return_,
    fake_create_data: MagicMock,
) -> None:
    """create() must call pkg_returns.p_process via callproc and return the new Return_."""
    mock_cursor = _setup_cursor(mock_session, out_value=30)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_return

    repo = ReturnRepository()
    result = repo.create(mock_session, fake_create_data)

    mock_cursor.callproc.assert_called_once()
    proc_name = mock_cursor.callproc.call_args[0][0]
    assert "pkg_returns.p_process" in proc_name

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert bind_args == [
        fake_create_data.loan_id,
        fake_create_data.return_date,
        fake_create_data.fine_amount,
        fake_create_data.notes,
        mock_cursor.var.return_value,
    ]

    assert result.id == 30


def test_create_no_commit(
    mock_session: MagicMock,
    fake_return: Return_,
    fake_create_data: MagicMock,
) -> None:
    """create() must NOT call session.commit."""
    _setup_cursor(mock_session, out_value=30)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_return

    repo = ReturnRepository()
    repo.create(mock_session, fake_create_data)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------


def test_get_by_id_uses_select(mock_session: MagicMock, fake_return: Return_) -> None:
    """get_by_id() must issue a SQLAlchemy Select (not TextClause)."""
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_return

    repo = ReturnRepository()
    result = repo.get_by_id(mock_session, 30)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert result is fake_return


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------


def test_list_all_uses_select_no_where(
    mock_session: MagicMock, fake_return: Return_
) -> None:
    """list_all() must issue a Select and return all mocked rows."""
    mock_session.execute.return_value.scalars.return_value.all.return_value = [fake_return]

    repo = ReturnRepository()
    results = repo.list_all(mock_session)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert results == [fake_return]


# ---------------------------------------------------------------------------
# update() → p_update
# ---------------------------------------------------------------------------


def test_update_calls_p_update(
    mock_session: MagicMock,
    fake_return: Return_,
    fake_create_data: MagicMock,
) -> None:
    """update() must call pkg_returns.p_update via session.execute and return the refreshed entity."""
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_return

    repo = ReturnRepository()
    result = repo.update(mock_session, 30, fake_create_data)

    assert mock_session.execute.called
    # update() calls execute twice: first the text() proc call, then get_by_id ORM select
    first_call_sql = str(mock_session.execute.call_args_list[0][0][0])
    assert "p_update" in first_call_sql
    assert result is fake_return


# ---------------------------------------------------------------------------
# delete() → p_delete
# ---------------------------------------------------------------------------


def test_delete_returns_true_when_found(mock_session: MagicMock) -> None:
    """delete() must return True when the procedure reports a row was deleted."""
    mock_cursor = _setup_cursor(mock_session, out_value=1)

    repo = ReturnRepository()
    result = repo.delete(mock_session, 30)

    mock_cursor.callproc.assert_called_once()
    assert result is True


def test_delete_returns_false_when_not_found(mock_session: MagicMock) -> None:
    """delete() must return False when the procedure reports no row was found."""
    mock_cursor = _setup_cursor(mock_session, out_value=0)

    repo = ReturnRepository()
    result = repo.delete(mock_session, 999)

    mock_cursor.callproc.assert_called_once()
    assert result is False
