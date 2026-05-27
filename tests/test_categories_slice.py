"""Tests for the first catalog CRUD vertical slice: categories."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1"

import main  # noqa: E402
from app.api.v1.routers.categories import get_category_service  # noqa: E402
from app.application.errors import ConflictError, NotFoundError  # noqa: E402
from app.application.services.category_service import CategoryService  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.schemas.catalog.categories import CategoryCreate, CategoryUpdate  # noqa: E402


@dataclass
class CategoryStub:
    id: int
    name: str
    description: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FakeCategoryRepository:
    def __init__(self) -> None:
        self.items: dict[int, CategoryStub] = {
            1: CategoryStub(id=1, name="Novela", description="Narrativa")
        }
        self.next_id = 2

    def get_by_id(self, _session: Any, id: int) -> CategoryStub | None:
        return self.items.get(id)

    def list_all(self, _session: Any) -> list[CategoryStub]:
        return list(self.items.values())

    def create(self, _session: Any, data: CategoryCreate) -> CategoryStub:
        if any(item.name == data.name for item in self.items.values()):
            raise ConflictError("Category name already exists.")
        category = CategoryStub(id=self.next_id, **data.model_dump())
        self.items[category.id] = category
        self.next_id += 1
        return category

    def update(self, _session: Any, id: int, data: CategoryUpdate) -> CategoryStub | None:
        category = self.items.get(id)
        if category is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        return category

    def delete(self, _session: Any, id: int) -> bool:
        return self.items.pop(id, None) is not None


def test_category_schema_allows_oracle_description_length() -> None:
    payload = CategoryCreate(name="Historia", description="x" * 500)

    assert payload.description == "x" * 500


def test_category_schema_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        CategoryCreate(name="Historia", legacy_code="HIS")

    with pytest.raises(ValidationError):
        CategoryUpdate(legacy_code="HIS")


@pytest.mark.parametrize("description", ["x" * 501])
def test_category_schema_rejects_description_above_oracle_length(description: str) -> None:
    with pytest.raises(ValidationError):
        CategoryCreate(name="Historia", description=description)


def test_category_service_raises_not_found_for_missing_category() -> None:
    service = CategoryService(FakeCategoryRepository())

    with pytest.raises(NotFoundError, match="Category not found"):
        service.get_category(object(), 999)


def test_category_service_creates_category_through_repository() -> None:
    service = CategoryService(FakeCategoryRepository())

    category = service.create_category(object(), CategoryCreate(name="Ciencia", description="Ensayos"))

    assert category.id == 2
    assert category.name == "Ciencia"
    assert category.description == "Ensayos"


def test_categories_router_is_mounted_and_lists_categories() -> None:
    service = CategoryService(FakeCategoryRepository())

    main.app.dependency_overrides[get_category_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/categories/")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Novela"


def test_categories_router_maps_missing_category_to_404() -> None:
    service = CategoryService(FakeCategoryRepository())

    main.app.dependency_overrides[get_category_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/categories/999")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found."}
