"""SQLAlchemy adapter for ReturnRepository port.

After inserting a return row the Oracle AFTER INSERT trigger updates the
corresponding loan's status and return_date server-side.  SQLAlchemy's
identity map will not see that change unless we expire the stale attributes
before the next access.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.domain.models.loan import Loan
from app.domain.models.return_ import Return_
from app.infrastructure.repositories.base import SqlRepositoryBase

# Loan attributes updated server-side by the Oracle trigger
_TRIGGER_UPDATED_LOAN_ATTRS = ["status", "return_date"]


class ReturnRepositorySql(SqlRepositoryBase[Return_]):
    """Concrete repository for BIBLIOTECA.returns.

    Structurally satisfies the ``ReturnRepository`` typing.Protocol.
    """

    model = Return_

    # ------------------------------------------------------------------
    # Override create — expire stale loan fields after flush
    # ------------------------------------------------------------------

    def create(
        self,
        session: Session,
        data: Any,
        loan_instance: Loan | None = None,
    ) -> Return_:
        """Persist a new return row and expire stale loan attributes.

        Args:
            session: The current SQLAlchemy session.
            data: Mapping of column values for the new Return_ row.
            loan_instance: The ``Loan`` ORM instance whose status and
                return_date will be updated server-side by the Oracle trigger.
                If provided, those attributes are expired so the next access
                re-fetches from the database.

        Returns:
            The newly created ``Return_`` instance.
        """
        return_obj = super().create(session, data)

        if loan_instance is not None:
            session.expire(loan_instance, _TRIGGER_UPDATED_LOAN_ATTRS)

        return return_obj
