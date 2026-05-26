# Verify Report: SQLAlchemy Persistence Chain

Date: 2026-05-26
Branch: `docs/finalize-sqlalchemy-acceptance`
Base reviewed: `origin/feat/circulation-returns-slice` after PR #34 merge (`0cf92ea`)

## Commands

Reproducible commands from the repository root after installing dependencies or activating a project virtual environment:

```bash
python -m compileall app main.py
python -m pytest
```

Recorded local run used `../Sistema_Biblioteca/venv/Scripts/python.exe` as the Python interpreter.

Results:

- `compileall`: passed.
- `pytest`: passed, `71 passed`.

Oracle-gated checks were not run because this worktree does not have a prepared Oracle `DATABASE_URL`/schema instance for integration testing.

## Architecture checks

- Runtime engine/session creation remains centralized in `app/core/database.py` (`engine`, `SessionLocal`, `get_db`, DB smoke check). `main.py` uses `SessionLocal` only for the `/health` diagnostic path.
- API routers under `app/api/v1/routers/` delegate to application services and do not perform normal workflow SQL or parse Oracle errors directly.
- Application services under `app/application/services/` do not import FastAPI or SQLAlchemy; they coordinate workflow rules through repository ports.
- SQLAlchemy adapters and aggregate/reporting queries live under `app/infrastructure/repositories/`.
- Domain/application errors remain framework-free in `app/application/errors.py` and are mapped centrally in `app/api/exception_handlers.py`.

## PR3 circulation evidence

- ORM mappings for `Loan`, `Return_`, and `Book` mirror the Oracle table ownership for loan status, dates, stock columns, and relationships.
- `database/oracle_schema.sql` remains the source of truth for:
  - checkout stock decrement and `ORA-20001` out-of-stock failure in `trg_loans_checkout_stock`;
  - return stock restore plus loan `RETURNED`/`return_date` update in `trg_returns_restore_stock`.
- `SqlAlchemyLoanRepository` flushes inserts and translates wrapped Oracle `ORA-20001`/stock failures to `OutOfStockError`.
- `SqlAlchemyReturnRepository` flushes inserts and expires the related loan's trigger-owned `status` and `return_date` attributes when a loan instance is provided.
- `LoanService` performs application-owned checks for existing user/book, inactive users, and overdue-loan blocking through ports.
- `ReturnService` validates active loans and duplicate returns before delegating trigger-owned updates to Oracle.
- Flat slice tests cover the service/router behavior without Oracle:
  - `tests/test_loans_slice.py`
  - `tests/test_returns_slice.py`
  - centralized error mapping coverage in `tests/test_reports_slice.py`

## Known gaps

- No `tests/integration/` Oracle suite exists yet. Trigger-sensitive behavior is documented and adapter behavior is unit/slice-tested with fakes/mocks, but available-stock checkout, zero-stock rejection, trigger-updated return state, and stock restore still need a prepared Oracle database to execute end-to-end.
- OpenSpec originally mentioned `tests/unit/`; this project currently uses flat `tests/test_*_slice.py` files for no-Oracle service/router coverage.
- Auth/session product slices remain outside this SQLAlchemy persistence acceptance scope.

## Merge-readiness note

`origin/master` has advanced after the SQLAlchemy stack with PR #35 workflow changes. A simulated merge of `origin/master` and the stacked head produced no textual conflict markers in the inspected output, but final integration should still merge/rebase deliberately so the PR #35 workflow changes and the SQLAlchemy stack are both preserved.

## Result

The SQLAlchemy persistence chain is acceptance-ready for a final merge-preparation step, with the Oracle integration test suite documented as the remaining verification gap.
