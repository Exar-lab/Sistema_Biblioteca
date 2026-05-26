"""Tests for the circulation vertical slice: returns."""

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1"

import main  # noqa: E402
from app.api.v1.routers.returns import get_return_service  # noqa: E402
from app.application.errors import ConflictError, NotFoundError  # noqa: E402
from app.application.services.return_service import ReturnService  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.schemas.circulation.returns import ReturnCreate, ReturnUpdate  # noqa: E402


@dataclass
class LoanStub:
    id: int
    user_id: int = 1
    book_id: int = 1
    loan_date: date = field(default_factory=date.today)
    due_date: date = field(default_factory=lambda: date.today() + timedelta(days=14))
    return_date: date | None = None
    status: str = "ACTIVE"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class ReturnStub:
    id: int
    loan_id: int
    return_date: date = field(default_factory=date.today)
    fine_amount: Decimal = Decimal("0.00")
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FakeLoanRepository:
    def __init__(self, loans: dict[int, LoanStub] | None = None) -> None:
        self.loans = loans if loans is not None else {1: LoanStub(id=1)}

    def get_by_id(self, _session: Any, id: int) -> LoanStub | None:
        return self.loans.get(id)


class FakeReturnRepository:
    def __init__(self, *, existing_return: ReturnStub | None = None) -> None:
        self.items: dict[int, ReturnStub] = {}
        if existing_return is not None:
            self.items[existing_return.id] = existing_return
        self.next_id = len(self.items) + 1
        self._loan_map: dict[int, int] = {r.loan_id: r.id for r in self.items.values()}
        self.expire_called_with: list[Any] = []

    def get_by_id(self, _session: Any, id: int) -> ReturnStub | None:
        return self.items.get(id)

    def list_all(self, _session: Any) -> list[ReturnStub]:
        return list(self.items.values())

    def create(self, _session: Any, data: ReturnCreate, loan_instance: Any = None) -> ReturnStub:
        if loan_instance is not None:
            self.expire_called_with.append(loan_instance)
        record = ReturnStub(
            id=self.next_id,
            loan_id=data.loan_id,
            fine_amount=data.fine_amount,
            notes=data.notes,
        )
        self.items[record.id] = record
        self._loan_map[record.loan_id] = record.id
        self.next_id += 1
        return record

    def update(self, _session: Any, id: int, data: ReturnUpdate) -> ReturnStub | None:
        record = self.items.get(id)
        if record is None:
            return None
        for f, v in data.model_dump(exclude_unset=True).items():
            setattr(record, f, v)
        return record

    def delete(self, _session: Any, id: int) -> bool:
        if id not in self.items:
            return False
        del self.items[id]
        return True

    def get_by_loan(self, _session: Any, loan_id: int) -> ReturnStub | None:
        rid = self._loan_map.get(loan_id)
        return self.items.get(rid) if rid is not None else None


def build_service(
    *,
    return_repository: FakeReturnRepository | None = None,
    loan_repository: FakeLoanRepository | None = None,
) -> ReturnService:
    return ReturnService(
        return_repository or FakeReturnRepository(),
        loan_repository or FakeLoanRepository(),
    )


# ── Schema ────────────────────────────────────────────────────────────────────

def test_return_schema_matches_oracle_fields_and_forbids_stale_extras() -> None:
    payload = ReturnCreate(loan_id=1, fine_amount=Decimal("5.00"), notes="Late")

    dumped = payload.model_dump()
    assert dumped["loan_id"] == 1
    assert "condition" not in dumped
    assert "processed_by_user_id" not in dumped
    assert "processed_at" not in dumped

    with pytest.raises(ValidationError):
        ReturnCreate(loan_id=1, condition="Good")

    with pytest.raises(ValidationError):
        ReturnCreate(loan_id=1, processed_by_user_id=2)


def test_return_schema_rejects_negative_fine() -> None:
    with pytest.raises(ValidationError):
        ReturnCreate(loan_id=1, fine_amount=Decimal("-1.00"))


# ── Service ───────────────────────────────────────────────────────────────────

def test_return_service_raises_not_found_for_missing_loan() -> None:
    service = build_service(loan_repository=FakeLoanRepository(loans={}))

    with pytest.raises(NotFoundError, match="Loan not found"):
        service.create_return(object(), ReturnCreate(loan_id=1))


def test_return_service_rejects_already_returned_loan() -> None:
    returned_loan = LoanStub(id=1, status="RETURNED")
    service = build_service(loan_repository=FakeLoanRepository(loans={1: returned_loan}))

    with pytest.raises(ConflictError, match="not active"):
        service.create_return(object(), ReturnCreate(loan_id=1))


def test_return_service_rejects_duplicate_return() -> None:
    existing = ReturnStub(id=1, loan_id=1)
    service = build_service(return_repository=FakeReturnRepository(existing_return=existing))

    with pytest.raises(ConflictError, match="already exists"):
        service.create_return(object(), ReturnCreate(loan_id=1))


def test_return_service_creates_return_and_passes_loan_instance() -> None:
    repo = FakeReturnRepository()
    loan = LoanStub(id=1)
    service = ReturnService(repo, FakeLoanRepository(loans={1: loan}))

    record = service.create_return(object(), ReturnCreate(loan_id=1, notes="On time"))

    assert record.id == 1
    assert record.loan_id == 1
    assert record.notes == "On time"
    assert repo.expire_called_with == [loan]


def test_return_service_raises_not_found_on_missing_update() -> None:
    service = build_service()

    with pytest.raises(NotFoundError, match="Return not found"):
        service.update_return(object(), 999, ReturnUpdate(notes="x"))


def test_return_service_raises_not_found_on_missing_delete() -> None:
    service = build_service()

    with pytest.raises(NotFoundError, match="Return not found"):
        service.delete_return(object(), 999)


# ── Router ────────────────────────────────────────────────────────────────────

def test_returns_router_is_mounted_and_creates_return() -> None:
    service = build_service()

    main.app.dependency_overrides[get_return_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).post(
            "/api/v1/returns/",
            json={"loan_id": 1, "fine_amount": "2.50", "notes": "Slight delay"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 1
    assert payload["loan_id"] == 1
    assert payload["fine_amount"] == "2.50"
    assert "condition" not in payload
    assert "processed_by_user_id" not in payload


def test_returns_router_maps_missing_loan_to_404() -> None:
    service = build_service(loan_repository=FakeLoanRepository(loans={}))

    main.app.dependency_overrides[get_return_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).post("/api/v1/returns/", json={"loan_id": 1})
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Loan not found."}


def test_returns_router_maps_missing_return_to_404() -> None:
    service = build_service()

    main.app.dependency_overrides[get_return_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/returns/999")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Return not found."}


def test_returns_router_maps_duplicate_return_to_409() -> None:
    existing = ReturnStub(id=1, loan_id=1)
    service = build_service(return_repository=FakeReturnRepository(existing_return=existing))

    main.app.dependency_overrides[get_return_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).post("/api/v1/returns/", json={"loan_id": 1})
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_returns_router_lists_returns() -> None:
    repo = FakeReturnRepository()
    repo.items[1] = ReturnStub(id=1, loan_id=1)
    service = ReturnService(repo, FakeLoanRepository())

    main.app.dependency_overrides[get_return_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/returns/")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["loan_id"] == 1
