"""Unit tests for BookService.list_books() filter forwarding.

Tests verify that the service correctly forwards title/author/category
keyword arguments down to the repository without modification.

No live Oracle connection is required.

Run with:
    pytest tests/unit/test_book_filters.py -v
"""

from unittest.mock import MagicMock

from app.application.services.book_service import BookService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(repo: MagicMock) -> BookService:
    return BookService(repo)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBookServiceListBooksFilters:
    """BookService.list_books() — filter forwarding suite."""

    def test_no_params_calls_repo_with_all_none(self) -> None:
        """Calling list_books() with no args forwards title=None, author=None, category=None."""
        repo = MagicMock()
        repo.list_all.return_value = []

        service = _make_service(repo)
        service.list_books(MagicMock())

        repo.list_all.assert_called_once()
        _, kwargs = repo.list_all.call_args.args, repo.list_all.call_args.kwargs
        assert kwargs.get("title") is None
        assert kwargs.get("author") is None
        assert kwargs.get("category") is None

    def test_title_filter_is_forwarded(self) -> None:
        """title kwarg is forwarded verbatim to repo.list_all()."""
        repo = MagicMock()
        repo.list_all.return_value = []

        service = _make_service(repo)
        service.list_books(MagicMock(), title="Clean Code")

        kwargs = repo.list_all.call_args.kwargs
        assert kwargs["title"] == "Clean Code"
        assert kwargs.get("author") is None
        assert kwargs.get("category") is None

    def test_author_filter_is_forwarded(self) -> None:
        """author kwarg is forwarded verbatim to repo.list_all()."""
        repo = MagicMock()
        repo.list_all.return_value = []

        service = _make_service(repo)
        service.list_books(MagicMock(), author="Martin")

        kwargs = repo.list_all.call_args.kwargs
        assert kwargs.get("title") is None
        assert kwargs["author"] == "Martin"
        assert kwargs.get("category") is None

    def test_category_filter_is_forwarded(self) -> None:
        """category kwarg is forwarded verbatim to repo.list_all()."""
        repo = MagicMock()
        repo.list_all.return_value = []

        service = _make_service(repo)
        service.list_books(MagicMock(), category="Programming")

        kwargs = repo.list_all.call_args.kwargs
        assert kwargs.get("title") is None
        assert kwargs.get("author") is None
        assert kwargs["category"] == "Programming"

    def test_all_filters_forwarded_together(self) -> None:
        """All three filters are forwarded simultaneously when all are provided."""
        repo = MagicMock()
        repo.list_all.return_value = []

        service = _make_service(repo)
        service.list_books(MagicMock(), title="Code", author="Martin", category="Programming")

        kwargs = repo.list_all.call_args.kwargs
        assert kwargs["title"] == "Code"
        assert kwargs["author"] == "Martin"
        assert kwargs["category"] == "Programming"

    def test_repo_list_all_called_exactly_once(self) -> None:
        """repo.list_all() is called exactly once per list_books() invocation."""
        repo = MagicMock()
        repo.list_all.return_value = []

        service = _make_service(repo)
        service.list_books(MagicMock(), title="something")

        repo.list_all.assert_called_once()

    def test_service_returns_repo_result_unchanged(self) -> None:
        """list_books() returns exactly what the repository returns, without modification."""
        repo = MagicMock()
        fake_books = [MagicMock(id=1), MagicMock(id=2)]
        repo.list_all.return_value = fake_books

        service = _make_service(repo)
        result = service.list_books(MagicMock())

        assert result is fake_books
