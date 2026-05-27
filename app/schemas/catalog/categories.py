"""Category schemas."""

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema, IdSchema, TimestampSchema


class CategoryBase(BaseSchema):
    """Shared category fields."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=80, description="Category name.")
    description: str | None = Field(default=None, max_length=500, description="Category description.")
    is_active: bool = Field(default=True, description="Whether the category is active.")


class CategoryCreate(CategoryBase):
    """Payload used to create a category."""


class CategoryUpdate(BaseSchema):
    """Payload used to update a category."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CategoryRead(CategoryBase, IdSchema, TimestampSchema):
    """Category data returned by the API."""


__all__ = ["CategoryBase", "CategoryCreate", "CategoryUpdate", "CategoryRead"]
