"""Loans router — CRUD endpoints plus user/book filters."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.loan_service import LoanService
from app.composition import get_loan_service
from app.schemas.circulation.loans import LoanCreate, LoanRead, LoanUpdate

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.get("/", response_model=list[LoanRead], status_code=status.HTTP_200_OK)
def list_loans(
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
) -> list[LoanRead]:
    """Return all loans."""
    return service.list(db)


@router.get("/by-user/{user_id}", response_model=list[LoanRead], status_code=status.HTTP_200_OK)
def get_loans_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
) -> list[LoanRead]:
    """Return all loans for a given user."""
    return service.get_by_user(db, user_id)


@router.get("/by-book/{book_id}", response_model=list[LoanRead], status_code=status.HTTP_200_OK)
def get_loans_by_book(
    book_id: int,
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
) -> list[LoanRead]:
    """Return all loans for a given book."""
    return service.get_by_book(db, book_id)


@router.get("/{loan_id}", response_model=LoanRead, status_code=status.HTTP_200_OK)
def get_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
) -> LoanRead:
    """Return a single loan by ID (raises 404 if not found)."""
    return service.get(db, loan_id)


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(
    payload: LoanCreate,
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
) -> LoanRead:
    """Create a new loan (raises 409 if book is out of stock)."""
    return service.create(db, payload)


@router.put("/{loan_id}", response_model=LoanRead, status_code=status.HTTP_200_OK)
def update_loan(
    loan_id: int,
    payload: LoanUpdate,
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
) -> LoanRead:
    """Update an existing loan (raises 404 if not found)."""
    return service.update(db, loan_id, payload)


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    service: LoanService = Depends(get_loan_service),
) -> None:
    """Delete a loan (raises 404 if not found)."""
    service.delete(db, loan_id)
