# Technical Manual — Library Control System

**Version:** 0.1.0  
**Stack:** Python 3.10+ · FastAPI · SQLAlchemy (sync) · Oracle DB · pytest  
**Date:** 2026-06-08

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Project Structure](#3-project-structure)
4. [Domain Models](#4-domain-models)
5. [Application Layer](#5-application-layer)
6. [Infrastructure Layer](#6-infrastructure-layer)
7. [API Layer](#7-api-layer)
8. [Authentication and Security](#8-authentication-and-security)
9. [Configuration](#9-configuration)
10. [Database](#10-database)
11. [Error Handling](#11-error-handling)
12. [Testing](#12-testing)
13. [Local Setup](#13-local-setup)
14. [Demo Data](#14-demo-data)

---

## 1. Project Overview

The Library Control System is a REST API backend for managing the full lifecycle of a library: catalog management (books, authors, categories), user accounts, loan operations, returns, and administrative reports.

The application is built following **Hexagonal Architecture** (Ports and Adapters). Business logic lives in framework-free services; FastAPI and SQLAlchemy are implementation details behind ports.

A static frontend (HTML + CSS + vanilla JS) is served directly from FastAPI at `/` and `/static`, providing views for login, catalog, loans, returns, and the reports dashboard.

---

## 2. Architecture

### Hexagonal Architecture (Ports and Adapters)

```
┌─────────────────────────────────────────────────┐
│                   API Layer                      │
│    FastAPI routers · Pydantic schemas · Deps     │
└────────────────────┬────────────────────────────┘
                     │ calls
┌────────────────────▼────────────────────────────┐
│               Application Layer                  │
│    Services · Ports (Protocols) · Errors         │
│    No FastAPI · No SQLAlchemy imports            │
└────────────────────┬────────────────────────────┘
                     │ implements
┌────────────────────▼────────────────────────────┐
│             Infrastructure Layer                 │
│    SQLAlchemy repositories · Oracle adapters     │
└─────────────────────────────────────────────────┘
```

**Key rule:** The application layer has zero knowledge of FastAPI or SQLAlchemy. It depends only on port interfaces (Python `Protocol`) and raises framework-free exceptions from `app/application/errors.py`.

### Dependency Flow per Request

```
HTTP Request
  → FastAPI Router
    → get_db() yields Session
    → Service (injected via Depends)
      → Repository Port (Protocol)
        → SQLAlchemy / Oracle (Infrastructure)
  ← Response serialized by Pydantic schema
```

---

## 3. Project Structure

```
Sistema_Biblioteca/
├── main.py                            # FastAPI app factory, health endpoint, router registration
├── app/
│   ├── api/
│   │   ├── exception_handlers.py      # Maps domain errors → HTTP status codes
│   │   ├── dependencies.py            # Shared FastAPI dependencies (get_current_user, AdminOnly)
│   │   └── v1/routers/               # One file per domain
│   │       ├── auth.py               # POST /login, POST /register, GET /me, PATCH /me/password
│   │       ├── authors.py
│   │       ├── books.py
│   │       ├── categories.py
│   │       ├── loans.py
│   │       ├── returns.py
│   │       ├── roles.py
│   │       ├── reports.py
│   │       └── users.py
│   ├── application/
│   │   ├── errors.py                  # Domain exceptions (no HTTP, no SQLAlchemy)
│   │   ├── ports/                     # Repository contracts (Protocol classes)
│   │   └── services/                  # Business use cases
│   ├── domain/
│   │   └── models/                    # SQLAlchemy ORM models
│   ├── infrastructure/
│   │   └── repositories/             # Concrete SQLAlchemy + Oracle implementations
│   ├── schemas/                       # Pydantic request / response models
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── roles.py
│   │   ├── dashboard.py
│   │   ├── catalog/                   # authors.py, books.py, categories.py
│   │   └── circulation/              # loans.py, returns.py
│   ├── core/
│   │   ├── config.py                  # pydantic-settings Settings class
│   │   ├── database.py               # Engine, SessionLocal, get_db, smoke check
│   │   ├── security.py               # bcrypt hashing, JWT sign / decode
│   │   └── base.py                   # SQLAlchemy declarative Base
│   └── static/                       # Static frontend (HTML, CSS, JS)
├── database/
│   └── oracle_schema.sql             # Oracle DDL: tables, triggers, sequences, indexes
├── scripts/
│   └── seed_demo_data.py             # Deterministic demo data seeder
└── tests/
    ├── conftest.py                    # Environment defaults for tests
    ├── integration/                  # Repository integration tests (requires Oracle)
    └── unit/                         # Unit tests with mocked sessions
```

---

## 4. Domain Models

All ORM models live in `app/domain/models/` and use `schema="BIBLIOTECA"` to scope every table to the Oracle `BIBLIOTECA` user.

### LibraryUser (`library_users`)

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Autoincrement via Oracle sequence |
| `username` | String(50) | Unique |
| `full_name` | String(120) | |
| `email` | String(255) | Unique |
| `phone` | String(30) | Nullable |
| `password_hash` | String(255) | bcrypt hash |
| `is_active` | BoolChar (`'Y'`/`'N'`) | Default `'Y'` |
| `role_id` | FK → roles | |
| `created_at`, `updated_at` | TIMESTAMP | Server default `SYSTIMESTAMP` |

Relationships: `role` (many-to-one), `loans` (one-to-many).

### Book (`books`)

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `title` | String(200) | |
| `isbn` | String(20) | Unique, nullable |
| `description` | String(4000) | Nullable |
| `publication_date` | Date | Nullable |
| `publisher` | String(120) | Nullable |
| `edition` | String(40) | Nullable |
| `pages` | Integer | Nullable |
| `stock_total` | Integer | Default 0 |
| `stock_available` | Integer | Default 0; decremented by `trg_loans_decrement_stock` |
| `is_active` | BoolChar | Default `'Y'` |
| `category_id` | FK → categories | Nullable |

Relationships: `category` (many-to-one), `authors` (many-to-many via `book_authors`), `loans` (one-to-many).

### Loan (`loans`)

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → library_users | |
| `book_id` | FK → books | |
| `loan_date` | Date | Default `TRUNC(SYSDATE)` |
| `due_date` | Date | |
| `return_date` | Date | Nullable; set on return |
| `status` | String(20) | `ACTIVE`, `RETURNED`, `CANCELLED` |

Relationships: `user`, `book`, `return_` (one-to-one).

### Other Models

- **Author** (`authors`): `id`, `name`, `bio`, `is_active`, timestamps.
- **Category** (`categories`): `id`, `name`, `description`, `is_active`, timestamps.
- **Role** (`roles`): `id`, `name`, `description`, timestamps.
- **Return_** (`returns`): `id`, `loan_id` (FK, unique), `return_date`, `notes`, timestamps.

### BoolChar Type

Oracle does not have a native boolean. The project uses a custom SQLAlchemy `TypeDecorator` (`BoolChar`) that stores `'Y'` / `'N'` in `CHAR(1)` and exposes `True` / `False` to Python.

---

## 5. Application Layer

### Ports (`app/application/ports/`)

Each domain has a `Protocol` interface that declares the contract for its repository. Services depend on these protocols, never on the concrete SQLAlchemy implementations.

Example — `LoanRepository` port:

```python
class LoanRepository(Protocol):
    def get_by_id(self, session, id) -> Loan | None: ...
    def list_all(self, session) -> list[Loan]: ...
    def create(self, session, data) -> Loan: ...          # raises OutOfStockError
    def update(self, session, id, data) -> Loan | None: ...
    def delete(self, session, id) -> bool: ...
    def get_by_user(self, session, user_id) -> list[Loan]: ...
    def get_by_book(self, session, book_id) -> list[Loan]: ...
    def has_overdue_loans(self, session, user_id) -> bool: ...
    def cancel(self, session, loan_id) -> bool: ...
```

### Services (`app/application/services/`)

Services orchestrate use cases by calling ports and raising domain errors. They import no FastAPI or SQLAlchemy symbols.

| Service | Responsibilities |
|---|---|
| `AuthService` | Login (validates credentials, issues JWT), register, change password |
| `AuthorService` | CRUD authors, raises `NotFoundError` |
| `BookService` | CRUD books including author assignments |
| `CategoryService` | CRUD categories |
| `LoanService` | Create/update/cancel loans, validates user active state and overdue status |
| `ReturnService` | Creates return records, updates loan status |
| `RoleService` | CRUD roles |
| `ReportService` | Aggregates dashboard metrics |
| `UserService` | Admin user management |

### Domain Errors (`app/application/errors.py`)

| Exception | Meaning |
|---|---|
| `NotFoundError` | Resource does not exist |
| `OutOfStockError` | No available stock for a new loan |
| `ConflictError` | Duplicate or conflicting record |
| `InvalidCredentialsError` | Bad username or password |
| `InactiveUserError` | Inactive user attempted an action |

---

## 6. Infrastructure Layer

### SQLAlchemy Repositories (`app/infrastructure/repositories/`)

Concrete implementations of the port protocols. Pattern:

- **Reads** use SQLAlchemy ORM `select()` queries.
- **Writes** for loans and returns delegate exclusively to Oracle **stored procedures** (`pkg_loans`, `pkg_returns`) via `callproc`.
- No `session.commit()` or `session.rollback()` inside repositories — the session lifecycle is owned by `get_db()` in the API layer.

### Loan Repository — Stored Procedure Integration

```python
# Insert via pkg_loans.p_insert with an OUT parameter for the new ID
with session.connection().connection.cursor() as cur:
    out_id = cur.var(int)
    cur.callproc("BIBLIOTECA.pkg_loans.p_insert", [
        data.user_id, data.book_id, data.loan_date, data.due_date, out_id
    ])
    new_id = out_id.getvalue()
session.expire_all()
return self.get_by_id(session, new_id)
```

`session.expire_all()` is called after every write so the subsequent ORM read reflects the Oracle-side changes (stock decrements, trigger updates).

**ORA-20001 detection:** the Oracle trigger `trg_loans_decrement_stock` raises `-20001` when stock is zero. The repository catches this and translates it to `OutOfStockError`.

---

## 7. API Layer

### Router Registration (`main.py`)

All routers are mounted under `/api/v1`:

```
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/auth/me
PATCH  /api/v1/auth/me/password

GET    /api/v1/authors          POST /api/v1/authors
GET    /api/v1/authors/{id}     PATCH /api/v1/authors/{id}    DELETE /api/v1/authors/{id}

GET    /api/v1/books            POST /api/v1/books
GET    /api/v1/books/{id}       PATCH /api/v1/books/{id}      DELETE /api/v1/books/{id}

GET    /api/v1/categories       POST /api/v1/categories
GET    /api/v1/categories/{id}  PATCH /api/v1/categories/{id} DELETE /api/v1/categories/{id}

GET    /api/v1/loans            POST /api/v1/loans
POST   /api/v1/loans/me                                       (self-service borrow)
GET    /api/v1/loans/{id}       PATCH /api/v1/loans/{id}
PATCH  /api/v1/loans/{id}/return
PATCH  /api/v1/loans/{id}/cancel
GET    /api/v1/loans/users/{user_id}
GET    /api/v1/loans/books/{book_id}

GET    /api/v1/returns          POST /api/v1/returns
GET    /api/v1/returns/{id}

GET    /api/v1/roles            POST /api/v1/roles
GET    /api/v1/roles/{id}       PATCH /api/v1/roles/{id}      DELETE /api/v1/roles/{id}

GET    /api/v1/users            POST /api/v1/users
GET    /api/v1/users/{id}       PATCH /api/v1/users/{id}      DELETE /api/v1/users/{id}

GET    /api/v1/reports/dashboard

GET    /health
```

### Authorization Levels

| Dependency | Who can use |
|---|---|
| `get_current_user` | Any authenticated user (validates Bearer token) |
| `AdminOnly` | Only users with role `"admin"` (returns 403 otherwise) |

Loans follow a mixed model: listing and creating by user ID require admin; `POST /loans/me` and returning own loans work for any authenticated user.

---

## 8. Authentication and Security

### JWT Flow

1. Client sends `POST /api/v1/auth/login` with `{ username, password }`.
2. `AuthService.authenticate()` verifies the bcrypt hash with `verify_password()`.
3. On success, `create_access_token()` signs a JWT containing `sub` (user ID), `username`, and `role`.
4. Response returns `{ access_token, token_type: "bearer", user: UserRead }`.
5. Subsequent requests include `Authorization: Bearer <token>`.
6. `get_current_user` dependency decodes the token with `decode_token()` and loads the user from DB.

### Token Configuration

| Setting | Default | Description |
|---|---|---|
| `SECRET_KEY` | Required | Signing key (must be kept secret) |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime in minutes |

### Password Hashing

`passlib` with `bcrypt` scheme. No plain-text passwords are ever stored or returned in responses.

---

## 9. Configuration

Settings are loaded from `.env` via `pydantic-settings`. The `get_settings()` function is cached with `@lru_cache` so the `.env` file is read only once per process.

```
DATABASE_URL=oracle+oracledb://BIBLIOTECA:password@localhost:1521/?service_name=XEPDB1
SECRET_KEY=your-secret-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SQLALCHEMY_ECHO=false
```

Copy `.env.example` to `.env` to get started.

---

## 10. Database

### Engine Setup

Synchronous SQLAlchemy engine using `oracledb` (thin mode by default):

```python
engine = create_engine(settings.DATABASE_URL, echo=settings.SQLALCHEMY_ECHO)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

### Session Lifecycle

`get_db()` is a FastAPI dependency that yields a session and manages commit/rollback:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### Oracle Schema (`database/oracle_schema.sql`)

The script runs as `SYS`/DBA and creates (or re-creates idempotently):

- **User:** `BIBLIOTECA` with all required grants.
- **Tables:** `library_users`, `roles`, `books`, `authors`, `categories`, `book_authors`, `loans`, `returns`.
- **Sequences:** One per table for primary key generation.
- **Triggers:**
  - `trg_loans_decrement_stock` — decrements `books.stock_available` on loan insert; raises `ORA-20001` when stock is zero.
  - `trg_returns_increment_stock` — increments `books.stock_available` on return insert.
- **Stored Procedures:** `pkg_loans` and `pkg_returns` packages for write operations.
- **Indexes:** On foreign keys and frequently filtered columns.

### Healthcheck

```
GET /health → { "status": "ok", "database": "up" }   # 200
            → { "status": "error", "database": "down" } # 503
```

Executes `SELECT 1 FROM DUAL` to verify Oracle connectivity.

---

## 11. Error Handling

Exception handlers registered in `app/api/exception_handlers.py` translate domain errors to HTTP responses with a consistent shape:

```json
{ "detail": "<error message>" }
```

| Domain Exception | HTTP Status |
|---|---|
| `NotFoundError` | 404 Not Found |
| `ConflictError` | 409 Conflict |
| `OutOfStockError` | 409 Conflict |
| `InvalidCredentialsError` | 401 Unauthorized |
| `InactiveUserError` | 403 Forbidden |

FastAPI's default `RequestValidationError` still returns 422 for malformed request bodies (Pydantic validation failures).

---

## 12. Testing

### Layout

```
tests/
├── conftest.py                      # Sets DATABASE_URL and SECRET_KEY env vars for tests
├── test_health_and_db_lifecycle.py
├── test_authors_slice.py
├── test_categories_slice.py
├── test_reports_slice.py
├── test_roles_slice.py
├── unit/
│   └── repositories/
│       ├── test_loan_repository.py
│       ├── test_return_repository.py
│       └── test_role_repository.py
└── integration/
    └── test_repositories_integration.py  # Requires live Oracle connection
```

### Running Tests

```powershell
# All tests (unit only if Oracle unavailable)
python -m pytest

# Specific slice
python -m pytest tests/test_authors_slice.py -v

# Integration tests (requires Oracle)
python -m pytest tests/integration/ -v
```

### Test Defaults (`conftest.py`)

Sets fake values so unit tests don't fail on missing env:

```python
os.environ.setdefault("DATABASE_URL", "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-jwt-auth")
```

---

## 13. Local Setup

### Prerequisites

- Python 3.10+
- Oracle XE with the `XEPDB1` (or `FREEPDB1`) PDB active
- `sqlplus` available for schema bootstrap

### Steps

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Configure environment
Copy-Item .env.example .env
# Edit .env with DATABASE_URL and SECRET_KEY

# 4. Bootstrap Oracle schema (run as SYS/DBA)
sqlplus / as sysdba @database/oracle_schema.sql

# 5. Seed demo data (optional)
python scripts/seed_demo_data.py

# 6. Start the server
uvicorn main:app --reload
```

### Verify Syntax (pre-run check)

```powershell
python -m compileall app main.py scripts
```

### API Documentation

With the server running, visit:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **Frontend:** `http://127.0.0.1:8000/`

---

## 14. Demo Data

The script `scripts/seed_demo_data.py` inserts a deterministic dataset with fixed dates so loan history stays reproducible across runs. Safe to re-run.

### Demo Credentials

| Username | Password | Role |
|---|---|---|
| `demo.admin` | `DemoAdmin123!` | Admin |
| `demo.alice` | `DemoUser123!` | Usuario |
| `demo.ben` | `DemoUser123!` | Usuario |
| `demo.clara` | `DemoUser123!` | Usuario |
| `demo.dan` | `DemoUser123!` | Usuario |
| `demo.valeria` | `DemoUser123!` | Usuario |

### Validate Database Objects

```sql
SELECT object_name, object_type, status
FROM user_objects
WHERE object_type IN ('TABLE', 'TRIGGER', 'INDEX', 'SEQUENCE')
ORDER BY object_type, object_name;
```
