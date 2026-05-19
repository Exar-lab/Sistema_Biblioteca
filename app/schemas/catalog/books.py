"""Book schemas."""

from datetime import date

from pydantic import Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema
from app.schemas.catalog.authors import AuthorRead
from app.schemas.catalog.categories import CategoryRead


class BookBase(BaseSchema):
    """Shared book fields."""

    title: str = Field(..., min_length=2, max_length=200, description="Book title.")
    isbn: str | None = Field(default=None, max_length=20, description="ISBN code.")
    description: str | None = Field(default=None, max_length=4000, description="Book summary.")
    publication_date: date | None = Field(default=None, description="Publication date.")
    publisher: str | None = Field(default=None, max_length=120, description="Publisher name.")
    edition: str | None = Field(default=None, max_length=40, description="Edition label.")
    pages: int | None = Field(default=None, gt=0, description="Number of pages.")
    stock_total: int = Field(default=0, ge=0, description="Total copies in inventory.")
    is_active: bool = Field(default=True, description="Whether the book is active.")
    category_id: int | None = Field(default=None, gt=0, description="Assigned category identifier.")


class BookCreate(BookBase):
    """Payload used to create a book."""

    author_ids: list[int] = Field(default_factory=list, description="Author identifiers for the many-to-many relation.")


class BookUpdate(BaseSchema):
    """Payload used to update a book."""

    title: str | None = Field(default=None, min_length=2, max_length=200)
    isbn: str | None = Field(default=None, max_length=20)
    description: str | None = Field(default=None, max_length=4000)
    publication_date: date | None = None
    publisher: str | None = Field(default=None, max_length=120)
    edition: str | None = Field(default=None, max_length=40)
    pages: int | None = Field(default=None, gt=0)
    stock_total: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    category_id: int | None = Field(default=None, gt=0)
    author_ids: list[int] | None = None


class BookRead(BookBase, IdSchema, TimestampSchema):
    """Book data returned by the API."""

    stock_available: int = Field(default=0, ge=0, description="Copies available for lending.")
    category: CategoryRead | None = None
    authors: list[AuthorRead] = Field(default_factory=list)


__all__ = ["BookBase", "BookCreate", "BookUpdate", "BookRead"]
