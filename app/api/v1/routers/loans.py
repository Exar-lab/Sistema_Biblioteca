"""Loan API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.application.errors import ConflictError, NotFoundError, OutOfStockError
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
def list_loans(db: DbSession, service: LoanServiceDep) -> list[object]:
    """List all loans."""

    return service.list_loans(db)


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, db: DbSession, service: LoanServiceDep) -> object:
    """Create a loan."""

    try:
        return service.create_loan(db, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (ConflictError, OutOfStockError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/users/{user_id}", response_model=list[LoanRead])
def get_user_loans(user_id: int, db: DbSession, service: LoanServiceDep) -> list[object]:
    """Return loan history for one user."""

    try:
        return service.get_loans_by_user(db, user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: DbSession, service: LoanServiceDep) -> object:
    """Return a loan by id."""

    try:
        return service.get_loan(db, loan_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{loan_id}", response_model=LoanRead)
def update_loan(loan_id: int, payload: LoanUpdate, db: DbSession, service: LoanServiceDep) -> object:
    """Update a loan."""

    try:
        return service.update_loan(db, loan_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int, db: DbSession, service: LoanServiceDep) -> Response:
    """Delete a loan."""

    try:
        service.delete_loan(db, loan_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router", "get_loan_service"]
