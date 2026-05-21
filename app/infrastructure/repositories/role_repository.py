"""SQLAlchemy adapter for role persistence."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.errors import ConflictError
from app.domain.models.role import Role
from app.schemas.roles import RoleCreate, RoleUpdate


class SqlAlchemyRoleRepository:
    """Persist roles using SQLAlchemy ORM models."""

    def get_by_id(self, session: Session, id: int) -> Role | None:
        """Return the role with *id*, or None if it does not exist."""

        return session.get(Role, id)

    def list_all(self, session: Session) -> list[Role]:
        """Return roles ordered by name for stable API responses."""

        return list(session.scalars(select(Role).order_by(Role.name)).all())

    def create(self, session: Session, data: RoleCreate) -> Role:
        """Persist a new role and return the created instance."""

        role = Role(**data.model_dump())
        session.add(role)
        return self._flush_and_refresh(session, role)

    def update(self, session: Session, id: int, data: RoleUpdate) -> Role | None:
        """Update the role with *id* and return it, or None if missing."""

        role = self.get_by_id(session, id)
        if role is None:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(role, field, value)

        return self._flush_and_refresh(session, role)

    def delete(self, session: Session, id: int) -> bool:
        """Delete the role with *id*. Return True if deleted."""

        role = self.get_by_id(session, id)
        if role is None:
            return False

        session.delete(role)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ConflictError("Role cannot be deleted because it is in use.") from exc
        return True

    def _flush_and_refresh(self, session: Session, role: Role) -> Role:
        """Flush changes and translate uniqueness failures to domain conflicts."""

        try:
            session.flush()
            session.refresh(role)
        except IntegrityError as exc:
            raise ConflictError("Role name already exists.") from exc
        return role


role_repository = SqlAlchemyRoleRepository()


__all__ = ["SqlAlchemyRoleRepository", "role_repository"]
