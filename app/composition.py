"""Composition root — DI factory functions for services.

Each ``get_*_service`` function is a FastAPI ``Depends``-compatible factory
that wires the database session → concrete repository → service.

Routers import these factories and declare them via ``Depends``; they never
instantiate repos or services directly.
"""

from app.application.services.author_service import AuthorService
from app.application.services.book_service import BookService
from app.application.services.category_service import CategoryService
from app.application.services.loan_service import LoanService
from app.application.services.return_service import ReturnService
from app.application.services.role_service import RoleService
from app.application.services.user_service import UserService
from app.infrastructure.repositories.author_repository import AuthorRepositorySql
from app.infrastructure.repositories.book_repository import BookRepositorySql
from app.infrastructure.repositories.category_repository import CategoryRepositorySql
from app.infrastructure.repositories.loan_repository import LoanRepositorySql
from app.infrastructure.repositories.return_repository import ReturnRepositorySql
from app.infrastructure.repositories.role_repository import RoleRepositorySql
from app.infrastructure.repositories.user_repository import UserRepositorySql

# ---------------------------------------------------------------------------
# Singleton-like repository instances (stateless — session is per call)
# ---------------------------------------------------------------------------

_role_repo = RoleRepositorySql()
_user_repo = UserRepositorySql()
_category_repo = CategoryRepositorySql()
_author_repo = AuthorRepositorySql()
_book_repo = BookRepositorySql()
_loan_repo = LoanRepositorySql()
_return_repo = ReturnRepositorySql()


# ---------------------------------------------------------------------------
# Service factory functions
# ---------------------------------------------------------------------------


def get_role_service() -> RoleService:
    """Return a RoleService wired to the current request session."""
    return RoleService(repo=_role_repo)


def get_user_service() -> UserService:
    """Return a UserService wired to the current request session."""
    return UserService(repo=_user_repo)


def get_category_service() -> CategoryService:
    """Return a CategoryService wired to the current request session."""
    return CategoryService(repo=_category_repo)


def get_author_service() -> AuthorService:
    """Return an AuthorService wired to the current request session."""
    return AuthorService(repo=_author_repo)


def get_book_service() -> BookService:
    """Return a BookService wired to the current request session."""
    return BookService(repo=_book_repo, author_repo=_author_repo)


def get_loan_service() -> LoanService:
    """Return a LoanService wired to the current request session."""
    return LoanService(
        repo=_loan_repo,
        user_repo=_user_repo,
        book_repo=_book_repo,
    )


def get_return_service() -> ReturnService:
    """Return a ReturnService wired to the current request session."""
    return ReturnService(
        repo=_return_repo,
        loan_repo=_loan_repo,
    )
