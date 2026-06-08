"""Loan API routes."""

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import AdminOnly, get_current_user
from app.application.services.loan_service import LoanService
from app.application.services.return_service import ReturnService
from app.schemas.users import UserRead
from app.core.database import get_db
from app.infrastructure.repositories.book_repository import book_repository
from app.infrastructure.repositories.loan_repository import loan_repository
from app.infrastructure.repositories.return_repository import return_repository
from app.infrastructure.repositories.user_repository import user_repository
from app.schemas.circulation.loans import LoanCreate, LoanCreateSelf, LoanRead, LoanUpdate
from app.schemas.circulation.returns import ReturnCreate

router = APIRouter(prefix="/loans", tags=["Loans"])


def get_loan_service() -> LoanService:
    """Build the loan service with SQLAlchemy repository adapters."""

    return LoanService(loan_repository, user_repository, book_repository)


def get_return_service() -> ReturnService:
    return ReturnService(return_repository, loan_repository)


DbSession = Annotated[Session, Depends(get_db)]
LoanServiceDep = Annotated[LoanService, Depends(get_loan_service)]
ReturnServiceDep = Annotated[ReturnService, Depends(get_return_service)]


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


@router.post("/me", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_own_loan(
    payload: LoanCreateSelf,
    db: DbSession,
    service: LoanServiceDep,
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> object:
    """Allow an authenticated user to borrow a book for themselves."""

    loan_data = LoanCreate(
        user_id=current_user.id,
        book_id=payload.book_id,
        loan_date=datetime.date.today(),
        due_date=datetime.date.today() + datetime.timedelta(days=14),
    )
    return service.create_loan(db, loan_data)


@router.get("/users/{user_id}", response_model=list[LoanRead])
def get_user_loans(
    user_id: int,
    db: DbSession,
    service: LoanServiceDep,
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> list[object]:
    """Return loan history for one user. Admins can query any user; regular users only their own."""

    is_admin = (current_user.role.name or "").strip().casefold() == "admin"
    if not is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
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


@router.patch("/{loan_id}/return", response_model=LoanRead)
def return_loan(
    loan_id: int,
    db: DbSession,
    loan_service: LoanServiceDep,
    return_service: ReturnServiceDep,
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> object:
    """Return a loan. Admins can return any loan; users can only return their own."""

    is_admin = (current_user.role.name or "").strip().casefold() == "admin"
    loan = loan_service.get_loan(db, loan_id)
    if not is_admin and loan.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    return_service.create_return(db, ReturnCreate(loan_id=loan_id))
    return loan_service.get_loan(db, loan_id)


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
