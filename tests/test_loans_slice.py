"""Tests for the circulation vertical slice: loans."""

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1"

import main  # noqa: E402
from app.api.v1.routers.loans import get_loan_service  # noqa: E402
from app.application.errors import ConflictError, NotFoundError, OutOfStockError  # noqa: E402
from app.application.services.loan_service import LoanService  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.infrastructure.repositories.loan_repository import SqlAlchemyLoanRepository  # noqa: E402
from app.schemas.circulation.loans import LoanCreate, LoanUpdate  # noqa: E402


@dataclass
class UserStub:
    id: int
    username: str = "reader"
    full_name: str = "Reader User"
    email: str = "reader@example.com"
    phone: str | None = None
    is_active: bool = True
    role_id: int | None = 1
    role: Any = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class BookStub:
    id: int
    title: str = "Ficciones"
    isbn: str | None = "9789500422808"
    description: str | None = None
    publication_date: date | None = None
    publisher: str | None = None
    edition: str | None = None
    pages: int | None = 203
    stock_total: int = 3
    stock_available: int = 3
    is_active: bool = True
    category_id: int | None = None
    category: Any = None
    authors: list[Any] | None = None

    def __post_init__(self) -> None:
        if self.authors is None:
            self.authors = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class LoanStub:
    id: int
    user_id: int
    book_id: int
    loan_date: date
    due_date: date
    return_date: date | None = None
    status: str = "ACTIVE"
    user: UserStub | None = None
    book: BookStub | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FakeUserRepository:
    def __init__(self, users: dict[int, UserStub] | None = None) -> None:
        self.users = users if users is not None else {1: UserStub(id=1)}

    def get_by_id(self, _session: Any, id: int) -> UserStub | None:
        return self.users.get(id)


class FakeBookRepository:
    def __init__(self, books: dict[int, BookStub] | None = None) -> None:
        self.books = books if books is not None else {1: BookStub(id=1)}

    def get_by_id(self, _session: Any, id: int) -> BookStub | None:
        return self.books.get(id)


class FakeLoanRepository:
    def __init__(self, *, overdue: bool = False, out_of_stock: bool = False) -> None:
        self.overdue = overdue
        self.out_of_stock = out_of_stock
        self.users = {1: UserStub(id=1)}
        self.books = {1: BookStub(id=1)}
        self.items: dict[int, LoanStub] = {
            1: LoanStub(
                id=1,
                user_id=1,
                book_id=1,
                loan_date=date.today(),
                due_date=date.today() + timedelta(days=7),
                user=self.users[1],
                book=self.books[1],
            )
        }
        self.next_id = 2

    def get_by_id(self, _session: Any, id: int) -> LoanStub | None:
        return self.items.get(id)

    def list_all(self, _session: Any) -> list[LoanStub]:
        return list(self.items.values())

    def create(self, _session: Any, data: LoanCreate) -> LoanStub:
        if self.out_of_stock:
            raise OutOfStockError("Book has no available stock for loan.")
        loan = LoanStub(
            id=self.next_id,
            user_id=data.user_id,
            book_id=data.book_id,
            loan_date=data.loan_date,
            due_date=data.due_date,
            user=self.users.get(data.user_id),
            book=self.books.get(data.book_id),
        )
        self.items[loan.id] = loan
        self.next_id += 1
        return loan

    def get_by_user(self, _session: Any, user_id: int) -> list[LoanStub]:
        return [loan for loan in self.items.values() if loan.user_id == user_id]

    def get_by_book(self, _session: Any, book_id: int) -> list[LoanStub]:
        return [loan for loan in self.items.values() if loan.book_id == book_id]

    def update(self, _session: Any, id: int, data: LoanUpdate) -> LoanStub | None:
        loan = self.items.get(id)
        if loan is None:
            return None
        for f, v in data.model_dump(exclude_unset=True).items():
            setattr(loan, f, v)
        return loan

    def delete(self, _session: Any, id: int) -> bool:
        if id not in self.items:
            return False
        del self.items[id]
        return True

    def has_overdue_loans(self, _session: Any, user_id: int) -> bool:
        return self.overdue and user_id == 1


def build_service(
    *,
    loan_repository: FakeLoanRepository | None = None,
    user_repository: FakeUserRepository | None = None,
    book_repository: FakeBookRepository | None = None,
) -> LoanService:
    return LoanService(
        loan_repository or FakeLoanRepository(),
        user_repository or FakeUserRepository(),
        book_repository or FakeBookRepository(),
    )


def test_loan_schema_matches_oracle_fields_and_forbids_stale_extras() -> None:
    payload = LoanCreate(user_id=1, book_id=1, loan_date=date.today(), due_date=date.today() + timedelta(days=7))

    dumped = payload.model_dump()
    assert dumped["user_id"] == 1
    assert "notes" not in dumped
    assert "is_active" not in dumped

    with pytest.raises(ValidationError):
        LoanCreate(user_id=1, book_id=1, due_date=date.today(), notes="not in Oracle")

    with pytest.raises(ValidationError):
        LoanCreate(user_id=1, book_id=1, due_date=date.today(), is_active=True)

    with pytest.raises(ValidationError):
        LoanCreate(user_id=1, book_id=1, due_date=date.today(), returned_at=datetime.now())


def test_loan_schema_rejects_due_date_before_loan_date() -> None:
    with pytest.raises(ValidationError, match="due_date must be on or after loan_date"):
        LoanCreate(user_id=1, book_id=1, loan_date=date.today(), due_date=date.today() - timedelta(days=1))


@pytest.mark.parametrize(
    ("user_repository", "book_repository", "message"),
    [
        (FakeUserRepository(users={}), FakeBookRepository(), "User not found"),
        (FakeUserRepository(), FakeBookRepository(books={}), "Book not found"),
    ],
)
def test_loan_service_raises_not_found_for_missing_user_or_book(
    user_repository: FakeUserRepository, book_repository: FakeBookRepository, message: str
) -> None:
    service = build_service(user_repository=user_repository, book_repository=book_repository)

    with pytest.raises(NotFoundError, match=message):
        service.create_loan(object(), LoanCreate(user_id=1, book_id=1, due_date=date.today() + timedelta(days=7)))


def test_loan_service_blocks_inactive_users() -> None:
    inactive_user_repo = FakeUserRepository(users={1: UserStub(id=1, is_active=False)})
    service = build_service(user_repository=inactive_user_repo)

    with pytest.raises(ConflictError, match="inactive"):
        service.create_loan(object(), LoanCreate(user_id=1, book_id=1, due_date=date.today() + timedelta(days=7)))


def test_loan_service_blocks_users_with_overdue_loans() -> None:
    service = build_service(loan_repository=FakeLoanRepository(overdue=True))

    with pytest.raises(ConflictError, match="overdue loans"):
        service.create_loan(object(), LoanCreate(user_id=1, book_id=1, due_date=date.today() + timedelta(days=7)))


def test_loan_service_creates_and_lists_user_history() -> None:
    service = build_service()

    loan = service.create_loan(object(), LoanCreate(user_id=1, book_id=1, due_date=date.today() + timedelta(days=7)))
    history = service.get_loans_by_user(object(), 1)

    assert loan.id == 2
    assert loan.status == "ACTIVE"
    assert loan.return_date is None
    assert [item.id for item in history] == [1, 2]


def test_sqlalchemy_loan_repository_detects_oracle_out_of_stock_error() -> None:
    class FakeOracleError(Exception):
        orig = "ORA-20001: Book has no available stock for loan."

    assert SqlAlchemyLoanRepository()._is_out_of_stock_error(FakeOracleError("trigger failed")) is True


def test_loans_router_is_mounted_and_creates_loan() -> None:
    service = build_service()

    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).post(
            "/api/v1/loans/",
            json={"user_id": 1, "book_id": 1, "due_date": str(date.today() + timedelta(days=7))},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 2
    assert payload["status"] == "ACTIVE"
    assert payload["return_date"] is None
    assert payload["user"]["username"] == "reader"
    assert payload["book"]["title"] == "Ficciones"
    assert "notes" not in payload
    assert "returned_at" not in payload


def test_loans_router_lists_loans_and_user_history() -> None:
    service = build_service()

    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        list_response = TestClient(main.app).get("/api/v1/loans/")
        user_response = TestClient(main.app).get("/api/v1/loans/users/1")
    finally:
        main.app.dependency_overrides.clear()

    assert list_response.status_code == 200
    assert user_response.status_code == 200
    assert list_response.json()[0]["id"] == 1
    assert user_response.json()[0]["user_id"] == 1


def test_loans_router_maps_missing_loan_to_404() -> None:
    service = build_service()

    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/loans/999")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Loan not found."}


@pytest.mark.parametrize(
    ("service", "expected_detail"),
    [
        (build_service(user_repository=FakeUserRepository(users={})), "User not found."),
        (build_service(book_repository=FakeBookRepository(books={})), "Book not found."),
    ],
)
def test_loans_router_maps_missing_user_or_book_to_404(service: LoanService, expected_detail: str) -> None:
    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).post(
            "/api/v1/loans/",
            json={"user_id": 1, "book_id": 1, "due_date": str(date.today() + timedelta(days=7))},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}


@pytest.mark.parametrize(
    ("service", "expected_detail"),
    [
        (build_service(loan_repository=FakeLoanRepository(overdue=True)), "User has overdue loans."),
        (build_service(loan_repository=FakeLoanRepository(out_of_stock=True)), "Book has no available stock for loan."),
    ],
)
def test_loans_router_maps_overdue_and_out_of_stock_to_409(service: LoanService, expected_detail: str) -> None:
    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).post(
            "/api/v1/loans/",
            json={"user_id": 1, "book_id": 1, "due_date": str(date.today() + timedelta(days=7))},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {"detail": expected_detail}


def test_loans_router_updates_due_date() -> None:
    service = build_service()
    new_due = date.today() + timedelta(days=21)

    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).patch(
            "/api/v1/loans/1",
            json={"due_date": str(new_due)},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["due_date"] == str(new_due)


def test_loans_router_maps_update_of_missing_loan_to_404() -> None:
    service = build_service()

    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).patch(
            "/api/v1/loans/999",
            json={"due_date": str(date.today() + timedelta(days=7))},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404


def test_loans_router_deletes_loan() -> None:
    service = build_service()

    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).delete("/api/v1/loans/1")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 204


def test_loans_router_maps_delete_of_missing_loan_to_404() -> None:
    service = build_service()

    main.app.dependency_overrides[get_loan_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).delete("/api/v1/loans/999")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
