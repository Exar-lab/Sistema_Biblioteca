"""Tests for the catalog CRUD vertical slice: authors."""

import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1"

import main  # noqa: E402
from app.api.v1.routers.authors import get_author_service  # noqa: E402
from app.application.errors import NotFoundError  # noqa: E402
from app.application.services.author_service import AuthorService  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.schemas.catalog.authors import AuthorCreate, AuthorUpdate  # noqa: E402


@dataclass
class AuthorStub:
    id: int
    first_name: str
    last_name: str
    biography: str | None = None
    birth_date: date | None = None
    death_date: date | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FakeAuthorRepository:
    def __init__(self) -> None:
        self.items: dict[int, AuthorStub] = {
            1: AuthorStub(id=1, first_name="Jorge", last_name="Borges")
        }
        self.next_id = 2

    def get_by_id(self, _session: Any, id: int) -> AuthorStub | None:
        return self.items.get(id)

    def list_all(self, _session: Any) -> list[AuthorStub]:
        return list(self.items.values())

    def create(self, _session: Any, data: AuthorCreate) -> AuthorStub:
        author = AuthorStub(id=self.next_id, **data.model_dump())
        self.items[author.id] = author
        self.next_id += 1
        return author

    def update(self, _session: Any, id: int, data: AuthorUpdate) -> AuthorStub | None:
        author = self.items.get(id)
        if author is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(author, field, value)
        return author

    def delete(self, _session: Any, id: int) -> bool:
        return self.items.pop(id, None) is not None


def test_author_schema_allows_oracle_fields() -> None:
    payload = AuthorCreate(
        first_name="Julio",
        last_name="Cortázar",
        biography="Rayuela author",
        birth_date=date(1914, 8, 26),
        death_date=date(1984, 2, 12),
    )

    assert payload.first_name == "Julio"
    assert payload.death_date == date(1984, 2, 12)


def test_author_schema_rejects_non_oracle_nationality_field() -> None:
    with pytest.raises(ValidationError):
        AuthorCreate(first_name="Julio", last_name="Cortázar", nationality="Argentina")


def test_author_schema_rejects_first_name_above_oracle_length() -> None:
    with pytest.raises(ValidationError):
        AuthorCreate(first_name="x" * 81, last_name="Cortázar")


def test_author_service_raises_not_found_for_missing_author() -> None:
    service = AuthorService(FakeAuthorRepository())

    with pytest.raises(NotFoundError, match="Author not found"):
        service.get_author(object(), 999)


def test_author_service_creates_author_through_repository() -> None:
    service = AuthorService(FakeAuthorRepository())

    author = service.create_author(
        object(), AuthorCreate(first_name="Julio", last_name="Cortázar", biography="Rayuela author")
    )

    assert author.id == 2
    assert author.first_name == "Julio"
    assert author.last_name == "Cortázar"
    assert author.biography == "Rayuela author"


def test_authors_router_is_mounted_and_lists_authors() -> None:
    service = AuthorService(FakeAuthorRepository())

    main.app.dependency_overrides[get_author_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/authors/")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["first_name"] == "Jorge"
    assert response.json()[0]["last_name"] == "Borges"
    assert "nationality" not in response.json()[0]
    assert "full_name" not in response.json()[0]


def test_authors_router_maps_missing_author_to_404() -> None:
    service = AuthorService(FakeAuthorRepository())

    main.app.dependency_overrides[get_author_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/authors/999")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Author not found."}
