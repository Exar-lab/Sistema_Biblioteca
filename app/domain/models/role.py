"""Role ORM model."""

from sqlalchemy import Column, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    """Maps to BIBLIOTECA.roles.

    Columns must match oracle_schema.sql exactly — no is_active column on this table.
    """

    __tablename__ = "roles"
    __table_args__ = {"schema": "BIBLIOTECA"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))

    users = relationship("LibraryUser", back_populates="role", lazy="select")
