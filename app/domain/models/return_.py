"""Return_ ORM model."""

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, TIMESTAMP, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Return_(Base):
    """Maps to BIBLIOTECA.returns.

    No 'condition' or 'processed_by_user_id' columns — not present in oracle_schema.sql.
    Trailing underscore avoids collision with Python built-in 'return'.
    """

    __tablename__ = "returns"
    __table_args__ = {"schema": "BIBLIOTECA"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("BIBLIOTECA.loans.id"), nullable=False, unique=True)
    return_date = Column(Date, nullable=False, server_default=text("TRUNC(SYSDATE)"))
    fine_amount = Column(Numeric(10, 2), nullable=False, server_default=text("0"))
    notes = Column(String(1000), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("SYSTIMESTAMP"))

    loan = relationship("Loan", back_populates="return_", lazy="select")
