"""Loan ORM model."""

from sqlalchemy import Column, Date, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Loan(Base):
    """Maps to BIBLIOTECA.loans.

    No 'notes' column — not present in oracle_schema.sql.
    """

    __tablename__ = "loans"
    __table_args__ = {"schema": "BIBLIOTECA"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("BIBLIOTECA.library_users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("BIBLIOTECA.books.id"), nullable=False)
    loan_date = Column(Date, nullable=False, server_default=text("TRUNC(SYSDATE)"))
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, server_default=text("'ACTIVE'"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))

    user = relationship("LibraryUser", back_populates="loans", lazy="select")
    book = relationship("Book", back_populates="loans", lazy="select")
    return_ = relationship("Return_", back_populates="loan", uselist=False, lazy="select")
