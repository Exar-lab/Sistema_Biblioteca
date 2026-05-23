"""Application service for return workflows."""

from typing import Any

from app.application.errors import ConflictError, NotFoundError
from app.application.ports.loan_repository import LoanRepository
from app.application.ports.return_repository import ReturnRepository
from app.schemas.circulation.returns import ReturnCreate, ReturnUpdate


class ReturnService:
    """Coordinate return use cases without depending on FastAPI or SQLAlchemy."""

    def __init__(self, return_repository: ReturnRepository, loan_repository: LoanRepository) -> None:
        self._return_repository = return_repository
        self._loan_repository = loan_repository

    def list_returns(self, session: Any) -> list[Any]:
        """Return all return records."""

        return self._return_repository.list_all(session)

    def get_return(self, session: Any, return_id: int) -> Any:
        """Return a record or raise when it does not exist."""

        record = self._return_repository.get_by_id(session, return_id)
        if record is None:
            raise NotFoundError("Return not found.")
        return record

    def create_return(self, session: Any, data: ReturnCreate) -> Any:
        """Record a return after verifying the loan exists and is returnable."""

        loan = self._loan_repository.get_by_id(session, data.loan_id)
        if loan is None:
            raise NotFoundError("Loan not found.")
        if getattr(loan, "status", "ACTIVE") != "ACTIVE":
            raise ConflictError("Loan is not active and cannot be returned.")
        if self._return_repository.get_by_loan(session, data.loan_id) is not None:
            raise ConflictError("A return record already exists for this loan.")
        return self._return_repository.create(session, data, loan_instance=loan)

    def update_return(self, session: Any, return_id: int, data: ReturnUpdate) -> Any:
        """Update a return record or raise when it does not exist."""

        record = self._return_repository.update(session, return_id, data)
        if record is None:
            raise NotFoundError("Return not found.")
        return record

    def delete_return(self, session: Any, return_id: int) -> None:
        """Delete a return record or raise when it does not exist."""

        deleted = self._return_repository.delete(session, return_id)
        if not deleted:
            raise NotFoundError("Return not found.")


__all__ = ["ReturnService"]
