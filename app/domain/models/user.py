"""LibraryUser ORM model."""

from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.models.types import BoolChar


class LibraryUser(Base):
    """Maps to BIBLIOTECA.library_users."""

    __tablename__ = "library_users"
    __table_args__ = {"schema": "BIBLIOTECA"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(30), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(BoolChar, nullable=False, server_default=text("'Y'"))
    role_id = Column(Integer, ForeignKey("BIBLIOTECA.roles.id"), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))

    role = relationship("Role", back_populates="users", lazy="select")
    loans = relationship("Loan", back_populates="user", lazy="select")
