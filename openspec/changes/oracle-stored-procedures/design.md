# Design: Oracle Stored Procedures + Repository Layer

**Change ID**: `oracle-stored-procedures`
**Project**: `sistema_biblioteca`
**Architecture style**: Hexagonal (ports & adapters) with CQRS-lite write/read split

---

## 1. Architectural Approach

### Pattern
- **Hexagonal / Ports & Adapters**: domain + application ports already exist; this change implements the persistence adapter.
- **CQRS-lite write/read split**:
  - **Writes (Commands)** → PL/SQL stored procedures owned by Oracle (`BIBLIOTECA.pkg_*`).
  - **Reads (Queries)** → SQLAlchemy 2.0 ORM (`select()`) against existing models.
- **Aggregate-aligned packages**: one PL/SQL package per aggregate root (`pkg_roles`, `pkg_library_users`, `pkg_categories`, `pkg_authors`, `pkg_books`, `pkg_loans`, `pkg_returns`).
- **Repository per aggregate**: one Python file per aggregate in `app/infrastructure/repositories/`, implementing the matching Protocol port.

### Boundary rule (the contract)
> All INSERT / UPDATE / DELETE flow through stored procedures.
> All SELECT flows through SQLAlchemy ORM.
> No mixing inside a single method.

This is a hard rule, not a preference — it is mandated by the academic rubric.

---

## 2. Component Map

```
┌────────────────────────────────────────────────────────────────┐
│ app/application/ports/  (Protocols — already exist)            │
│   book_repository_port.py, author_repository_port.py, ...      │
└──────────────────────────┬─────────────────────────────────────┘
                           │ implements
                           ▼
┌────────────────────────────────────────────────────────────────┐
│ app/infrastructure/repositories/  (NEW — PR 2)                 │
│   book_repository.py        ── writes via pkg_books.*          │
│   author_repository.py      ── writes via pkg_authors.*        │
│   category_repository.py    ── writes via pkg_categories.*     │
│   loan_repository.py        ── writes via pkg_loans.*          │
│   return_repository.py      ── writes via pkg_returns.*        │
│   role_repository.py        ── writes via pkg_roles.*          │
│   user_repository.py        ── writes via pkg_library_users.*  │
│                                                                │
│   reads → SQLAlchemy select() over app/domain/models/*         │
└──────────────────────────┬─────────────────────────────────────┘
                           │ session.execute(text("BEGIN ... END;"))
                           ▼
┌────────────────────────────────────────────────────────────────┐
│ Oracle BIBLIOTECA schema  (PR 1 additions)                     │
│   seq_roles, seq_library_users, seq_categories, seq_authors,   │
│   seq_books, seq_loans, seq_returns                            │
│   pkg_roles, pkg_library_users, pkg_categories, pkg_authors,   │
│   pkg_books, pkg_loans, pkg_returns                            │
│                                                                │
│   Existing (unchanged): tables, FKs, updated_at triggers,      │
│   trg_loans_checkout_stock, trg_returns_restore_stock          │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow

### Write path (e.g. create a book with authors)
```
Service / caller
   │
   ▼
BookRepository.create(book)                       ← Python repo
   │
   ▼
session.execute(text("BEGIN BIBLIOTECA.pkg_books.p_insert(...); END;"),
                bind_params)                      ← anonymous PL/SQL block
   │
   ▼
pkg_books.p_insert                                ← PL/SQL procedure
   │
   ├── seq_books.NEXTVAL → :p_id_out               (OUT bind)
   ├── INSERT INTO books (...)
   ▼
(trigger trg_books_updated_at fires)
   │
   ▼
returns p_id_out to Python; repo sets book.id

For authors:
BookRepository.set_authors(book_id, author_ids)
   │
   ▼
loops author_ids → pkg_books.p_clear_authors(book_id)
                 → pkg_books.p_add_author(book_id, author_id) per id
```

### Read path (e.g. get book with authors)
```
Service / caller
   │
   ▼
BookRepository.get_with_authors(book_id)
   │
   ▼
session.execute(
    select(Book)
      .options(selectinload(Book.authors))
      .where(Book.id == book_id)
).scalar_one_or_none()
   │
   ▼
SQLAlchemy emits SELECT + IN(...) for the join table
   │
   ▼
returns Book ORM instance (with .authors populated)
```

### Loan / return special flows
- `pkg_loans.p_insert` — INSERT into `loans`; the existing `trg_loans_checkout_stock` decrements `books.stock` and raises if no stock. The procedure must NOT also decrement stock (trigger owns it).
- `pkg_loans.p_cancel(p_loan_id)` — sets `loans.status = 'CANCELLED'`. Does NOT restore stock (cancellation ≠ return). Raises if status is already `RETURNED` or `CANCELLED`.
- `pkg_returns.p_process(p_loan_id, p_return_date, p_fine_amount, p_notes)` — INSERT into `returns`. The existing `trg_returns_restore_stock` flips `loans.status = 'RETURNED'` and increments `books.stock`.

---

## 4. Integration Points

| Boundary | Protocol | Owner |
|---|---|---|
| Application ↔ Repository | Python `Protocol` (structural) in `app/application/ports/` | Application layer |
| Repository ↔ Oracle (writes) | Anonymous PL/SQL block via `session.execute(text(...), binds)` | Infrastructure |
| Repository ↔ Oracle (reads) | SQLAlchemy 2.0 Core/ORM `select()` | Infrastructure |
| Procedure ↔ Trigger | Implicit (trigger fires on table DML inside procedure) | Oracle schema |
| Test ↔ Repository | `unittest.mock.MagicMock` patching `Session.execute` | Tests |

---

## 5. ADR-Style Decisions

### ADR-1 — Add explicit sequences alongside existing IDENTITY columns
**Decision**: Add `seq_<table>` sequences for every table that already uses `GENERATED BY DEFAULT AS IDENTITY`. Procedures call `seq_<table>.NEXTVAL` to assign the PK explicitly.

**Rationale**:
- Academic rubric expects explicit sequence objects as visible artifacts.
- `GENERATED BY DEFAULT AS IDENTITY` (not `ALWAYS`) tolerates explicit values, so passing `NEXTVAL` works without changing column definitions.
- Keeps backward compatibility with any ad-hoc inserts during development.

**Rejected**:
- *Drop IDENTITY, sequences-only*: would require ALTER TABLE on every PK column, risk side effects on existing rows.
- *Sequences only, no IDENTITY change*: chosen.
- *IDENTITY only, no sequences*: fails rubric requirement for explicit sequence artifacts.

**Trade-off**: dual ownership of ID generation is documented in the schema header so reviewers know procedures are authoritative.

---

### ADR-2 — One PL/SQL package per aggregate root
**Decision**: Group procedures by aggregate, not by operation type. Packages: `pkg_roles`, `pkg_library_users`, `pkg_categories`, `pkg_authors`, `pkg_books`, `pkg_loans`, `pkg_returns`.

**Standard signatures** (per aggregate):
```
PROCEDURE p_insert (... per-table columns ..., p_id OUT NUMBER);
PROCEDURE p_update (p_id IN NUMBER, ... per-table columns ...);
PROCEDURE p_delete (p_id IN NUMBER);
```

**Extra procedures** (only where the aggregate needs them):
- `pkg_books.p_add_author    (p_book_id IN NUMBER, p_author_id IN NUMBER)`
- `pkg_books.p_remove_author (p_book_id IN NUMBER, p_author_id IN NUMBER)`
- `pkg_books.p_clear_authors (p_book_id IN NUMBER)`
- `pkg_loans.p_cancel        (p_loan_id IN NUMBER)`
- `pkg_returns.p_process     (p_loan_id IN NUMBER, p_return_date IN DATE, p_fine_amount IN NUMBER, p_notes IN VARCHAR2)`

**Rationale**: aggregate-aligned packages map 1:1 to repository files, keep related operations together, and let `CREATE OR REPLACE PACKAGE` re-deploy a whole aggregate atomically.

**Rejected**:
- *One mega-package*: hurts diff review, replacing it touches all aggregates.
- *One procedure per file (no packages)*: loses encapsulation, more DDL noise, no shared private helpers later.

---

### ADR-3 — Use anonymous PL/SQL block via `session.execute(text(...))` for procedure calls
**Decision**: Repositories invoke procedures with:
```python
session.execute(
    text("BEGIN BIBLIOTECA.pkg_books.p_insert(:title, :isbn, ..., :p_id_out); END;"),
    {"title": ..., "isbn": ..., "p_id_out": ...},
)
```

For procedures with OUT parameters (e.g. returning the new ID), drop to the raw DBAPI cursor:
```python
raw = session.connection().connection.cursor()
out_id = raw.var(oracledb.NUMBER)
raw.callproc("BIBLIOTECA.pkg_books.p_insert", [title, isbn, ..., out_id])
new_id = int(out_id.getvalue())
```

**Rationale**:
- `text("BEGIN ... END;")` keeps the call inside the SQLAlchemy session (same transaction, same connection pool) for procedures with no OUT params.
- For OUT params, `callproc` on the raw cursor is the cleanest oracledb pattern; using the underlying connection of the SQLAlchemy session preserves the transaction.
- Both patterns are mockable in tests (mock `session.execute` or `session.connection().connection.cursor()`).

**Rejected**:
- *`CALL pkg.proc(...)` SQL syntax*: oracledb supports it, but it's less ergonomic for OUT params and mixes Oracle dialect quirks.
- *Always use raw cursor `callproc`*: unnecessary for simple INPUT-only procs and harder to mock uniformly.
- *Pure DBAPI without SQLAlchemy session*: breaks transaction unity with reads.

**Pattern boundary**: simple input-only procs → `session.execute(text(...))`. Any proc with OUT (e.g. all `p_insert`) → raw cursor `callproc`.

---

### ADR-4 — Strict write-via-procedure / read-via-ORM split
**Decision**: Repositories perform every CUD operation through a stored procedure. Every read goes through SQLAlchemy ORM `select()`. No method mixes both.

**Rationale**: rubric requirement. Also creates a clean mental model: "if it mutates state, it's a procedure call."

**Rejected**:
- *ORM writes with hand-written SQL inserts for special cases*: ambiguous boundary, fails rubric.
- *Stored-procedure reads via SYS_REFCURSOR for everything*: enormous complexity for zero domain benefit; existing ORM models already shape the data correctly.

**Exception clause**: none. If a future case demands a procedure that returns data, it goes through SYS_REFCURSOR and is explicitly documented as a deviation in that procedure's header comment.

---

### ADR-5 — Manage `book_authors` link table via per-author procedure calls in a loop
**Decision**: `BookRepository.set_authors(book_id, author_ids)` implementation:
```python
def set_authors(self, book_id: int, author_ids: list[int]) -> None:
    self._session.execute(
        text("BEGIN BIBLIOTECA.pkg_books.p_clear_authors(:b); END;"),
        {"b": book_id},
    )
    for aid in author_ids:
        self._session.execute(
            text("BEGIN BIBLIOTECA.pkg_books.p_add_author(:b, :a); END;"),
            {"b": book_id, "a": aid},
        )
```

**Rationale**: simplest viable approach. Oracle collection types (`TABLE OF NUMBER`) are powerful but require schema-level type DDL (`CREATE TYPE`) and oracledb-side array binding, which is overkill for a link table that typically holds 1–5 authors per book.

**Rejected**:
- *Pass a collection type `t_id_list`*: more DDL, more oracledb-specific binding, premature optimization.
- *One bulk procedure that takes a comma-separated string*: fragile, hard to test.

**Trade-off**: N+1 procedure calls for N authors. Acceptable because N is tiny and this runs only on book create/update.

---

### ADR-6 — Loan cancellation does NOT restore stock
**Decision**: `pkg_loans.p_cancel(p_loan_id)` only sets `loans.status = 'CANCELLED'`. It does not touch `books.stock`.

**Rationale**: a cancellation models "this loan never effectively happened in business terms", but the existing `trg_loans_checkout_stock` already decremented stock at INSERT time. We have two reasonable models:
1. Cancellation reverses the checkout → restore stock.
2. Cancellation is an audit marker → leave stock alone (a manual return is still required to restore).

We pick (2) because:
- It matches the trigger's current behavior (only `trg_returns_restore_stock` restores stock, on actual return).
- Adding stock restoration to `p_cancel` would either duplicate the trigger logic or require a synthetic `returns` row, which lies about reality.
- The operational story is: "if a loan was created in error, cancel it AND create a corrective return entry" — clean separation of concerns.

**Rejected**:
- *p_cancel also restores stock*: violates single-responsibility of the trigger.
- *p_cancel forbidden, only delete*: loses audit trail.

**Documented constraint**: `p_cancel` must raise if `status IN ('RETURNED', 'CANCELLED')` to prevent double-cancel.

---

### ADR-7 — Returns processed via thin procedure that delegates to existing trigger
**Decision**: `pkg_returns.p_process(p_loan_id, p_return_date, p_fine_amount, p_notes)` simply INSERTs into `returns`. The existing `trg_returns_restore_stock` trigger handles the side effects (set loan to RETURNED, increment stock).

**Rationale**: the trigger already exists and is tested behaviorally by the schema. Re-implementing its logic in the procedure would create two sources of truth. The procedure exists purely to satisfy the "writes go through procedures" rule.

**Rejected**:
- *Move trigger logic into the procedure, drop the trigger*: more invasive, breaks the existing schema contract that the trigger represents.
- *Procedure does INSERT and explicit UPDATE on loans*: duplicates trigger work, risk of double-update.

---

### ADR-8 — Test isolation via mocked `session.execute`
**Decision**: Unit tests do NOT require a live Oracle. They:
- Mock `session.execute` and assert (a) the SQL text contains the expected package + procedure name, (b) the bind dict matches the expected shape and values.
- For OUT-param paths, mock `session.connection().connection.cursor()` and assert `callproc` was called with the right args.
- For reads, build the expected `select()` and compare via `.compile(compile_kwargs={"literal_binds": True})` string OR use SQLAlchemy's `events`/`Statement` capture.

Integration tests live under `tests/integration/` and are decorated with `@pytest.mark.skipif(not os.getenv("ORACLE_DSN"), reason="...")` so they run only when a developer points at a real Oracle XE.

**Rationale**: keeps CI deterministic and fast. Manual `@oracle_schema.sql` execution in PR 1 review covers the "did the PL/SQL parse?" question.

**Rejected**:
- *Testcontainers Oracle in CI*: heavy image (~3GB), slow, license fragility.
- *Live Oracle required for all tests*: blocks contributors without local DB.

**Risk acknowledged**: mocked tests can pass against syntactically broken PL/SQL. Mitigation: PR 1 reviewer must run the schema locally before approving.

---

### ADR-9 — Idempotency guards
**Decision**:
- **Packages** (`pkg_*`): use `CREATE OR REPLACE PACKAGE` and `CREATE OR REPLACE PACKAGE BODY` — naturally idempotent.
- **Sequences** (`seq_*`): wrap each `CREATE SEQUENCE` in:
  ```sql
  BEGIN
      EXECUTE IMMEDIATE 'CREATE SEQUENCE BIBLIOTECA.seq_books START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
  EXCEPTION
      WHEN OTHERS THEN
          IF SQLCODE != -955 THEN RAISE; END IF;
  END;
  /
  ```
  `-955` is "ORA-00955: name is already used by an existing object" — the only error we swallow.

**Rationale**: avoids `DROP SEQUENCE` (which would reset the counter and could break running systems). The narrow `SQLCODE` filter prevents masking unrelated errors.

**Rejected**:
- *Existence check via `SELECT count FROM user_sequences`*: more SQL, race-prone, less idiomatic in Oracle.
- *Drop-then-create*: destructive, breaks running deployments.

---

## 6. Rollback Plan

| Layer | Rollback action |
|---|---|
| PR 3 (tests) | `git revert <sha>` — no runtime impact |
| PR 2 (Python repos) | `git revert <sha>` — removes `app/infrastructure/repositories/*.py`. Ports remain; no consumers exist yet (services not yet wired). |
| PR 1 (schema) | `git revert <sha>` on the SQL file. For already-applied databases: run manual cleanup script (documented in PR 1 description): `DROP PACKAGE BIBLIOTECA.pkg_*;` for each, then `DROP SEQUENCE BIBLIOTECA.seq_*;` for each. Tables, triggers, FKs are untouched. |

No data migration → no data rollback. Identity columns survive the rollback because they were never changed.

---

## 7. Open Questions / Assumptions Requiring Validation

1. **OUT param style for `p_insert`** — assumption: callers want the new ID returned synchronously. If services later want fire-and-forget inserts with eager `RETURNING` via a separate query, we may simplify by dropping OUT params and adding a `seq_<table>.CURRVAL` read. Defer decision until first service is wired.
2. **`returns.id` generation** — assumption: `pkg_returns.p_process` returns the new return ID via OUT param, same pattern as other inserts. Confirm with reviewer.
3. **`book_authors` upsert semantics** — assumption: `set_authors` is a full replace (clear + insert). If partial-update semantics are ever needed, add `p_add_author` and `p_remove_author` calls from the service layer (procedures already exist).
4. **Error translation** — repositories currently let `oracledb.DatabaseError` bubble up. Future work may add a translator to domain exceptions; out of scope here.

---

## 8. Architectural Risks

| Risk | Mitigation |
|---|---|
| Mocked tests pass over broken PL/SQL | PR 1 review requires local schema apply; document `sqlplus @oracle_schema.sql` smoke step in PR 1 description |
| Procedures duplicate trigger logic | ADR-6 and ADR-7 explicitly forbid this; review checklist must verify |
| OUT-param `callproc` path bypasses SQLAlchemy session lifecycle | Always obtain cursor from `session.connection().connection.cursor()` — never open a fresh oracledb connection |
| Sequence + IDENTITY dual ownership confuses contributors | Schema header comment documents the rule: "procedures always use sequences; IDENTITY is for dev ad-hoc inserts only" |
| Adding collection-type procedures later would require schema TYPE DDL | Accepted; out of scope. ADR-5 explicitly defers |
