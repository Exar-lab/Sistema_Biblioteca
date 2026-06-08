"""Seed deterministic demo data into the Oracle library schema.

The script is idempotent by design:
- it upserts demo rows using natural keys,
- it reuses the Oracle package procedures for inserts and updates,
- it keeps demo identifiers clearly marked in usernames, ISBNs, names, and notes.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password as get_password_hash
from app.domain.models.author import Author
from app.domain.models.book import Book
from app.domain.models.category import Category
from app.domain.models.loan import Loan
from app.domain.models.return_ import Return_
from app.domain.models.role import Role
from app.domain.models.user import LibraryUser


DEMO_ANCHOR_DATE = date(2026, 6, 1)


@dataclass(frozen=True)
class DemoUserSeed:
    username: str
    full_name: str
    email: str
    phone: str | None
    password: str
    is_active: bool
    role_name: str


@dataclass(frozen=True)
class DemoCategorySeed:
    name: str
    description: str
    is_active: bool = True


@dataclass(frozen=True)
class DemoAuthorSeed:
    first_name: str
    last_name: str
    biography: str
    birth_date: date | None
    death_date: date | None
    is_active: bool = True


@dataclass(frozen=True)
class DemoBookSeed:
    title: str
    isbn: str
    description: str
    publication_date: date
    publisher: str
    edition: str
    pages: int
    stock_total: int
    # Final visible stock after loan/return history is seeded.
    stock_available: int
    is_active: bool
    category_name: str
    author_keys: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class DemoLoanSeed:
    username: str
    isbn: str
    loan_days_ago: int
    due_days_after_loan: int
    final_status: str
    return_days_after_loan: int | None = None
    fine_amount: Decimal = Decimal('0.00')
    notes: str | None = None


DEMO_USERS: tuple[DemoUserSeed, ...] = (
    DemoUserSeed(
        username="demo.admin",
        full_name="Demo Admin",
        email="demo.admin@library.local",
        phone="555-0101",
        password="DemoAdmin123!",
        is_active=True,
        role_name="Admin",
    ),
    DemoUserSeed(
        username="demo.alice",
        full_name="Demo Alice Reader",
        email="demo.alice@library.local",
        phone="555-0102",
        password="DemoUser123!",
        is_active=True,
        role_name="Usuario",
    ),
    DemoUserSeed(
        username="demo.ben",
        full_name="Demo Ben Reader",
        email="demo.ben@library.local",
        phone="555-0103",
        password="DemoUser123!",
        is_active=True,
        role_name="Usuario",
    ),
    DemoUserSeed(
        username="demo.clara",
        full_name="Demo Clara Reader",
        email="demo.clara@library.local",
        phone="555-0104",
        password="DemoUser123!",
        is_active=True,
        role_name="Usuario",
    ),
    DemoUserSeed(
        username="demo.dan",
        full_name="Demo Dan Reader",
        email="demo.dan@library.local",
        phone="555-0105",
        password="DemoUser123!",
        is_active=True,
        role_name="Usuario",
    ),
    DemoUserSeed(
        username="demo.valeria",
        full_name="Demo Valeria Reader",
        email="demo.valeria@library.local",
        phone="555-0106",
        password="DemoUser123!",
        is_active=False,
        role_name="Usuario",
    ),
)

DEMO_CATEGORIES: tuple[DemoCategorySeed, ...] = (
    DemoCategorySeed("Demo Technology", "Demo category for technical and systems titles."),
    DemoCategorySeed("Demo Science", "Demo category for science and databases titles."),
    DemoCategorySeed("Demo Fiction", "Demo category for narrative and literature titles."),
    DemoCategorySeed("Demo History", "Demo category for history and reference titles."),
    DemoCategorySeed("Demo Children", "Demo category for children and beginner titles."),
)

DEMO_AUTHORS: tuple[DemoAuthorSeed, ...] = (
    DemoAuthorSeed("Demo Ada", "Lovelace", "DEMO seed author for software and algorithms titles.", date(1815, 12, 10), date(1852, 11, 27)),
    DemoAuthorSeed("Demo Grace", "Hopper", "DEMO seed author for computing and compiler titles.", date(1906, 12, 9), date(1992, 1, 1)),
    DemoAuthorSeed("Demo Edgar", "Codd", "DEMO seed author for relational database titles.", date(1923, 8, 19), date(2003, 4, 18)),
    DemoAuthorSeed("Demo Mary", "Shelley", "DEMO seed author for classic literature titles.", date(1797, 8, 30), date(1851, 2, 1)),
    DemoAuthorSeed("Demo Yuval", "Harari", "DEMO seed author for history and world studies titles.", date(1976, 2, 24), None),
    DemoAuthorSeed("Demo Rosalind", "Franklin", "DEMO seed author for science and education titles.", date(1920, 7, 25), date(1958, 4, 16)),
    DemoAuthorSeed("Demo Whitfield", "Diffie", "DEMO seed author for security and cryptography titles.", date(1944, 5, 5), None),
    DemoAuthorSeed("Demo Martin", "Hellman", "DEMO seed author for security and cryptography titles.", date(1945, 10, 2), None),
)

DEMO_BOOKS: tuple[DemoBookSeed, ...] = (
    DemoBookSeed(
        title="DEMO: Applied Python Architecture",
        isbn="DEMO-ISBN-001",
        description="Demo title that supports category, author, loan, and report scenarios.",
        publication_date=date(2024, 1, 15),
        publisher="Demo Press",
        edition="1st",
        pages=320,
        stock_total=3,
        stock_available=1,
        is_active=True,
        category_name="Demo Technology",
        author_keys=(("Demo Ada", "Lovelace"), ("Demo Grace", "Hopper")),
    ),
    DemoBookSeed(
        title="DEMO: Modern Database Design",
        isbn="DEMO-ISBN-002",
        description="Demo title for relational modeling, indexes, and reporting.",
        publication_date=date(2023, 9, 21),
        publisher="Demo Press",
        edition="2nd",
        pages=280,
        stock_total=2,
        stock_available=1,
        is_active=True,
        category_name="Demo Science",
        author_keys=(("Demo Edgar", "Codd"),),
    ),
    DemoBookSeed(
        title="DEMO: Classic Stories Collection",
        isbn="DEMO-ISBN-003",
        description="Demo title for a returned and cancelled loan mix.",
        publication_date=date(2022, 5, 10),
        publisher="Demo Press",
        edition="3rd",
        pages=260,
        stock_total=2,
        stock_available=2,
        is_active=True,
        category_name="Demo Fiction",
        author_keys=(("Demo Mary", "Shelley"),),
    ),
    DemoBookSeed(
        title="DEMO: World History Atlas",
        isbn="DEMO-ISBN-004",
        description="Demo title for history reporting and low-stock coverage.",
        publication_date=date(2021, 3, 8),
        publisher="Demo Press",
        edition="1st",
        pages=410,
        stock_total=2,
        stock_available=1,
        is_active=True,
        category_name="Demo History",
        author_keys=(("Demo Yuval", "Harari"),),
    ),
    DemoBookSeed(
        title="DEMO: Science Experiments for Curious Kids",
        isbn="DEMO-ISBN-005",
        description="Demo title that keeps the children category represented in the seed.",
        publication_date=date(2024, 7, 1),
        publisher="Demo Press",
        edition="1st",
        pages=190,
        stock_total=2,
        stock_available=1,
        is_active=True,
        category_name="Demo Children",
        author_keys=(("Demo Rosalind", "Franklin"),),
    ),
    DemoBookSeed(
        title="DEMO: Network Security Basics",
        isbn="DEMO-ISBN-006",
        description="Demo title for multi-author coverage and an overdue-status loan.",
        publication_date=date(2024, 2, 28),
        publisher="Demo Press",
        edition="1st",
        pages=240,
        stock_total=2,
        stock_available=1,
        is_active=True,
        category_name="Demo Technology",
        author_keys=(("Demo Whitfield", "Diffie"), ("Demo Martin", "Hellman")),
    ),
)


def build_demo_loans() -> tuple[DemoLoanSeed, ...]:
    """Build demo loan records with deterministic relative dates."""

    return (
        DemoLoanSeed("demo.alice", "DEMO-ISBN-001", 5, 10, "ACTIVE"),
        DemoLoanSeed(
            "demo.alice",
            "DEMO-ISBN-001",
            35,
            14,
            "RETURNED",
            return_days_after_loan=10,
            notes="DEMO return record for reporting coverage.",
        ),
        DemoLoanSeed(
            "demo.alice",
            "DEMO-ISBN-001",
            65,
            14,
            "RETURNED",
            return_days_after_loan=11,
            fine_amount=Decimal('1.50'),
            notes="DEMO return with a small fine.",
        ),
        DemoLoanSeed("demo.alice", "DEMO-ISBN-001", 2, 14, "ACTIVE"),
        DemoLoanSeed("demo.ben", "DEMO-ISBN-002", 8, 3, "ACTIVE"),
        DemoLoanSeed(
            "demo.ben",
            "DEMO-ISBN-002",
            38,
            12,
            "RETURNED",
            return_days_after_loan=9,
            notes="DEMO return record for monthly coverage.",
        ),
        DemoLoanSeed(
            "demo.ben",
            "DEMO-ISBN-002",
            95,
            14,
            "RETURNED",
            return_days_after_loan=10,
            notes="DEMO oldest return record for monthly coverage.",
        ),
        DemoLoanSeed("demo.clara", "DEMO-ISBN-003", 12, 14, "CANCELLED"),
        DemoLoanSeed(
            "demo.clara",
            "DEMO-ISBN-003",
            42,
            14,
            "RETURNED",
            return_days_after_loan=11,
            notes="DEMO return record for cancellation coverage.",
        ),
        DemoLoanSeed("demo.dan", "DEMO-ISBN-004", 15, 14, "ACTIVE"),
        DemoLoanSeed(
            "demo.valeria",
            "DEMO-ISBN-005",
            18,
            10,
            "RETURNED",
            return_days_after_loan=7,
            notes="DEMO return record for the children category.",
        ),
        DemoLoanSeed("demo.valeria", "DEMO-ISBN-005", 3, 14, "ACTIVE"),
        DemoLoanSeed("demo.dan", "DEMO-ISBN-006", 25, 7, "OVERDUE"),
    )


def _callproc_out(session: Session, proc_name: str, args: list[object]) -> int:
    """Call an Oracle procedure that returns a numeric OUT id."""

    with session.connection().connection.cursor() as cursor:
        out_value = cursor.var(int)
        cursor.callproc(proc_name, [*args, out_value])
        value = out_value.getvalue()
        return int(value)


def _callproc(session: Session, proc_name: str, args: list[object]) -> None:
    """Call an Oracle procedure that only mutates rows."""

    with session.connection().connection.cursor() as cursor:
        cursor.callproc(proc_name, args)


def _bool_char(value: bool) -> str:
    return "Y" if value else "N"


def _fetch_one(session: Session, statement):
    return session.execute(statement).scalar_one_or_none()


def ensure_role(session: Session, name: str, description: str) -> Role:
    role = _fetch_one(session, select(Role).where(Role.name == name))
    if role is None:
        role_id = _callproc_out(session, "BIBLIOTECA.pkg_roles.p_insert", [name, description])
        session.expire_all()
        return session.get(Role, role_id)

    if role.description != description:
        _callproc(session, "BIBLIOTECA.pkg_roles.p_update", [role.id, name, description])
        session.expire_all()
        role = session.get(Role, role.id)
    return role


def ensure_user(session: Session, seed: DemoUserSeed, role_id: int) -> LibraryUser:
    user = _fetch_one(session, select(LibraryUser).where(LibraryUser.username == seed.username))
    password_hash = get_password_hash(seed.password)
    payload = [
        seed.username,
        seed.full_name,
        seed.email,
        seed.phone,
        password_hash,
        _bool_char(seed.is_active),
        role_id,
    ]

    if user is None:
        user_id = _callproc_out(session, "BIBLIOTECA.pkg_library_users.p_insert", payload)
        session.expire_all()
        return session.get(LibraryUser, user_id)

    _callproc(session, "BIBLIOTECA.pkg_library_users.p_update", [user.id, *payload])
    session.expire_all()
    return session.get(LibraryUser, user.id)


def ensure_category(session: Session, seed: DemoCategorySeed) -> Category:
    category = _fetch_one(session, select(Category).where(Category.name == seed.name))
    payload = [seed.name, seed.description, _bool_char(seed.is_active)]

    if category is None:
        category_id = _callproc_out(session, "BIBLIOTECA.pkg_categories.p_insert", payload)
        session.expire_all()
        return session.get(Category, category_id)

    _callproc(session, "BIBLIOTECA.pkg_categories.p_update", [category.id, *payload])
    session.expire_all()
    return session.get(Category, category.id)


def ensure_author(session: Session, seed: DemoAuthorSeed) -> Author:
    author = _fetch_one(
        session,
        select(Author).where(Author.first_name == seed.first_name, Author.last_name == seed.last_name),
    )
    payload = [
        seed.first_name,
        seed.last_name,
        seed.biography,
        seed.birth_date,
        seed.death_date,
        _bool_char(seed.is_active),
    ]

    if author is None:
        author_id = _callproc_out(session, "BIBLIOTECA.pkg_authors.p_insert", payload)
        session.expire_all()
        return session.get(Author, author_id)

    _callproc(session, "BIBLIOTECA.pkg_authors.p_update", [author.id, *payload])
    session.expire_all()
    return session.get(Author, author.id)


def ensure_book(
    session: Session,
    seed: DemoBookSeed,
    category_id: int,
) -> Book:
    book = _fetch_one(session, select(Book).where(Book.isbn == seed.isbn))
    payload = [
        seed.title,
        seed.isbn,
        seed.description,
        seed.publication_date,
        seed.publisher,
        seed.edition,
        seed.pages,
        seed.stock_total,
        seed.stock_total,
        _bool_char(seed.is_active),
        category_id,
    ]

    if book is None:
        book_id = _callproc_out(session, "BIBLIOTECA.pkg_books.p_insert", payload)
        session.expire_all()
        return session.get(Book, book_id)

    _callproc(session, "BIBLIOTECA.pkg_books.p_update", [book.id, *payload])
    session.expire_all()
    return session.get(Book, book.id)


def set_final_book_stock(
    session: Session,
    seed: DemoBookSeed,
    book_id: int,
    category_id: int,
) -> Book:
    """Set the final visible stock after demo circulation history is seeded."""

    _callproc(
        session,
        "BIBLIOTECA.pkg_books.p_update",
        [
            book_id,
            seed.title,
            seed.isbn,
            seed.description,
            seed.publication_date,
            seed.publisher,
            seed.edition,
            seed.pages,
            seed.stock_total,
            seed.stock_available,
            _bool_char(seed.is_active),
            category_id,
        ],
    )
    session.expire_all()
    return session.get(Book, book_id)


def ensure_book_authors(session: Session, book_id: int, author_ids: list[int]) -> None:
    _callproc(session, "BIBLIOTECA.pkg_books.p_clear_authors", [book_id])
    for author_id in author_ids:
        _callproc(session, "BIBLIOTECA.pkg_books.p_add_author", [book_id, author_id])
    session.expire_all()


def _loan_signature(session: Session, user_id: int, book_id: int, loan_date: date, due_date: date) -> Loan | None:
    return _fetch_one(
        session,
        select(Loan).where(
            Loan.user_id == user_id,
            Loan.book_id == book_id,
            Loan.loan_date == loan_date,
            Loan.due_date == due_date,
        ),
    )


def ensure_loan(session: Session, seed: DemoLoanSeed, user_id: int, book_id: int) -> int:
    loan_date = DEMO_ANCHOR_DATE - timedelta(days=seed.loan_days_ago)
    due_date = loan_date + timedelta(days=seed.due_days_after_loan)
    loan = _loan_signature(session, user_id, book_id, loan_date, due_date)

    if loan is None:
        loan_id = _callproc_out(session, "BIBLIOTECA.pkg_loans.p_insert", [user_id, book_id, loan_date, due_date])
        session.expire_all()
        loan = session.get(Loan, loan_id)
    else:
        loan_id = loan.id

    if seed.final_status in {"ACTIVE", "OVERDUE"}:
        if loan.status in {"ACTIVE", "OVERDUE"}:
            _callproc(
                session,
                "BIBLIOTECA.pkg_loans.p_update",
                [loan_id, user_id, book_id, loan_date, due_date, None, seed.final_status],
            )
            session.expire_all()
        return loan_id

    if seed.final_status == "CANCELLED":
        if loan.status == "ACTIVE":
            _callproc(
                session,
                "BIBLIOTECA.pkg_loans.p_update",
                [loan_id, user_id, book_id, loan_date, due_date, None, "ACTIVE"],
            )
            _callproc_out(session, "BIBLIOTECA.pkg_loans.p_cancel", [loan_id])
            session.expire_all()
        elif loan.status == "CANCELLED":
            _callproc(
                session,
                "BIBLIOTECA.pkg_loans.p_update",
                [loan_id, user_id, book_id, loan_date, due_date, None, "CANCELLED"],
            )
            session.expire_all()
        return loan_id

    if seed.final_status == "RETURNED":
        return_row = _fetch_one(session, select(Return_).where(Return_.loan_id == loan_id))
        return_date = loan_date + timedelta(days=seed.return_days_after_loan or 0)
        if loan.status == "RETURNED" and return_row is not None:
            _callproc(
                session,
                "BIBLIOTECA.pkg_loans.p_update",
                [loan_id, user_id, book_id, loan_date, due_date, return_date, "RETURNED"],
            )
            _callproc(
                session,
                "BIBLIOTECA.pkg_returns.p_update",
                [return_row.id, loan_id, return_date, seed.fine_amount, seed.notes],
            )
            session.expire_all()
            return loan_id

        if loan.status in {"ACTIVE", "OVERDUE"}:
            _callproc(
                session,
                "BIBLIOTECA.pkg_loans.p_update",
                [loan_id, user_id, book_id, loan_date, due_date, None, loan.status],
            )
            _callproc_out(
                session,
                "BIBLIOTECA.pkg_returns.p_process",
                [loan_id, return_date, seed.fine_amount, seed.notes],
            )
            session.expire_all()
            return loan_id

        if return_row is None:
            _callproc_out(
                session,
                "BIBLIOTECA.pkg_returns.p_process",
                [loan_id, return_date, seed.fine_amount, seed.notes],
            )
            session.expire_all()
        else:
            _callproc(
                session,
                "BIBLIOTECA.pkg_loans.p_update",
                [loan_id, user_id, book_id, loan_date, due_date, return_date, "RETURNED"],
            )
            _callproc(
                session,
                "BIBLIOTECA.pkg_returns.p_update",
                [return_row.id, loan_id, return_date, seed.fine_amount, seed.notes],
            )
            session.expire_all()
        return loan_id

    raise ValueError(f"Unsupported loan status: {seed.final_status}")


def seed_demo_data() -> None:
    """Seed the entire demo dataset in a single transaction."""

    loan_seeds = build_demo_loans()

    with SessionLocal() as session:
        try:
            admin_role = ensure_role(session, "Admin", "System administrator role.")
            user_role = ensure_role(session, "Usuario", "Default library user role.")

            role_ids = {"Admin": admin_role.id, "Usuario": user_role.id}
            users = {seed.username: ensure_user(session, seed, role_ids[seed.role_name]) for seed in DEMO_USERS}
            categories = {seed.name: ensure_category(session, seed) for seed in DEMO_CATEGORIES}
            authors = {
                (seed.first_name, seed.last_name): ensure_author(session, seed)
                for seed in DEMO_AUTHORS
            }
            books = {
                seed.isbn: ensure_book(session, seed, categories[seed.category_name].id)
                for seed in DEMO_BOOKS
            }

            for seed in DEMO_BOOKS:
                author_ids = [authors[key].id for key in seed.author_keys]
                ensure_book_authors(session, books[seed.isbn].id, author_ids)

            for seed in loan_seeds:
                ensure_loan(session, seed, users[seed.username].id, books[seed.isbn].id)

            for seed in DEMO_BOOKS:
                set_final_book_stock(session, seed, books[seed.isbn].id, categories[seed.category_name].id)

            session.commit()
        except Exception:
            session.rollback()
            raise


def main() -> None:
    seed_demo_data()
    print("Demo data seeded successfully.")
    print("Demo credentials:")
    print("- demo.admin / DemoAdmin123!")
    print("- demo.alice, demo.ben, demo.clara, demo.dan, demo.valeria / DemoUser123!")


if __name__ == "__main__":
    main()
