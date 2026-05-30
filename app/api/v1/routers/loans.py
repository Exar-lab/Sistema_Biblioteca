"""Loan API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.application.services.loan_service import LoanService
from app.core.database import get_db
from app.infrastructure.repositories.book_repository import book_repository
from app.infrastructure.repositories.loan_repository import loan_repository
from app.infrastructure.repositories.user_repository import user_repository
from app.schemas.circulation.loans import LoanCreate, LoanRead

router = APIRouter(prefix="/loans", tags=["Loans"])


def get_loan_service() -> LoanService:
    """Build the loan service with SQLAlchemy repository adapters."""

    return LoanService(loan_repository, user_repository, book_repository)


DbSession = Annotated[Session, Depends(get_db)]
LoanServiceDep = Annotated[LoanService, Depends(get_loan_service)]


@router.get("/", response_model=list[LoanRead])
def list_loans(db: DbSession, service: LoanServiceDep) -> list[object]:
    """List all loans."""

    return service.list_loans(db)


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, db: DbSession, service: LoanServiceDep) -> object:
    """Create a loan."""

    return service.create_loan(db, payload)


@router.get("/users/{user_id}", response_model=list[LoanRead])
def get_user_loans(user_id: int, db: DbSession, service: LoanServiceDep) -> list[object]:
    """Return loan history for one user."""

    return service.get_loans_by_user(db, user_id)


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: DbSession, service: LoanServiceDep) -> object:
    """Return a loan by id."""

    return service.get_loan(db, loan_id)


__all__ = ["router", "get_loan_service"]
