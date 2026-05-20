"""Category ORM model."""

from sqlalchemy import Column, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.domain.models.types import BoolChar


class Category(Base):
    """Maps to BIBLIOTECA.categories."""

    __tablename__ = "categories"
    __table_args__ = {"schema": "BIBLIOTECA"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    is_active = Column(BoolChar, nullable=False, server_default=text("'Y'"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))

    books = relationship("Book", back_populates="category", lazy="select")
