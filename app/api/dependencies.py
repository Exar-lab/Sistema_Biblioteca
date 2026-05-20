"""Shared FastAPI dependencies.

Re-exports ``get_db`` and all service factory functions so routers can import
from a single canonical location if desired.  The service factories delegate
to ``app.composition``; they are also importable directly from there.
"""

from app.core.database import get_db
from app.composition import (
    get_author_service,
    get_book_service,
    get_category_service,
    get_loan_service,
    get_return_service,
    get_role_service,
    get_user_service,
)

__all__ = [
    "get_db",
    "get_role_service",
    "get_user_service",
    "get_category_service",
    "get_author_service",
    "get_book_service",
    "get_loan_service",
    "get_return_service",
]
