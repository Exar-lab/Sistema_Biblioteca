"""Custom SQLAlchemy TypeDecorators for Oracle-specific column types."""

from sqlalchemy import CHAR
from sqlalchemy.types import TypeDecorator


class BoolChar(TypeDecorator):
    """Maps a CHAR(1) Oracle column ('Y'/'N') to/from Python bool.

    - Python True  -> stores 'Y'
    - Python False -> stores 'N'
    - DB 'Y'       -> Python True
    - DB anything else (including None) -> Python False / None
    """

    impl = CHAR(1)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert Python bool to CHAR(1) before writing to the DB."""
        if value is None:
            return None
        if not isinstance(value, bool):
            raise TypeError(f"BoolChar expected bool, got {type(value).__name__!r}")
        return "Y" if value else "N"

    def process_result_value(self, value, dialect):
        """Convert CHAR(1) from the DB back to Python bool."""
        if value is None:
            return None
        return value == "Y"


def bool_to_oracle_char(value: bool | None) -> str | None:
    """Convert Python booleans to Oracle CHAR(1) flag values."""

    if value is None:
        return None
    return "Y" if value else "N"
