"""Application service for returns.

Thin orchestration layer — loads the active loan before creating the return
so the adapter can expire its stale attributes after the Oracle trigger fires.
No SQLAlchemy or infrastructure imports.
"""

from typing import Any

from app.application.errors import NotFoundError
from app.application.ports.loan_repository import LoanRepository
from app.application.ports.return_repository import ReturnRepository


class ReturnService:
    """Orchestrates return operations through the ReturnRepository port.

    Also accepts LoanRepository to fetch the loan instance that the Oracle
    trigger will update server-side after the return row is inserted.
    """

    def __init__(
        self,
        repo: ReturnRepository,
        loan_repo: LoanRepository,
    ) -> None:
        self._repo = repo
        self._loan_repo = loan_repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, session: Any, id: int) -> Any:
        """Return the return record with *id*.

        Raises:
            NotFoundError: if no return record with that ID exists.
        """
        record = self._repo.get_by_id(session, id)
        if record is None:
            raise NotFoundError(f"Return {id} not found.")
        return record

    def list(self, session: Any) -> list[Any]:
        """Return all return records."""
        return self._repo.list_all(session)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Any, data: Any) -> Any:
        """Persist a new return record and expire stale loan attributes.

        Loads the loan from *data['loan_id']* before delegating to the repo
        so the adapter can call ``session.expire(loan_instance, [...])`` after
        the Oracle trigger updates status and return_date server-side.

        Raises:
            NotFoundError: if the referenced loan does not exist.
        """
        loan_id = data.get("loan_id") if isinstance(data, dict) else getattr(data, "loan_id", None)

        loan_instance = None
        if loan_id is not None:
            loan_instance = self._loan_repo.get_by_id(session, loan_id)
            if loan_instance is None:
                raise NotFoundError(f"Loan {loan_id} not found.")

        return self._repo.create(session, data, loan_instance=loan_instance)

    def update(self, session: Any, id: int, data: Any) -> Any:
        """Update an existing return record and return the updated instance.

        Raises:
            NotFoundError: if no return record with that ID exists.
        """
        updated = self._repo.update(session, id, data)
        if updated is None:
            raise NotFoundError(f"Return {id} not found.")
        return updated

    def delete(self, session: Any, id: int) -> None:
        """Delete the return record with *id*.

        Raises:
            NotFoundError: if no return record with that ID exists.
        """
        deleted = self._repo.delete(session, id)
        if not deleted:
            raise NotFoundError(f"Return {id} not found.")
