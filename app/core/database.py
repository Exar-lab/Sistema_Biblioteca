"""Synchronous SQLAlchemy setup for Oracle connectivity."""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.base import Base
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped DB session with commit/rollback lifecycle."""

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_db_smoke_check(db: Session) -> None:
    """Run a minimal Oracle connectivity check."""

    db.execute(text("SELECT 1 FROM DUAL"))


def is_database_available() -> bool:
    """Return True if smoke query succeeds; otherwise False."""

    try:
        with SessionLocal() as db:
            run_db_smoke_check(db)
        return True
    except SQLAlchemyError:
        return False
