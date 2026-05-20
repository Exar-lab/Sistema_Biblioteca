"""Unit tests for application error types.

Verifies that all domain errors are proper Exception subclasses,
carry the expected message, and are catchable by their own type.
No SQLAlchemy or infrastructure imports.
"""

import pytest

from app.application.errors import ConflictError, NotFoundError, OutOfStockError


class TestNotFoundError:
    def test_is_exception(self) -> None:
        assert issubclass(NotFoundError, Exception)

    def test_catchable_as_exception(self) -> None:
        with pytest.raises(Exception):
            raise NotFoundError("not found")

    def test_catchable_by_own_type(self) -> None:
        with pytest.raises(NotFoundError):
            raise NotFoundError("not found")

    def test_carries_message(self) -> None:
        err = NotFoundError("thing 42 not found")
        assert "thing 42 not found" in str(err)

    def test_default_message(self) -> None:
        err = NotFoundError()
        assert str(err)  # non-empty default message


class TestOutOfStockError:
    def test_is_exception(self) -> None:
        assert issubclass(OutOfStockError, Exception)

    def test_catchable_as_exception(self) -> None:
        with pytest.raises(Exception):
            raise OutOfStockError("no stock")

    def test_catchable_by_own_type(self) -> None:
        with pytest.raises(OutOfStockError):
            raise OutOfStockError("no stock")

    def test_carries_message(self) -> None:
        err = OutOfStockError("book 7 out of stock")
        assert "book 7 out of stock" in str(err)

    def test_default_message(self) -> None:
        err = OutOfStockError()
        assert str(err)


class TestConflictError:
    def test_is_exception(self) -> None:
        assert issubclass(ConflictError, Exception)

    def test_catchable_as_exception(self) -> None:
        with pytest.raises(Exception):
            raise ConflictError("conflict")

    def test_catchable_by_own_type(self) -> None:
        with pytest.raises(ConflictError):
            raise ConflictError("conflict")

    def test_carries_message(self) -> None:
        err = ConflictError("duplicate entry")
        assert "duplicate entry" in str(err)

    def test_default_message(self) -> None:
        err = ConflictError()
        assert str(err)


class TestErrorsAreDistinct:
    """Ensure the three error types do not overlap with each other."""

    def test_out_of_stock_is_not_catchable_as_not_found(self) -> None:
        """OutOfStockError must NOT be caught by an except NotFoundError clause."""
        caught_as_not_found = False
        try:
            raise OutOfStockError()
        except NotFoundError:
            caught_as_not_found = True
        except OutOfStockError:
            pass  # expected — swallow it
        assert not caught_as_not_found

    def test_conflict_is_not_catchable_as_not_found(self) -> None:
        """ConflictError must NOT be caught by an except NotFoundError clause."""
        caught_as_not_found = False
        try:
            raise ConflictError()
        except NotFoundError:
            caught_as_not_found = True
        except ConflictError:
            pass  # expected — swallow it
        assert not caught_as_not_found
