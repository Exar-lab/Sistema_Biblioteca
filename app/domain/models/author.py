"""Author ORM model."""

from sqlalchemy import Column, Date, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.domain.models.types import BoolChar


class Author(Base):
    """Maps to BIBLIOTECA.authors.

    No 'nationality' column — not present in oracle_schema.sql.
    """

    __tablename__ = "authors"
    __table_args__ = {"schema": "BIBLIOTECA"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    biography = Column(String(2000), nullable=True)
    birth_date = Column(Date, nullable=True)
    death_date = Column(Date, nullable=True)
    is_active = Column(BoolChar, nullable=False, server_default=text("'Y'"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))

    books = relationship(
        "Book",
        secondary="BIBLIOTECA.book_authors",
        back_populates="authors",
        lazy="select",
    )
