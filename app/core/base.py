"""SQLAlchemy declarative base — import-safe, no engine creation."""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
