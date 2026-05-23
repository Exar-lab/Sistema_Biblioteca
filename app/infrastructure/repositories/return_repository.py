"""SQLAlchemy adapter for return persistence."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.errors import ConflictError, NotFoundError
from app.domain.models.return_ import Return_
from app.schemas.circulation.returns import ReturnCreate, ReturnUpdate


class SqlAlchemyReturnRepository:
    """Persist return records and refresh the related loan after Oracle trigger fires."""

    def get_by_id(self, session: Session, id: int) -> Return_ | None:
        """Return the record with *id*, or None if it does not exist."""

        return session.scalar(select(Return_).where(Return_.id == id))

    def list_all(self, session: Session) -> list[Return_]:
        """Return all return records ordered by newest first."""

        return list(session.scalars(select(Return_).order_by(Return_.id.desc())).all())

    def create(self, session: Session, data: ReturnCreate, loan_instance: Any = None) -> Return_:
        """Persist a new return record.

        After flush Oracle fires a trigger that marks the related loan as RETURNED
        and sets its return_date. Expiring the loan_instance forces SQLAlchemy to
        re-fetch those attributes on next access.
        """

        values = data.model_dump()
        record = Return_(**values)
        session.add(record)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Return violates database constraints.") from exc
        if loan_instance is not None:
            session.expire(loan_instance, ["status", "return_date"])
        session.refresh(record)
        return record

    def update(self, session: Session, id: int, data: ReturnUpdate) -> Return_ | None:
        """Update the record with *id*, or return None if missing."""

        record = self.get_by_id(session, id)
        if record is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Return violates database constraints.") from exc
        session.refresh(record)
        return record

    def delete(self, session: Session, id: int) -> bool:
        """Delete the record with *id*. Return True if deleted."""

        record = self.get_by_id(session, id)
        if record is None:
            return False
        session.delete(record)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Return cannot be deleted because it is in use.") from exc
        return True

    def get_by_loan(self, session: Session, loan_id: int) -> Return_ | None:
        """Return the return record for the given *loan_id*, or None."""

        return session.scalar(select(Return_).where(Return_.loan_id == loan_id))


return_repository = SqlAlchemyReturnRepository()


__all__ = ["SqlAlchemyReturnRepository", "return_repository"]
