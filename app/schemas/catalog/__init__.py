"""Catalog schemas."""

from app.schemas.catalog.authors import AuthorBase, AuthorCreate, AuthorRead, AuthorUpdate
from app.schemas.catalog.books import BookBase, BookCreate, BookRead, BookUpdate
from app.schemas.catalog.categories import CategoryBase, CategoryCreate, CategoryRead, CategoryUpdate

__all__ = [
    "AuthorBase",
    "AuthorCreate",
    "AuthorRead",
    "AuthorUpdate",
    "BookBase",
    "BookCreate",
    "BookRead",
    "BookUpdate",
    "CategoryBase",
    "CategoryCreate",
    "CategoryRead",
    "CategoryUpdate",
]
