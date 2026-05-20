# Tasks: Hexagonal Repository Layer

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900–1 200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Domain foundation: errors, BoolChar, ORM models, ports | PR 1 | Base = master; no HTTP surface yet |
| 2 | Infrastructure + application layer: repos, services, composition root | PR 2 | Base = PR 1 branch; depends on models + ports |
| 3 | HTTP delivery: routers, exception handlers, main wiring, schema reconciliation, tests | PR 3 | Base = PR 2 branch; completes the vertical stack |

---

## Phase 1: Domain Foundation

- [ ] 1.1 Create `app/domain/__init__.py` and `app/domain/models/__init__.py` (empty init files).
- [ ] 1.2 Create `app/domain/models/types.py` — `BoolChar` TypeDecorator: `process_bind_param` maps `True→"Y"`, `False→"N"`; `process_result_value` maps `"Y"→True`, else `False`. impl = `CHAR(1)`.
- [ ] 1.3 Create `app/application/__init__.py`, `app/application/ports/__init__.py`, `app/application/services/__init__.py` (empty inits).
- [ ] 1.4 Create `app/application/errors.py` — define `NotFoundError`, `OutOfStockError`, `ConflictError` as plain Python exceptions; no FastAPI or HTTP imports.
- [ ] 1.5 Create `app/domain/models/role.py` — `Role` mapped class, `__table_args__ = {"schema": "BIBLIOTECA"}`, no `is_active` column.
- [ ] 1.6 Create `app/domain/models/user.py` — `LibraryUser` mapped class, CHAR(1) `is_active` column via `BoolChar`, schema `BIBLIOTECA`.
- [ ] 1.7 Create `app/domain/models/category.py` — `Category` mapped class, schema `BIBLIOTECA`.
- [ ] 1.8 Create `app/domain/models/author.py` — `Author` mapped class, no `nationality` column, schema `BIBLIOTECA`.
- [ ] 1.9 Create `app/domain/models/book.py` — `Book` mapped class + `book_authors` `Table` object linking books↔authors; `authors` relationship with `secondary=book_authors`; schema `BIBLIOTECA` on both table objects.
- [ ] 1.10 Create `app/domain/models/loan.py` — `Loan` mapped class, no `notes` column, schema `BIBLIOTECA`.
- [ ] 1.11 Create `app/domain/models/return_.py` — `Return_` mapped class, no `condition`/`processed_by_user_id` columns, schema `BIBLIOTECA`.
- [ ] 1.12 Create `app/application/ports/role_repository.py` — `RoleRepository` `typing.Protocol`: `get`, `list`, `create`, `update`, `delete`. No SQLAlchemy imports.
- [ ] 1.13 Create remaining 7 port files (`user_repository.py`, `category_repository.py`, `author_repository.py`, `book_repository.py` with `get_with_authors`/`set_authors`, `loan_repository.py`, `return_repository.py`) — same Protocol pattern; `BookRepository` adds `get_with_authors(id) -> Book | None` and `set_authors(book, author_ids, session) -> None`.

---

## Phase 2: Infrastructure + Application Layer

- [ ] 2.1 Create `app/infrastructure/__init__.py` and `app/infrastructure/repositories/__init__.py`.
- [ ] 2.2 Create `app/infrastructure/repositories/base.py` — `SqlRepositoryBase[M]` generic: `get(session, id)`, `list(session)`, `create(session, data)`, `update(session, id, data)`, `delete(session, id)`. Session accepted at call time (not constructor).
- [ ] 2.3 Create `app/infrastructure/repositories/roles.py` — `RoleRepositorySql(SqlRepositoryBase[Role])`.
- [ ] 2.4 Create `app/infrastructure/repositories/users.py` — `UserRepositorySql`.
- [ ] 2.5 Create `app/infrastructure/repositories/categories.py` — `CategoryRepositorySql`.
- [ ] 2.6 Create `app/infrastructure/repositories/authors.py` — `AuthorRepositorySql`.
- [ ] 2.7 Create `app/infrastructure/repositories/books.py` — `BookRepositorySql`; override `get` to use `selectinload(Book.authors)`; add `get_with_authors` and `set_authors`.
- [ ] 2.8 Create `app/infrastructure/repositories/loans.py` — `LoanRepositorySql`; override `create` to catch `DBAPIError` where `e.orig.args[0].code == 20001` and raise `OutOfStockError`.
- [ ] 2.9 Create `app/infrastructure/repositories/returns.py` — `ReturnRepositorySql`; override `create` to accept `loan_instance=None`; after flush call `session.expire(loan_instance, ["status", "return_date"])`.
- [ ] 2.10 Create `app/application/services/role_service.py` — `RoleService(repo: RoleRepository)`; `get` raises `NotFoundError` if `None`; no SQLAlchemy import.
- [ ] 2.11 Create remaining 7 service files (`user_service.py`, `category_service.py`, `author_service.py`, `book_service.py`, `loan_service.py` with user+book existence checks before create, `return_service.py`) — same thin-service pattern.
- [ ] 2.12 Create `app/composition.py` — factory `Depends` functions (`get_role_service`, …`get_return_service`) that wire `get_db` → `*RepositorySql` → `*Service`. No direct instantiation in `main.py`.

---

## Phase 3: HTTP Delivery + Wiring

- [ ] 3.1 Reconcile `app/schemas/catalog/authors.py` — remove `nationality` from `AuthorRead`; add `model_config = ConfigDict(from_attributes=True)`.
- [ ] 3.2 Reconcile `app/schemas/circulation/loans.py` — remove `notes` from `LoanRead`; add `ConfigDict(from_attributes=True)`.
- [ ] 3.3 Reconcile `app/schemas/circulation/returns.py` — remove `condition` and `processed_by_user_id` from `ReturnRead`; add `ConfigDict(from_attributes=True)`.
- [ ] 3.4 Reconcile `app/schemas/roles.py` — remove `is_active` from `RoleBase`; add `ConfigDict(from_attributes=True)` to read schema.
- [ ] 3.5 Add `ConfigDict(from_attributes=True)` to remaining read schemas that lack it (`users.py`, `categories.py`, `books.py`).
- [ ] 3.6 Create `app/api/exception_handlers.py` — handlers for `NotFoundError→404`, `OutOfStockError→409 {"code":"OUT_OF_STOCK"}`, `ConflictError→409`.
- [ ] 3.7 Create `app/api/v1/routers/__init__.py` and router stubs for all 8 entities (`roles.py`, `users.py`, `categories.py`, `authors.py`, `books.py`, `loans.py`, `returns.py`) — each with GET list (200), GET by ID (200/404), POST (201), PUT (200/404), DELETE (204/404). `GET /books/{id}` calls `book_service.get_with_authors`.
- [ ] 3.8 Create `app/api/v1/router.py` — `APIRouter` that includes all 8 entity routers with their prefixes and tags.
- [ ] 3.9 Update `app/api/dependencies.py` — re-export or delegate to composition.py factories; keep existing `get_db` re-export untouched.
- [ ] 3.10 Update `main.py` — include `api_router` at `/api/v1`; register exception handlers from `app/api/exception_handlers.py`; do NOT instantiate repos/services directly.

---

## Phase 4: Tests

- [ ] 4.1 Create `tests/unit/test_boolchar.py` — test `BoolChar` bind: `True→"Y"`, `False→"N"`; result: `"Y"→True`, `"N"→False` (spec scenario: BoolChar bind/result roundtrip).
- [ ] 4.2 Create `tests/unit/test_errors.py` — assert `OutOfStockError`, `NotFoundError`, `ConflictError` are catchable as `Exception`; assert they carry a message (spec scenario: OutOfStockError is catchable).
- [ ] 4.3 Create `tests/unit/test_role_service.py` — use in-memory fake `RoleRepository`; test `get` returns entity; test `get` raises `NotFoundError` when fake returns `None`; test `create` delegates to port once (spec scenarios: Service get/NotFoundError/create).
- [ ] 4.4 Create `tests/integration/test_loan_repository.py` — against real Oracle XEPDB1: test `LoanRepositorySql.create` with valid stock inserts row; test raises `OutOfStockError` when Oracle fires -20001 (spec scenarios: Create loan/zero-stock).
- [ ] 4.5 Create `tests/integration/test_return_repository.py` — verify `session.expire(loan)` called after return create so `loan.status` reflects `RETURNED` on next access (spec scenario: Create return refreshes loan status).
