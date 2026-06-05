# Spec: PR 2 — Python Repository Layer

**Change ID**: `oracle-stored-procedures`
**PR slice**: `pr2-python-repositories`
**Directory governed**: `app/infrastructure/repositories/`

---

## 1. Scope

This spec defines what MUST be true about the Python repository layer after PR 2 is merged.
It does not specify test coverage (PR 3) or Oracle schema details (PR 1).

---

## 2. Requirements

### 2.1 File Structure

**R-REPO-FILES-01** — The following files MUST exist after PR 2 is merged:

```
app/infrastructure/repositories/
    __init__.py
    role_repository.py
    user_repository.py
    category_repository.py
    author_repository.py
    book_repository.py
    loan_repository.py
    return_repository.py
```

**R-REPO-FILES-02** — Each repository file MUST export exactly one class that implements its matching Protocol from `app/application/ports/`.

### 2.2 Port Compliance

**R-PORT-01** — Every repository class MUST satisfy its Protocol via structural typing. The class MUST carry an explicit type annotation (`: <PortName>`) on the class or be registered with `typing.runtime_checkable` enforcement in tests.

**R-PORT-02** — Every repository class MUST implement the five base methods: `get_by_id(session, id)`, `list_all(session)`, `create(session, data)`, `update(session, id, data)`, `delete(session, id) -> bool`.

**R-PORT-03** — `BookRepository` MUST additionally implement: `get_with_authors(session, id)`, `set_authors(session, book_id, author_ids)`.

**R-PORT-04** — No repository class MUST add public methods beyond those declared in its Protocol. Private helpers (prefixed `_`) are allowed.

### 2.3 Write Path — Stored Procedures (MUST)

**R-WRITE-01** — Every `create` method MUST invoke the corresponding `p_insert` procedure. No `INSERT` SQL or ORM `session.add()` call is permitted inside any `create` method.

**R-WRITE-02** — Every `update` method MUST invoke the corresponding `p_update` procedure. No `UPDATE` SQL or ORM attribute assignment is permitted inside any `update` method.

**R-WRITE-03** — Every `delete` method MUST invoke the corresponding `p_delete` procedure. No `DELETE` SQL or ORM `session.delete()` call is permitted inside any `delete` method.

**R-WRITE-04** — For procedures that have only `IN` parameters (no OUT), the call MUST use:
```python
session.execute(
    text("BEGIN BIBLIOTECA.<pkg>.<proc>(:p1, :p2, ...); END;"),
    {"p1": value1, "p2": value2, ...},
)
```

**R-WRITE-05** — For procedures with `OUT` parameters (all `p_insert` calls that return the new ID), the call MUST use the raw DBAPI cursor obtained from the current SQLAlchemy session:
```python
raw = session.connection().connection.cursor()
out_id = raw.var(oracledb.NUMBER)
raw.callproc("BIBLIOTECA.<pkg>.p_insert", [..., out_id])
new_id = int(out_id.getvalue())
```
The cursor MUST be obtained from `session.connection().connection.cursor()`, never from a fresh `oracledb.connect()` call, to preserve transaction unity.

**R-WRITE-06** — The `create` method MUST return the domain object (or its ID) with the newly assigned PK populated from the OUT parameter.

**R-WRITE-07** — `BookRepository.set_authors(session, book_id, author_ids)` MUST:
1. Call `p_clear_authors` via `session.execute(text("BEGIN BIBLIOTECA.pkg_books.p_clear_authors(:b); END;"), {"b": book_id})`.
2. For each `author_id` in `author_ids`, call `p_add_author` via `session.execute(text("BEGIN BIBLIOTECA.pkg_books.p_add_author(:b, :a); END;"), {"b": book_id, "a": author_id})`.
3. Not use `session.add()`, direct INSERT, or any ORM mutation on `book_authors`.

**R-WRITE-08** — `LoanRepository.cancel(session, loan_id)` MUST call `pkg_loans.p_cancel` via `session.execute(...)`. This method is NOT part of the base Protocol but MUST be added as a repository-level extra method if the port Protocol declares it; otherwise the call signature is defined in this spec and the port Protocol MUST be extended in PR 2.

### 2.4 Read Path — SQLAlchemy ORM (MUST)

**R-READ-01** — Every `get_by_id` method MUST use SQLAlchemy 2.0 `select()` syntax. Using `session.query()` (legacy) is SHOULD NOT be used; if legacy style is present in existing code it MAY be kept but new code MUST use `select()`.

**R-READ-02** — Every `list_all` method MUST use `select()` against the matching ORM model class.

**R-READ-03** — `BookRepository.get_with_authors(session, id)` MUST use `select(Book).options(selectinload(Book.authors)).where(Book.id == id)` or equivalent eager-load strategy. It MUST NOT call a stored procedure or raw SQL string to perform the read.

**R-READ-04** — No `get_by_id` or `list_all` method MUST issue a raw SQL string (`text(...)`) for its SELECT. ORM `select()` is mandatory for all reads.

### 2.5 Transaction Boundaries

**R-TXN-01** — No repository method MUST call `session.commit()` or `session.rollback()`. Transaction control is owned by the service layer or unit-of-work caller.

**R-TXN-02** — No repository constructor MUST open a database connection or session. The `session` parameter is injected per-method call.

### 2.6 Import and Compilation

**R-COMPILE-01** — `python -m compileall app main.py` MUST exit with code 0 after PR 2 is merged.

**R-COMPILE-02** — All repository files MUST import only from:
- Python standard library
- `sqlalchemy` / `sqlalchemy.orm`
- `oracledb`
- `app.domain.models.*`
- `app.application.ports.*`
Any import from `app.presentation` or `app.infrastructure.repositories` (circular) is FORBIDDEN.

### 2.7 Boundary Rule Enforcement

**R-BOUNDARY-01** — No repository method MUST mix write path and read path in the same method body. A method that performs a write (procedure call) MUST NOT also issue an ORM `select()` within the same logical operation. If the created entity must be returned with its new state, the new ID is obtained from the OUT parameter and returned; a separate `get_by_id` call at the service layer is permitted.

---

## 3. Acceptance Scenarios

### SCENARIO-REPO-CREATE-01 — create() calls the correct package procedure

**Given** a `BookRepository` instance with a mocked SQLAlchemy session
**When** `create(session, book_data)` is called
**Then** `session.connection().connection.cursor().callproc` is called with `"BIBLIOTECA.pkg_books.p_insert"` as the first argument
**And** the bind list contains the correct column values
**And** the returned object has `id` set to the value returned by the OUT param

### SCENARIO-REPO-CREATE-02 — create() for loans does not pass stock arguments

**Given** a `LoanRepository` instance with a mocked session
**When** `create(session, loan_data)` is called
**Then** `callproc` is called with `"BIBLIOTECA.pkg_loans.p_insert"`
**And** the bind list does NOT include any stock-related parameter

### SCENARIO-REPO-UPDATE-01 — update() uses session.execute with text block

**Given** a `RoleRepository` instance with a mocked session
**When** `update(session, role_id, role_data)` is called
**Then** `session.execute` is called
**And** the first argument's text contains `"BIBLIOTECA.pkg_roles.p_update"`
**And** the bind dict includes `p_id = role_id` and the updated fields

### SCENARIO-REPO-DELETE-01 — delete() returns True on success

**Given** a `CategoryRepository` instance with a mocked session
**When** `delete(session, category_id)` is called and the procedure executes without error
**Then** `session.execute` is called with text containing `"BIBLIOTECA.pkg_categories.p_delete"`
**And** the method returns `True`

### SCENARIO-REPO-DELETE-02 — delete() returns False when entity not found

**Given** a `CategoryRepository` instance with a mocked session
**When** `delete(session, non_existent_id)` is called and the procedure raises a NO_DATA_FOUND-equivalent error
**Then** the method returns `False` without propagating the error

### SCENARIO-REPO-READ-01 — get_by_id() uses ORM select

**Given** a `AuthorRepository` instance with a mocked session
**When** `get_by_id(session, author_id)` is called
**Then** `session.execute` is called with a SQLAlchemy `select(Author)` construct (not a `text()` string)
**And** the WHERE clause filters on `Author.id == author_id`

### SCENARIO-REPO-READ-02 — list_all() uses ORM select without filter

**Given** a `UserRepository` instance with a mocked session
**When** `list_all(session)` is called
**Then** `session.execute` is called with a `select(LibraryUser)` construct
**And** no WHERE clause is applied

### SCENARIO-REPO-BOOKS-AUTHORS-01 — get_with_authors() uses eager load

**Given** a `BookRepository` instance with a mocked session
**When** `get_with_authors(session, book_id)` is called
**Then** `session.execute` is called with a `select(Book)` that includes `selectinload(Book.authors)` or equivalent
**And** no stored procedure is called

### SCENARIO-REPO-BOOKS-AUTHORS-02 — set_authors() clears then re-inserts

**Given** a `BookRepository` instance with a mocked session
**And** `author_ids = [10, 20]`
**When** `set_authors(session, book_id=5, author_ids=[10, 20])` is called
**Then** `session.execute` is called first with text containing `"pkg_books.p_clear_authors"` and bind `{"b": 5}`
**And** `session.execute` is called a second time with text containing `"pkg_books.p_add_author"` and bind `{"b": 5, "a": 10}`
**And** `session.execute` is called a third time with text containing `"pkg_books.p_add_author"` and bind `{"b": 5, "a": 20}`
**And** no ORM mutation on `book_authors` is issued

### SCENARIO-REPO-LOANS-CANCEL-01 — cancel() calls p_cancel procedure

**Given** a `LoanRepository` instance with a mocked session
**When** `cancel(session, loan_id=7)` is called
**Then** `session.execute` is called with text containing `"pkg_loans.p_cancel"`
**And** the bind dict contains the loan ID

### SCENARIO-REPO-TXN-01 — No commit inside repository

**Given** any repository instance with a mocked session
**When** any write method (`create`, `update`, `delete`) is called
**Then** `session.commit` is NEVER called
**And** `session.rollback` is NEVER called

### SCENARIO-REPO-CURSOR-01 — OUT-param cursor uses session's connection

**Given** a `BookRepository.create()` implementation
**When** a new book is created
**Then** the raw cursor is obtained via `session.connection().connection.cursor()`
**And** no new `oracledb.connect()` call is made

### SCENARIO-COMPILE-01 — Module compiles cleanly

**Given** the repository after PR 2 is merged
**When** `python -m compileall app main.py` is run
**Then** the command exits with code 0
**And** no `SyntaxError` or `ImportError` is produced

---

## 4. Rollback Plan

1. `git revert <pr2-sha>` removes `app/infrastructure/repositories/*.py`.
2. No Oracle schema changes are introduced by PR 2 — rollback is code-only, no DB cleanup required.
3. Application services (not yet wired) lose their concrete implementations; ports remain intact. The application will fail at runtime if services attempt to instantiate repositories, but no data loss occurs.

---

## 5. Out of Scope

- Oracle DDL (PR 1)
- pytest regression tests (PR 3)
- Application service layer wiring
- FastAPI route handlers
- Authentication / authorization
- Error translation from `oracledb.DatabaseError` to domain exceptions (deferred)
