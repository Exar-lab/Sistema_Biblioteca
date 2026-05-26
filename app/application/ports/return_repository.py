"""ReturnRepository outbound port."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ReturnRepository(Protocol):
    """Contract for return persistence.

    After create, the underlying loan's status and return_date reflect the
    server-side Oracle trigger update (adapter must call session.expire(loan)).
    """

    def get_by_id(self, session: Any, id: int) -> Any | None:
        """Return the return record with *id*, or None if it does not exist."""
        ...

    def list_all(self, session: Any) -> list[Any]:
        """Return all return records."""
        ...

    def create(self, session: Any, data: Any, loan_instance: Any = None) -> Any:
        """Persist a new return record and return the created instance."""
        ...

    def update(self, session: Any, id: int, data: Any) -> Any | None:
        """Update the return record with *id*, or return None if it does not exist."""
        ...

    def delete(self, session: Any, id: int) -> bool:
        """Delete the return record with *id*. Return True if deleted, False if not found."""
        ...

    def get_by_loan(self, session: Any, loan_id: int) -> Any | None:
        """Return the return record for *loan_id*, or None if the loan has not been returned."""
        ...
