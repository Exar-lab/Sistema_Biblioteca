"""Infrastructure repository implementations backed by Oracle stored procedures."""

from app.infrastructure.repositories.author_repository import AuthorRepository
from app.infrastructure.repositories.book_repository import BookRepository
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.infrastructure.repositories.loan_repository import LoanRepository
from app.infrastructure.repositories.return_repository import ReturnRepository
from app.infrastructure.repositories.role_repository import RoleRepository
from app.infrastructure.repositories.user_repository import UserRepository

__all__ = [
    "AuthorRepository",
    "BookRepository",
    "CategoryRepository",
    "LoanRepository",
    "ReturnRepository",
    "RoleRepository",
    "UserRepository",
]
