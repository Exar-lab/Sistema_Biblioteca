"""Tests for the catalog CRUD vertical slice: books."""

import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1"

import main  # noqa: E402
from app.api.v1.routers.books import get_book_service  # noqa: E402
from app.application.errors import ConflictError, NotFoundError  # noqa: E402
from app.application.services.book_service import BookService  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.schemas.catalog.books import BookCreate, BookUpdate  # noqa: E402


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


@dataclass
class CategoryStub:
    id: int
    name: str
    description: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class BookStub:
    id: int
    title: str
    isbn: str | None = None
    description: str | None = None
    publication_date: date | None = None
    publisher: str | None = None
    edition: str | None = None
    pages: int | None = None
    stock_total: int = 0
    stock_available: int = 0
    is_active: bool = True
    category_id: int | None = None
    category: CategoryStub | None = None
    authors: list[AuthorStub] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FakeBookRepository:
    def __init__(self) -> None:
        self.authors: dict[int, AuthorStub] = {
            1: AuthorStub(id=1, first_name="Jorge", last_name="Borges"),
            2: AuthorStub(id=2, first_name="Adolfo", last_name="Bioy Casares"),
        }
        self.categories: dict[int, CategoryStub] = {1: CategoryStub(id=1, name="Novela")}
        self.items: dict[int, BookStub] = {
            1: BookStub(
                id=1,
                title="Ficciones",
                isbn="9789500422808",
                pages=203,
                stock_total=3,
                stock_available=3,
                category_id=1,
                category=self.categories[1],
                authors=[self.authors[1]],
            )
        }
        self.next_id = 2
        self.set_author_calls: list[tuple[int, list[int]]] = []

    def get_by_id(self, _session: Any, id: int) -> BookStub | None:
        return self.items.get(id)

    def get_with_authors(self, _session: Any, id: int) -> BookStub | None:
        return self.items.get(id)

    def list_all(
        self,
        _session: Any,
        *,
        title: str | None = None,
        author: str | None = None,
        category: str | None = None,
    ) -> list[BookStub]:
        return list(self.items.values())

    def create(self, _session: Any, data: BookCreate) -> BookStub:
        values = data.model_dump()
        values.pop("author_ids")
        values["stock_available"] = values["stock_total"]
        book = BookStub(id=self.next_id, **values)
        book.category = self.categories.get(book.category_id) if book.category_id is not None else None
        self.items[book.id] = book
        self.next_id += 1
        return book

    def update(self, _session: Any, id: int, data: BookUpdate) -> BookStub | None:
        book = self.items.get(id)
        if book is None:
            return None
        values = data.model_dump(exclude_unset=True)
        values.pop("author_ids", None)
        new_stock_total = values.get("stock_total")
        if new_stock_total is not None and book.stock_available > new_stock_total:
            book.stock_available = new_stock_total
        for field_name, value in values.items():
            setattr(book, field_name, value)
        if "category_id" in values:
            book.category = self.categories.get(book.category_id) if book.category_id is not None else None
        return book

    def delete(self, _session: Any, id: int) -> bool:
        return self.items.pop(id, None) is not None

    def set_authors(self, _session: Any, book_id: int, author_ids: list[int]) -> None:
        self.set_author_calls.append((book_id, author_ids))
        book = self.items.get(book_id)
        if book is None:
            raise NotFoundError("Book not found.")
        self._assign_relationships(book, author_ids)

    def _assign_relationships(self, book: BookStub, author_ids: list[int]) -> None:
        unique_ids = list(dict.fromkeys(author_ids))
        missing_ids = [author_id for author_id in unique_ids if author_id not in self.authors]
        if missing_ids:
            raise ConflictError("One or more authors do not exist.")
        book.authors = [self.authors[author_id] for author_id in unique_ids]
        book.category = self.categories.get(book.category_id) if book.category_id is not None else None


def test_book_schema_allows_oracle_fields_and_response_only_stock_available() -> None:
    payload = BookCreate(
        title="Sobre héroes y tumbas",
        isbn="9789507316322",
        description="x" * 4000,
        publication_date=date(1961, 1, 1),
        publisher="Sudamericana",
        edition="1a",
        pages=544,
        stock_total=4,
        category_id=1,
        author_ids=[1, 2],
    )

    dumped = payload.model_dump()
    assert dumped["description"] == "x" * 4000
    assert dumped["author_ids"] == [1, 2]
    assert "stock_available" not in dumped


def test_book_schema_rejects_response_only_and_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        BookCreate(title="Ficciones", stock_available=3)

    with pytest.raises(ValidationError):
        BookUpdate(full_title="Ficciones completas")


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "F"},
        {"title": "Ficciones", "pages": 0},
        {"title": "Ficciones", "stock_total": -1},
        {"title": "Ficciones", "category_id": 0},
        {"title": "Ficciones", "author_ids": [0]},
    ],
)
def test_book_schema_rejects_invalid_oracle_values(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        BookCreate(**payload)


def test_book_service_raises_not_found_for_missing_book() -> None:
    service = BookService(FakeBookRepository())

    with pytest.raises(NotFoundError, match="Book not found"):
        service.get_book(object(), 999)


def test_book_service_creates_book_and_assigns_unique_authors() -> None:
    repository = FakeBookRepository()
    service = BookService(repository)

    book = service.create_book(
        object(),
        BookCreate(title="La invención de Morel", isbn="9789500420972", stock_total=2, author_ids=[2, 2]),
    )

    assert book.id == 2
    assert book.title == "La invención de Morel"
    assert book.stock_total == 2
    assert book.stock_available == 2
    assert repository.set_author_calls == [(2, [2, 2])]
    assert [author.id for author in book.authors] == [2]


def test_book_service_updates_author_relationships_when_supplied() -> None:
    repository = FakeBookRepository()
    service = BookService(repository)

    book = service.update_book(object(), 1, BookUpdate(title="Ficciones corregidas", author_ids=[2]))

    assert book.title == "Ficciones corregidas"
    assert repository.set_author_calls == [(1, [2])]
    assert [author.id for author in book.authors] == [2]


def test_book_service_clamps_available_stock_when_total_is_reduced() -> None:
    service = BookService(FakeBookRepository())

    book = service.update_book(object(), 1, BookUpdate(stock_total=1))

    assert book.stock_total == 1
    assert book.stock_available == 1


def test_book_service_rejects_missing_author_relationship() -> None:
    service = BookService(FakeBookRepository())

    with pytest.raises(ConflictError, match="authors do not exist"):
        service.create_book(object(), BookCreate(title="Libro inválido", author_ids=[999]))


def test_book_repository_set_authors_raises_not_found_for_missing_book() -> None:
    repository = FakeBookRepository()

    with pytest.raises(NotFoundError, match="Book not found"):
        repository.set_authors(object(), 999, [1])


def test_books_router_is_mounted_and_lists_books() -> None:
    service = BookService(FakeBookRepository())

    main.app.dependency_overrides[get_book_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/books/")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()[0]
    assert payload["title"] == "Ficciones"
    assert payload["stock_available"] == 3
    assert payload["category"]["name"] == "Novela"
    assert payload["authors"][0]["last_name"] == "Borges"
    assert "author_ids" not in payload


def test_books_router_maps_missing_book_to_404() -> None:
    service = BookService(FakeBookRepository())

    main.app.dependency_overrides[get_book_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/books/999")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found."}


def test_books_router_maps_author_conflict_to_409() -> None:
    service = BookService(FakeBookRepository())

    main.app.dependency_overrides[get_book_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).post("/api/v1/books/", json={"title": "Libro inválido", "author_ids": [999]})
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {"detail": "One or more authors do not exist."}
