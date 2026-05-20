"""SQLAlchemy repository adapters — concrete implementations of outbound port Protocols."""

from app.infrastructure.repositories.role_repository import RoleRepositorySql
from app.infrastructure.repositories.user_repository import UserRepositorySql
from app.infrastructure.repositories.category_repository import CategoryRepositorySql
from app.infrastructure.repositories.author_repository import AuthorRepositorySql
from app.infrastructure.repositories.book_repository import BookRepositorySql
from app.infrastructure.repositories.loan_repository import LoanRepositorySql
from app.infrastructure.repositories.return_repository import ReturnRepositorySql

__all__ = [
    "RoleRepositorySql",
    "UserRepositorySql",
    "CategoryRepositorySql",
    "AuthorRepositorySql",
    "BookRepositorySql",
    "LoanRepositorySql",
    "ReturnRepositorySql",
]
