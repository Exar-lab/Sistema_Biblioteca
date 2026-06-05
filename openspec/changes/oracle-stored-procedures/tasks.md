# Tasks: Oracle Stored Procedures + Repository Layer

**Change ID**: `oracle-stored-procedures`
**Delivery strategy**: chained PRs, stacked-to-main
**Chain strategy**: stacked-to-main

---

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~950–1 200 (PR 1: ~350, PR 2: ~450, PR 3: ~350) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 (stacked-to-main) |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Oracle schema: sequences + 7 PL/SQL packages | PR 1 | Base: main; manual smoke gate required |
| 2 | Python repository layer (7 files + port fix) | PR 2 | Base: PR 1 branch; compileall gate |
| 3 | Unit + integration regression tests | PR 3 | Base: PR 2 branch; full pytest gate |

---

## PR 1 — Oracle Schema Foundation

**Done definition**: `database/oracle_schema.sql` re-runs idempotently with `sqlplus`, all 7 sequences and 7 packages parse without error, reviewer confirms local smoke pass.

- [x] 1.1 Add 7 idempotent sequence blocks to `database/oracle_schema.sql` (`seq_roles_id`, `seq_library_users_id`, `seq_categories_id`, `seq_authors_id`, `seq_books_id`, `seq_loans_id`, `seq_returns_id`) — each wrapped in `BEGIN EXECUTE IMMEDIATE ... EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN RAISE; END IF; END;` with `OWNED BY <table>.<col>`, `START WITH 1 NOCACHE NOCYCLE`.
- [x] 1.2 Add `pkg_roles` package spec + body to `database/oracle_schema.sql` with procedures `p_insert(p_name, p_description, p_id OUT)`, `p_update(p_id, p_name, p_description)`, `p_delete(p_id)`, `p_sel_by_id(p_id, p_cursor OUT)`, `p_list(p_cursor OUT)`. Use `CREATE OR REPLACE`.
- [x] 1.3 Add `pkg_library_users` package spec + body — same standard 5 procedures (`p_insert` columns: name, email, phone, role_id, `p_id OUT`).
- [x] 1.4 Add `pkg_categories` package spec + body — standard 5 procedures (`p_insert` columns: name, description, `p_id OUT`).
- [x] 1.5 Add `pkg_authors` package spec + body — standard 5 procedures (`p_insert` columns: name, bio, `p_id OUT`).
- [x] 1.6 Add `pkg_books` package spec + body — standard 5 procedures plus `p_add_author(p_book_id, p_author_id)`, `p_remove_author(p_book_id, p_author_id)`, `p_clear_authors(p_book_id)`. `p_insert` columns: title, isbn, stock, category_id, `p_id OUT`. No stock side effects (trigger owns stock).
- [x] 1.7 Add `pkg_loans` package spec + body — standard 5 procedures plus `p_cancel(p_loan_id)`. `p_cancel` sets `status = 'CANCELLED'`, does NOT touch stock, raises if `status IN ('RETURNED','CANCELLED')`. `p_insert` columns: user_id, book_id, loan_date, due_date, `p_id OUT`.
- [x] 1.8 Add `pkg_returns` package spec + body — procedures: `p_process(p_loan_id, p_return_date, p_fine_amount, p_notes, p_id OUT)` (INSERT only into `returns`; trigger `trg_returns_restore_stock` owns loan/stock side effects), `p_sel_by_id(p_id, p_cursor OUT)`.
- [ ] 1.9 **Manual gate** — re-run `sqlplus BIBLIOTECA/<pwd>@<dsn> @database/oracle_schema.sql` against an existing schema and confirm: no ORA-* errors, no sequence resets, all packages compile (`SELECT object_name, status FROM user_objects WHERE object_type LIKE 'PACKAGE%'` shows `VALID`). Mark as "run locally" in PR description.
- [x] 1.10 Update `README.md` with sqlplus invocation note, idempotency explanation, password variable setup, and post-apply validation query (`SELECT object_name, object_type, status FROM user_objects WHERE object_type IN ('PACKAGE','PACKAGE BODY')`). Done — see README section "Aplicar el esquema Oracle".

---

## PR 2 — Python Repository Layer

**Done definition**: All 7 repository files exist, each satisfies its port Protocol, `python -m compileall app main.py` exits 0, no circular imports.

- [x] 2.1 Add `cancel(self, session, loan_id: int) -> bool` to `app/application/ports/loan_repository.py` Protocol.
- [x] 2.2 Create `app/infrastructure/repositories/__init__.py` (empty or exporting classes).
- [x] 2.3 Create `app/infrastructure/repositories/role_repository.py` — class `RoleRepository` implementing `RoleRepositoryPort`. `create()` uses raw cursor `callproc` for `pkg_roles.p_insert` OUT param, sets `role.id`, returns entity. `update()`/`delete()` use `session.execute(text("BEGIN BIBLIOTECA.pkg_roles.p_<x>(...); END;"), binds)`. `delete()` returns `True`/`False`. `get_by_id()`/`list_all()` use `session.execute(select(Role)...)`. No `session.commit/rollback`.
- [x] 2.4 Create `app/infrastructure/repositories/category_repository.py` — same pattern as `RoleRepository` against `pkg_categories` and `Category` model.
- [x] 2.5 Create `app/infrastructure/repositories/author_repository.py` — same pattern against `pkg_authors` and `Author` model.
- [x] 2.6 Create `app/infrastructure/repositories/user_repository.py` — same pattern against `pkg_library_users` and `LibraryUser` model.
- [x] 2.7 Create `app/infrastructure/repositories/book_repository.py` — standard 5 methods + `get_with_authors(session, book_id)` (uses `selectinload(Book.authors)`) + `set_authors(session, book_id, author_ids)` (`p_clear_authors` then `p_add_author` per id). All writes via `pkg_books`. No `text()` in reads.
- [x] 2.8 Create `app/infrastructure/repositories/loan_repository.py` — standard 5 methods + `cancel(session, loan_id)` (calls `pkg_loans.p_cancel`, returns `True` on success). `p_insert` has no stock params.
- [x] 2.9 Create `app/infrastructure/repositories/return_repository.py` — `create()` calls `pkg_returns.p_process` via raw cursor (OUT param for new id). `get_by_id()`/`list_all()` via ORM select.
- [x] 2.10 Run `python -m compileall app main.py` locally and confirm exit code 0. Fix any import errors before PR.

---

## PR 3 — Regression Tests

**Done definition**: `python -m compileall app main.py` exits 0; `python -m pytest` exits 0 with integration tests SKIPPED when `ORACLE_DSN` is not set; all unit assertions listed below pass.

- [x] 3.1 Create `tests/unit/repositories/test_role_repository.py` — 6 unit tests: `test_create_calls_p_insert_and_returns_id`, `test_create_binds_correct_params`, `test_update_calls_p_update`, `test_delete_returns_true_on_success`, `test_delete_returns_false_on_not_found`, `test_get_by_id_uses_select`, `test_list_all_uses_select_no_where`. Mock `session.execute` and `session.connection().connection.cursor()`.
- [x] 3.2 Create `tests/unit/repositories/test_category_repository.py` — same 6+1 tests as above against `CategoryRepository` / `pkg_categories`.
- [x] 3.3 Create `tests/unit/repositories/test_author_repository.py` — same 6+1 tests against `AuthorRepository` / `pkg_authors`.
- [x] 3.4 Create `tests/unit/repositories/test_user_repository.py` — same 6+1 tests against `UserRepository` / `pkg_library_users`.
- [x] 3.5 Create `tests/unit/repositories/test_book_repository.py` — standard 6+1 tests + `test_get_with_authors_uses_selectinload` (assert `selectinload` in query, no procedure call) + `test_set_authors_with_two_authors` (assert `p_clear_authors` called once then `p_add_author` called twice in order) + `test_set_authors_with_empty_list` (assert only `p_clear_authors` called, zero `p_add_author` calls).
- [x] 3.6 Create `tests/unit/repositories/test_loan_repository.py` — standard 6+1 tests + `test_cancel_calls_p_cancel` (cancel uses raw cursor callproc, not session.execute — asserts callproc called with pkg_loans.p_cancel and loan_id in bind list).
- [x] 3.7 Create `tests/unit/repositories/test_return_repository.py` — `test_create_calls_p_process_and_returns_id`, `test_get_by_id_uses_select`, `test_list_all_uses_select_no_where`. Assert no `session.commit` in any write-path test across all files.
- [x] 3.8 Create `tests/integration/test_repositories_integration.py` — combined file with pytestmark skipif guard for all 7 repositories; smoke test list_all + create/get/delete round-trip where applicable.
- [x] 3.9 Add `tests/unit/__init__.py`, `tests/unit/repositories/__init__.py` and `tests/integration/__init__.py` (empty) if not present.
- [x] 3.10 Run `python -m compileall app main.py` — must exit 0.
- [x] 3.11 Run `python -m pytest` (no `ORACLE_DSN` set) — exit 0: 68 passed, 11 skipped. Integration tests SKIPPED, not FAILED.
