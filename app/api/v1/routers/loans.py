"""Loan API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import AdminOnly
from app.application.services.loan_service import LoanService
from app.core.database import get_db
from app.infrastructure.repositories.book_repository import book_repository
from app.infrastructure.repositories.loan_repository import loan_repository
from app.infrastructure.repositories.user_repository import user_repository
from app.schemas.circulation.loans import LoanCreate, LoanRead, LoanUpdate

router = APIRouter(prefix="/loans", tags=["Loans"])


def get_loan_service() -> LoanService:
    """Build the loan service with SQLAlchemy repository adapters."""

    return LoanService(loan_repository, user_repository, book_repository)


DbSession = Annotated[Session, Depends(get_db)]
LoanServiceDep = Annotated[LoanService, Depends(get_loan_service)]


@router.get("/", response_model=list[LoanRead])
def list_loans(db: DbSession, service: LoanServiceDep, _current_user: AdminOnly) -> list[object]:
    """List all loans."""

    return service.list_loans(db)


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(
    payload: LoanCreate,
    db: DbSession,
    service: LoanServiceDep,
    _current_user: AdminOnly,
) -> object:
    """Create a loan."""

    return service.create_loan(db, payload)


@router.get("/users/{user_id}", response_model=list[LoanRead])
def get_user_loans(user_id: int, db: DbSession, service: LoanServiceDep, _current_user: AdminOnly) -> list[object]:
    """Return loan history for one user."""

    return service.get_loans_by_user(db, user_id)


@router.get("/books/{book_id}", response_model=list[LoanRead])
def get_book_loans(book_id: int, db: DbSession, service: LoanServiceDep, _current_user: AdminOnly) -> list[object]:
    """Return loan history for one book."""

    return service.get_loans_by_book(db, book_id)


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: DbSession, service: LoanServiceDep, _current_user: AdminOnly) -> object:
    """Return a loan by id."""

    return service.get_loan(db, loan_id)


@router.patch("/{loan_id}", response_model=LoanRead)
def update_loan(
    loan_id: int,
    payload: LoanUpdate,
    db: DbSession,
    service: LoanServiceDep,
    _current_user: AdminOnly,
) -> object:
    """Update a loan's safe admin-editable fields."""

    return service.update_loan(db, loan_id, payload)


@router.patch("/{loan_id}/cancel", response_model=LoanRead)
def cancel_loan(
    loan_id: int,
    db: DbSession,
    service: LoanServiceDep,
    _current_user: AdminOnly,
) -> object:
    """Cancel an active loan."""

    return service.cancel_loan(db, loan_id)


__all__ = ["router", "get_loan_service"]
