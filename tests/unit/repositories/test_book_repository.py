"""Unit tests for BookRepository — no live Oracle required."""

import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import Select

from app.domain.models.book import Book
from app.infrastructure.repositories.book_repository import BookRepository
from app.schemas.catalog.books import BookUpdate


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
def fake_update_data() -> BookUpdate:
    return BookUpdate(
        title="Updated Title",
        isbn="978-0-06-088328-7",
        description="Updated description",
        publication_date=datetime.date(1967, 6, 5),
        publisher="Harper",
        edition="2nd",
        pages=420,
        stock_total=5,
        is_active=True,
        category_id=1,
    )


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
    assert bind_args == [
        fake_create_data.title,
        fake_create_data.isbn,
        fake_create_data.description,
        fake_create_data.publication_date,
        fake_create_data.publisher,
        fake_create_data.edition,
        fake_create_data.pages,
        fake_create_data.stock_total,
        fake_create_data.stock_total,
        "Y",
        fake_create_data.category_id,
        mock_cursor.var.return_value,
    ]


def test_create_binds_inactive_bool_as_oracle_char(
    mock_session: MagicMock,
    fake_book: Book,
    fake_create_data: MagicMock,
) -> None:
    mock_cursor = _setup_cursor(mock_session, out_value=20)
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book
    fake_create_data.is_active = False

    repo = BookRepository()
    repo.create(mock_session, fake_create_data)

    bind_args = mock_cursor.callproc.call_args[0][1]
    assert bind_args[9] == "N"


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
    update_call = mock_session.execute.call_args_list[1]
    sql_text = str(update_call[0][0])
    assert "p_update" in sql_text
    binds = update_call[0][1]
    assert binds["p_id"] == 20
    assert binds["p_is_active"] == "Y"


def test_update_binds_inactive_bool_as_oracle_char(
    mock_session: MagicMock,
    fake_book: Book,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    repo.update(mock_session, 20, BookUpdate(is_active=False))

    binds = mock_session.execute.call_args_list[1][0][1]
    assert binds["p_is_active"] == "N"


def test_update_preserves_existing_values_for_partial_payload(
    mock_session: MagicMock,
    fake_book: Book,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    repo.update(mock_session, 20, BookUpdate(author_ids=[1]))

    binds = mock_session.execute.call_args_list[1][0][1]
    assert binds["p_title"] == fake_book.title
    assert binds["p_isbn"] == fake_book.isbn
    assert binds["p_description"] == fake_book.description
    assert binds["p_publication_date"] == fake_book.publication_date
    assert binds["p_publisher"] == fake_book.publisher
    assert binds["p_edition"] == fake_book.edition
    assert binds["p_pages"] == fake_book.pages
    assert binds["p_stock_total"] == fake_book.stock_total
    assert binds["p_stock_available"] == fake_book.stock_available
    assert binds["p_is_active"] == "Y"
    assert binds["p_category_id"] == fake_book.category_id


def test_update_ignores_explicit_nulls_for_optional_scalar_fields(
    mock_session: MagicMock,
    fake_book: Book,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    repo.update(
        mock_session,
        20,
        BookUpdate(
            isbn=None,
            description=None,
            publication_date=None,
            publisher=None,
            edition=None,
            pages=None,
            stock_total=None,
            category_id=None,
        ),
    )

    binds = mock_session.execute.call_args_list[1][0][1]
    assert binds["p_isbn"] == fake_book.isbn
    assert binds["p_description"] == fake_book.description
    assert binds["p_publication_date"] == fake_book.publication_date
    assert binds["p_publisher"] == fake_book.publisher
    assert binds["p_edition"] == fake_book.edition
    assert binds["p_pages"] == fake_book.pages
    assert binds["p_stock_total"] == fake_book.stock_total
    assert binds["p_stock_available"] == fake_book.stock_available
    assert binds["p_category_id"] == fake_book.category_id


def test_update_clamps_available_stock_when_total_is_reduced(
    mock_session: MagicMock,
    fake_book: Book,
) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = fake_book

    repo = BookRepository()
    repo.update(mock_session, 20, BookUpdate(stock_total=2))

    binds = mock_session.execute.call_args_list[1][0][1]
    assert binds["p_stock_total"] == 2
    assert binds["p_stock_available"] == 2


def test_update_returns_none_when_book_does_not_exist(mock_session: MagicMock) -> None:
    mock_session.execute.return_value.scalar_one_or_none.return_value = None

    repo = BookRepository()
    result = repo.update(mock_session, 999, BookUpdate(title="Missing"))

    assert result is None
    assert len(mock_session.execute.call_args_list) == 1


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
