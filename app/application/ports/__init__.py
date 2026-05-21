"""Outbound port protocols — abstract contracts for infrastructure adapters."""

from app.application.ports.role_repository import RoleRepository
from app.application.ports.user_repository import UserRepository
from app.application.ports.category_repository import CategoryRepository
from app.application.ports.author_repository import AuthorRepository
from app.application.ports.book_repository import BookRepository
from app.application.ports.loan_repository import LoanRepository
from app.application.ports.return_repository import ReturnRepository

__all__ = [
    "RoleRepository",
    "UserRepository",
    "CategoryRepository",
    "AuthorRepository",
    "BookRepository",
    "LoanRepository",
    "ReturnRepository",
]
