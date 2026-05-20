"""Book ORM model and book_authors association table."""

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Table, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.domain.models.types import BoolChar


# Association table — plain Table object, NOT a mapped class.
book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("BIBLIOTECA.books.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", Integer, ForeignKey("BIBLIOTECA.authors.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP")),
    schema="BIBLIOTECA",
)


class Book(Base):
    """Maps to BIBLIOTECA.books."""

    __tablename__ = "books"
    __table_args__ = {"schema": "BIBLIOTECA"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    isbn = Column(String(20), nullable=True, unique=True)
    description = Column(String(4000), nullable=True)
    publication_date = Column(Date, nullable=True)
    publisher = Column(String(120), nullable=True)
    edition = Column(String(40), nullable=True)
    pages = Column(Integer, nullable=True)
    stock_total = Column(Integer, nullable=False, server_default=text("0"))
    stock_available = Column(Integer, nullable=False, server_default=text("0"))
    is_active = Column(BoolChar, nullable=False, server_default=text("'Y'"))
    category_id = Column(Integer, ForeignKey("BIBLIOTECA.categories.id"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))

    category = relationship("Category", back_populates="books", lazy="select")
    authors = relationship(
        "Author",
        secondary=book_authors,
        back_populates="books",
        lazy="selectin",
    )
    loans = relationship("Loan", back_populates="book", lazy="select")
