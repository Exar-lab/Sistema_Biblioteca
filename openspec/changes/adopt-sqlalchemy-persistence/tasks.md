# Tasks: Adopt SQLAlchemy as the FastAPI Persistence Layer

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 650-950 additions/deletions across code, tests, and docs |
| 300-line budget risk | High |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 core/session + docs → PR 2 catalog CRUD path → PR 3 circulation triggers/rules → PR 4 reporting/audit cleanup |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No — the delivery strategy and budget risks are captured in the forecast table above.

## Verification Commands

Run after each PR unless scoped otherwise:

```bash
python -m compileall app main.py
python -m pytest
```

Oracle-gated checks, only when `DATABASE_URL` points to a prepared Oracle database:

```bash
python -m pytest tests/integration/ -m integration -v
curl http://127.0.0.1:8000/health
```

## PR 1 — Core SQLAlchemy contract and documentation

- [x] Audit `requirements.txt` and confirm no dependency churn is needed beyond existing `SQLAlchemy`, `oracledb`, `pydantic-settings`, and `pytest`.
- [x] Verify `app/core/config.py` documents/loads `DATABASE_URL` and `SQLALCHEMY_ECHO` for sync `oracle+oracledb://...` use.
- [x] Verify `app/core/base.py` remains import-safe and contains only the SQLAlchemy declarative `Base`.
- [x] Harden `app/core/database.py` as the only runtime engine/session factory: `engine`, `SessionLocal`, `get_db`, and DB health smoke query.
- [x] Add or update tests in `tests/test_health_and_db_lifecycle.py` for successful commit/close and exception rollback/close.
- [x] Document SQLAlchemy-vs-Oracle ownership in `README.md` or the project setup doc: SQLAlchemy for app runtime persistence; `database/oracle_schema.sql` for schema, triggers, constraints, indexes, seeds, and DBA setup.
- [x] Verification: run `python -m compileall app main.py` and `python -m pytest tests/test_health_and_db_lifecycle.py`.
- [x] Rollback boundary: revert only `app/core/*`, lifecycle tests, and docs; no entity behavior should depend on this PR yet.

## PR 2 — Catalog and low-risk CRUD repository path

### PR 2A — Category vertical slice

- [x] Align category schema description length with Oracle `VARCHAR2(500)`.
- [x] Add SQLAlchemy category repository adapter.
- [x] Add category application service without FastAPI or SQLAlchemy imports.
- [x] Add `/api/v1/categories` router and mount it in `main.py`.
- [x] Add schema, service, and router tests using fakes/no Oracle dependency.
- [x] Verification: `python -m compileall app main.py` and targeted pytest passed.

### Remaining PR 2 scope

- [ ] Audit ORM mappings against `database/oracle_schema.sql` for `app/domain/models/role.py`, `category.py`, `author.py`, `book.py`, and the `book_authors` association table.
- [ ] Align Pydantic contracts in `app/schemas/role.py`, `category.py`, `author.py`, and `book.py` so read schemas use `from_attributes=True` and do not expose persistence-only internals.
- [ ] Confirm or complete repository ports in `app/application/ports/{role,category,author,book}_repository.py` for required CRUD and book-author relationship methods.
- [ ] Confirm or complete SQLAlchemy adapters in `app/infrastructure/repositories/{role,category,author,book}_repository.py`; keep SQLAlchemy query code out of services/routes.
- [ ] Confirm or complete services in `app/application/services/{role,category,author,book}_service.py`; services may enforce workflow checks but must not import SQLAlchemy or FastAPI.
- [ ] Confirm `app/api/v1/routers/{roles,categories,authors,books}.py` only inject `Session = Depends(get_db)` and service dependencies, then delegate to services.
- [ ] Add or update focused unit tests under `tests/unit/` for catalog service behavior using fake repositories; avoid Oracle requirements for these tests.
- [ ] Verification: run `python -m compileall app main.py`, `python -m pytest tests/unit`, and full `python -m pytest` if scope remains small.
- [ ] Rollback boundary: revert catalog models/schemas/ports/repositories/services/routes/tests only; PR 1 core remains intact.

## PR 3 — Circulation flows, Oracle trigger coexistence, and error translation

- [ ] Audit `app/domain/models/loan.py`, `return_.py`, and `book.py` against `database/oracle_schema.sql` for `loans`, `returns`, stock columns, status defaults, timestamps, and relationships.
- [ ] Confirm `database/oracle_schema.sql` remains the owner for checkout stock decrement, return stock restore, loan return status/date updates, and related Oracle errors.
- [ ] Add or update domain errors in `app/application/errors.py` for not found, conflict, and out-of-stock/Oracle-trigger failures.
- [ ] Confirm or complete ports in `app/application/ports/loan_repository.py` and `return_repository.py` for `get_by_user`, `get_by_book`, `has_overdue_loans`, active-loan lookup, and return creation.
- [ ] Confirm or complete `app/infrastructure/repositories/loan_repository.py` to flush loan inserts and translate Oracle out-of-stock errors such as `ORA-20001` into `OutOfStockError`.
- [ ] Confirm or complete `app/infrastructure/repositories/return_repository.py` to flush return inserts and expire/refresh affected loan/book state when trigger-owned data is needed in responses.
- [ ] Confirm or complete `app/application/services/loan_service.py` so overdue-user blocking is application-owned and evaluated through repository ports.
- [ ] Confirm or complete `app/application/services/return_service.py` so return workflows validate the active loan and delegate trigger-owned updates to Oracle.
- [ ] Confirm `app/api/v1/routers/loans.py` and `returns.py` stay thin and never parse Oracle errors directly.
- [ ] Add or update unit tests under `tests/unit/` for overdue blocking, missing loan/book/user failures, duplicate/invalid return handling, and out-of-stock translation using fakes/mocks.
- [ ] Add or update Oracle-gated integration tests under `tests/integration/` for available-stock checkout, zero-stock rejection, return-trigger loan state, and stock restore.
- [ ] Verification: run `python -m compileall app main.py`, `python -m pytest tests/unit`, and, when Oracle is configured, `python -m pytest tests/integration/ -m integration -v`.
- [ ] Rollback boundary: revert circulation ports/repositories/services/routes/tests; database SQL changes should be reverted separately and reviewed first.

## PR 4 — Cross-cutting cleanup, reporting path, and review guardrails

- [ ] Search `app/api`, `app/application`, and `app/infrastructure` for direct `SessionLocal(`, `create_engine(`, route-level `execute(`, and ad hoc `text(` calls; move normal runtime persistence into repositories, leaving only infrastructure diagnostics such as health checks in `app/core/database.py`.
- [ ] If reporting endpoints exist or are added, implement repository/service methods under `app/infrastructure/repositories/` and `app/application/services/`; isolate any unavoidable Oracle-specific SQL in repository methods with comments explaining why.
- [ ] Register or verify domain exception translation in `app/api/exception_handlers.py` and `main.py` so routes do not duplicate HTTP error mapping.
- [ ] Update `AGENTS.md` or setup docs only if executable verification commands changed.
- [ ] Add a lightweight review checklist to `README.md` or a project doc covering: routes thin, services no SQLAlchemy/FastAPI imports, repositories own ORM, Oracle `.sql` preserved, rule owner declared.
- [ ] Verification: run `python -m compileall app main.py`, `python -m pytest`, and Oracle-gated checks when configured.
- [ ] Rollback boundary: revert reporting/cleanup/doc-only files independently; do not roll back prior PRs unless a contract regression is found.

## Final Acceptance Checklist

- [ ] `app/core/database.py` is the only normal runtime session factory and request sessions commit/rollback/close correctly.
- [ ] FastAPI routes in `app/api/v1/routers/` delegate to services and do not execute normal workflow SQL directly.
- [ ] Services in `app/application/services/` enforce workflow rules without SQLAlchemy or FastAPI imports.
- [ ] SQLAlchemy code and Oracle error translation live in `app/infrastructure/repositories/`.
- [ ] ORM models in `app/domain/models/` mirror `database/oracle_schema.sql` without replacing it as the source for Oracle-owned artifacts.
- [ ] `database/oracle_schema.sql` remains present and documented for schema/bootstrap/triggers/constraints/indexes/seeds.
- [ ] Unit tests cover service rules without Oracle; integration tests or documented checks cover trigger-sensitive flows when Oracle is available.
