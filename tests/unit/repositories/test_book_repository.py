"""Unit tests for BookRepository — no live Oracle required."""

import datetime
from unittest.mock import MagicMock, call

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select

from app.domain.models.book import Book
from app.infrastructure.repositories.book_repository import BookRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture()
def fake_book() -> Book:
    b = Book()
    b.id = 20
    b.title = "One Hundred Years of Solitude"
    b.isbn = "978-0-06-088328-7"
    b.description = "A novel by Garcia Marquez"
    b.publication_date = datetime.date(1967, 6, 5)
    b.publisher = "Harper"
    b.edition = "1st"
    b.pages = 417
    b.stock_total = 5
    b.stock_available = 3
    b.is_active = True
    b.category_id = 1
    return b


@pytest.fixture()
def fake_create_data() -> MagicMock:
    d = MagicMock()
    d.title = "One Hundred Years of Solitude"
    d.isbn = "978-0-06-088328-7"
    d.description = "A novel by Garcia Marquez"
    d.publication_date = datetime.date(1967, 6, 5)
    d.publisher = "Harper"
    d.edition = "1st"
    d.pages = 417
    d.stock_total = 5
    d.stock_available = 3
    d.is_active = True
    d.category_id = 1
    return d


@pytest.fixture()
def fake_update_data() -> MagicMock:
    d = MagicMock()
    d.title = "Updated Title"
    d.isbn = "978-0-06-088328-7"
    d.description = "Updated description"
    d.publication_date = datetime.date(1967, 6, 5)
    d.publisher = "Harper"
    d.edition = "2nd"
    d.pages = 420
    d.stock_total = 5
    d.stock_available = 5
    d.is_active = True
    d.category_id = 1
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_cursor(mock_session: MagicMock, out_value: int = 20) -> MagicMock:
    """Wire cursor for create/delete/set_authors paths."""
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
    fake_book: Book,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=20)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    result = repo.create(mock_session, fake_create_data)

    mock_cursor.callproc.assert_called_once()
    proc_name = mock_cursor.callproc.call_args[0][0]
    assert "pkg_books.p_insert" in proc_name
    assert result.id == 20


def test_create_binds_correct_params(
    mock_session: MagicMock,
    fake_book: Book,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=20)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    repo.create(mock_session, fake_create_data)

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert fake_create_data.title in bind_args
    assert fake_create_data.isbn in bind_args
    assert fake_create_data.category_id in bind_args


def test_create_no_commit(
    mock_session: MagicMock,
    fake_book: Book,
    fake_create_data: MagicMock,
) -> None:
    _setup_cursor(mock_session, out_value=20)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    repo.create(mock_session, fake_create_data)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


def test_update_calls_p_update(
    mock_session: MagicMock,
    fake_book: Book,
    fake_update_data: MagicMock,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    repo.update(mock_session, 20, fake_update_data)

    assert mock_session.execute.called
    first_call = mock_session.execute.call_args_list[0]
    sql_text = str(first_call[0][0])
    assert "p_update" in sql_text
    binds = first_call[0][1]
    assert binds["p_id"] == 20


# ---------------------------------------------------------------------------
# delete()
# ---------------------------------------------------------------------------


def test_delete_returns_true_on_success(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = BookRepository()
    assert repo.delete(mock_session, 20) is True


def test_delete_returns_false_on_not_found(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=0)

    repo = BookRepository()
    assert repo.delete(mock_session, 999) is False


def test_delete_no_commit(mock_session: MagicMock) -> None:
    _setup_cursor(mock_session, out_value=1)

    repo = BookRepository()
    repo.delete(mock_session, 20)

    mock_session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# get_by_id()
# ---------------------------------------------------------------------------


def test_get_by_id_uses_select(mock_session: MagicMock, fake_book: Book) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    result = repo.get_by_id(mock_session, 20)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert result is fake_book


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------


def test_list_all_uses_select_no_where(mock_session: MagicMock, fake_book: Book) -> None:
    mock_session.execute.return_value.scalars.return_value.all.return_value = [fake_book]

    repo = BookRepository()
    results = repo.list_all(mock_session)

    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)
    assert results == [fake_book]


# ---------------------------------------------------------------------------
# get_with_authors()  — ORM path, NO procedure call
# ---------------------------------------------------------------------------


def test_get_with_authors_uses_orm_not_procedure(
    mock_session: MagicMock, fake_book: Book
) -> None:
    """get_with_authors() must use session.execute (ORM), not callproc."""
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    result = repo.get_with_authors(mock_session, 20)

    # ORM path was used
    assert mock_session.execute.called
    sql_arg = mock_session.execute.call_args[0][0]
    assert isinstance(sql_arg, Select)

    # No raw cursor / callproc was used
    mock_session.connection.assert_not_called()

    assert result is fake_book


# ---------------------------------------------------------------------------
# set_authors()  — cursor path
# ---------------------------------------------------------------------------


def test_set_authors_clears_then_adds(mock_session: MagicMock) -> None:
    """set_authors([3, 7]) must call p_clear_authors once, then p_add_author twice."""
    mock_cursor = _setup_cursor(mock_session)

    repo = BookRepository()
    repo.set_authors(mock_session, book_id=20, author_ids=[3, 7])

    calls = mock_cursor.callproc.call_args_list
    # 3 total calls: 1 clear + 2 add
    assert len(calls) == 3

    clear_call = calls[0]
    assert "p_clear_authors" in clear_call[0][0]
    assert clear_call[0][1] == [20]

    add_call_1 = calls[1]
    assert "p_add_author" in add_call_1[0][0]
    assert add_call_1[0][1] == [20, 3]

    add_call_2 = calls[2]
    assert "p_add_author" in add_call_2[0][0]
    assert add_call_2[0][1] == [20, 7]


def test_set_authors_with_empty_list_only_clears(mock_session: MagicMock) -> None:
    """set_authors([]) must call p_clear_authors once and p_add_author zero times."""
    mock_cursor = _setup_cursor(mock_session)

    repo = BookRepository()
    repo.set_authors(mock_session, book_id=20, author_ids=[])

    calls = mock_cursor.callproc.call_args_list
    # exactly 1 call: the clear
    assert len(calls) == 1
    assert "p_clear_authors" in calls[0][0][0]

    # no p_add_author call
    add_calls = [c for c in calls if "p_add_author" in c[0][0]]
    assert len(add_calls) == 0
