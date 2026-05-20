"""Unit tests for BoolChar TypeDecorator.

Zero SQLAlchemy session/engine dependency — tests only the pure conversion
logic of process_bind_param and process_result_value.
"""

import pytest

from app.domain.models.types import BoolChar


@pytest.fixture
def boolchar() -> BoolChar:
    """Return a fresh BoolChar instance for each test."""
    return BoolChar()


class TestProcessBindParam:
    """Python -> DB direction."""

    def test_true_maps_to_Y(self, boolchar: BoolChar) -> None:
        assert boolchar.process_bind_param(True, None) == "Y"

    def test_false_maps_to_N(self, boolchar: BoolChar) -> None:
        assert boolchar.process_bind_param(False, None) == "N"

    def test_none_maps_to_none(self, boolchar: BoolChar) -> None:
        assert boolchar.process_bind_param(None, None) is None


class TestProcessResultValue:
    """DB -> Python direction."""

    def test_Y_maps_to_true(self, boolchar: BoolChar) -> None:
        assert boolchar.process_result_value("Y", None) is True

    def test_N_maps_to_false(self, boolchar: BoolChar) -> None:
        assert boolchar.process_result_value("N", None) is False

    def test_none_is_none_safe(self, boolchar: BoolChar) -> None:
        # None from DB must not raise; implementation returns None
        result = boolchar.process_result_value(None, None)
        assert result is None

    def test_unexpected_value_maps_to_false(self, boolchar: BoolChar) -> None:
        """Any value that is not 'Y' evaluates to False."""
        assert boolchar.process_result_value("X", None) is False
