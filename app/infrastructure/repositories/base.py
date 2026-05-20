"""Generic synchronous SQLAlchemy repository base.

Session is accepted at call time so callers (routers / services) control
the transaction boundary — no session stored on the instance.
"""

from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from app.core.database import Base

M = TypeVar("M", bound=Base)  # type: ignore[type-arg]


class SqlRepositoryBase(Generic[M]):
    """Thin CRUD base for synchronous SQLAlchemy.

    Subclasses set ``model`` at class level and may override any method.
    """

    model: type[M]  # set by each concrete subclass

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, session: Session, id: int) -> M | None:
        """Return the instance with *id*, or None if it does not exist."""
        return session.get(self.model, id)

    def list_all(self, session: Session) -> list[M]:
        """Return all rows ordered by primary key ascending."""
        return session.query(self.model).order_by(self.model.id).all()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, session: Session, data: Any) -> M:
        """Persist a new instance built from *data* and return it.

        *data* may be a Pydantic model or a plain dict.
        """
        if hasattr(data, "model_dump"):
            data = data.model_dump(exclude_unset=True)
        instance = self.model(**data)
        session.add(instance)
        session.flush()
        session.refresh(instance)
        return instance

    def update(self, session: Session, id: int, data: Any) -> M | None:
        """Update the instance with *id* using *data*.

        *data* may be a Pydantic model or a plain dict.
        Returns the updated instance, or None if not found.
        """
        if hasattr(data, "model_dump"):
            data = data.model_dump(exclude_unset=True)
        instance = self.get_by_id(session, id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        session.flush()
        session.refresh(instance)
        return instance

    def delete(self, session: Session, id: int) -> bool:
        """Delete the instance with *id*.

        Returns True if deleted, False if not found.
        """
        instance = self.get_by_id(session, id)
        if instance is None:
            return False
        session.delete(instance)
        session.flush()
        return True
