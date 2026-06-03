"""Unit tests for LoanRepository — no live Oracle required."""

import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select

from app.domain.models.loan import Loan
from app.infrastructure.repositories.loan_repository import LoanRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture()
def fake_loan() -> Loan:
    l = Loan()
    l.id = 15
    l.user_id = 5
    l.book_id = 20
    l.loan_date = datetime.date(2024, 1, 10)
    l.due_date = datetime.date(2024, 2, 10)
    l.return_date = None
    l.status = "ACTIVE"
    return l


@pytest.fixture()
def fake_create_data() -> MagicMock:
    d = MagicMock()
    d.user_id = 5
    d.book_id = 20
    d.loan_date = datetime.date(2024, 1, 10)
    d.due_date = datetime.date(2024, 2, 10)
    return d


@pytest.fixture()
def fake_update_data() -> MagicMock:
    d = MagicMock()
    d.user_id = 5
    d.book_id = 20
    d.loan_date = datetime.date(2024, 1, 10)
    d.due_date = datetime.date(2024, 3, 10)
    d.return_date = None
    d.status = "ACTIVE"
    d.model_fields_set = {"user_id", "book_id", "loan_date", "due_date", "return_date", "status"}
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_cursor(mock_session: MagicMock, out_value: int = 15) -> MagicMock:
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
    fake_loan: Loan,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=15)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_loan

    repo = LoanRepository()
    result = repo.create(mock_session, fake_create_data)

    mock_cursor.callproc.assert_called_once()
    proc_name = mock_cursor.callproc.call_args[0][0]
    assert "pkg_loans.p_insert" in proc_name
    assert result.id == 15


def test_create_binds_correct_params(
    mock_session: MagicMock,
    fake_loan: Loan,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=15)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_loan

    repo = LoanRepository()
    repo.create(mock_session, fake_create_data)

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert bind_args == [
        fake_create_data.user_id,
        fake_create_data.book_id,
        fake_create_data.loan_date,
        fake_create_data.due_date,
        mock_cursor.var.return_value,
    ]


def test_create_no_commit(
    mock_session: MagicMock,
    fake_loan: Loan,
    fake_create_data: MagicMock,
) -> None:
    _setup_cursor(mock_session, out_value=15)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_loan

    repo = LoanRepository()
    repo.create(mock_session, fake_create_data)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


def test_update_calls_p_update(
    mock_session: MagicMock,
    fake_loan: Loan,
    fake_update_data: MagicMock,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_loan

    repo = LoanRepository()
    repo.update(mock_session, 15, fake_update_data)

    assert mock_session.execute.called
    update_call = next(
        call for call in mock_session.execute.call_args_list if "p_update" in str(call[0][0])
    )
    sql_text = str(update_call[0][0])
    assert "p_update" in sql_text
    binds = update_call[0][1]
    assert binds["p_id"] == 15
    assert binds["p_user_id"] == fake_update_data.user_id
    assert binds["p_book_id"] == fake_update_data.book_id
    assert binds["p_loan_date"] == fake_update_data.loan_date
    assert binds["p_due_date"] == fake_update_data.due_date
    assert binds["p_return_date"] is None
    assert binds["p_status"] == "ACTIVE"


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


def test_delete_returns_true_on_success(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = LoanRepository()
    assert repo.delete(mock_session, 15) is True


def test_delete_returns_false_on_not_found(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=0)

    repo = LoanRepository()
    assert repo.delete(mock_session, 999) is False


def test_delete_no_commit(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = LoanRepository()
    repo.delete(mock_session, 15)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------


def test_get_by_id_uses_select(mock_session: MagicMock, fake_loan: Loan) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_loan

    repo = LoanRepository()
    result = repo.get_by_id(mock_session, 15)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert result is fake_loan


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------


def test_list_all_uses_select_no_where(mock_session: MagicMock, fake_loan: Loan) -> None:
    mock_session.execute.return_value.scalars.return_value.all.return_value = [fake_loan]

    repo = LoanRepository()
    results = repo.list_all(mock_session)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert results == [fake_loan]


# ---------------------------------------------------------------------------
# cancel()  — raw cursor path (p_cancel via callproc)
# ---------------------------------------------------------------------------


def test_cancel_calls_p_cancel_and_returns_true(mock_session: MagicMock) -> None:
    """cancel() must call pkg_loans.p_cancel via callproc and return True when found."""
    mock_cursor = _setup_cursor(mock_session, out_value=1)

    repo = LoanRepository()
    result = repo.cancel(mock_session, loan_id=15)

    mock_cursor.callproc.assert_called_once()
    proc_name = mock_cursor.callproc.call_args[0][0]
    assert "pkg_loans.p_cancel" in proc_name

    # loan_id must be in the bind list
    bind_args = mock_cursor.callproc.call_args[0][1]
    assert 15 in bind_args

    assert result is True


def test_cancel_returns_false_when_not_found(mock_session: MagicMock) -> None:
    """cancel() must return False when p_cancel OUT param == 0 (not found)."""
    _setup_cursor(mock_session, out_value=0)

    repo = LoanRepository()
    result = repo.cancel(mock_session, loan_id=999)

    assert result is False


def test_cancel_no_commit(mock_session: MagicMock) -> None:
    """cancel() must NOT call session.commit."""
    _setup_cursor(mock_session, out_value=1)

    repo = LoanRepository()
    repo.cancel(mock_session, loan_id=15)

    mock_session.commit.assert_not_called()
