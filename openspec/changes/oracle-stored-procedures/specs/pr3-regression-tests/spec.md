# Spec: PR 3 — Regression Test Suite

**Change ID**: `oracle-stored-procedures`
**PR slice**: `pr3-regression-tests`
**Directories governed**: `tests/unit/repositories/`, `tests/integration/repositories/`

---

## 1. Scope

This spec defines what MUST be true about the test suite after PR 3 is merged.
It covers unit tests (no live Oracle), integration tests (gated on env var), and compilation check.

---

## 2. Requirements

### 2.1 Compilation Gate

**R-COMPILE-01** — `python -m compileall app main.py` MUST be executed as a test step (or pre-test step) and MUST exit with code 0. This verifies no `SyntaxError` or broken import exists in the codebase before any test runs.

### 2.2 Test Runner

**R-RUNNER-01** — `python -m pytest` MUST exit with code 0 (all collected tests pass).

**R-RUNNER-02** — The test suite MUST NOT require a live Oracle connection to pass. Any test requiring Oracle MUST be gated behind a `pytest.mark.skipif(not os.getenv("ORACLE_DSN"), reason="requires live Oracle")` decorator or equivalent conftest mechanism.

**R-RUNNER-03** — Test discovery MUST follow the standard pytest convention: test files named `test_*.py` or `*_test.py` inside `tests/`.

### 2.3 Coverage — Unit Tests (per repository)

For each of the seven repositories (`RoleRepository`, `UserRepository`, `CategoryRepository`, `AuthorRepository`, `BookRepository`, `LoanRepository`, `ReturnRepository`), the following unit tests MUST exist:

**R-UNIT-CREATE** — A test MUST verify that `create()` invokes the correct Oracle procedure name (e.g., `"BIBLIOTECA.pkg_roles.p_insert"`). The test MUST assert either:
  - The SQL text passed to `session.execute` contains the expected procedure name, OR
  - `callproc` is called with the expected procedure name as the first argument.

**R-UNIT-CREATE-BINDS** — A test MUST verify that `create()` passes a bind dict/list whose keys or positional values correspond to the expected column parameters. The bind shape MUST match what the procedure signature requires.

**R-UNIT-CREATE-ID** — A test MUST verify that `create()` returns an object (or ID) with the PK populated from the OUT parameter mock value.

**R-UNIT-UPDATE** — A test MUST verify that `update()` invokes the correct `p_update` procedure and includes the entity ID and updated fields in the bind dict.

**R-UNIT-DELETE-TRUE** — A test MUST verify that `delete()` invokes the correct `p_delete` procedure and returns `True` when the procedure succeeds.

**R-UNIT-DELETE-FALSE** — A test MUST verify that `delete()` returns `False` (or a semantically equivalent falsy value) when the procedure raises a not-found exception.

**R-UNIT-GET-BY-ID** — A test MUST verify that `get_by_id()` issues a SQLAlchemy `select()` query (not a `text()` call) and that the WHERE clause filters on the correct primary key.

**R-UNIT-LIST-ALL** — A test MUST verify that `list_all()` issues a `select()` query with no WHERE clause and returns all mocked rows.

**R-UNIT-NO-COMMIT** — At least one test per repository MUST assert that `session.commit` is never called during any write operation.

### 2.4 Coverage — BookRepository Extras

**R-UNIT-BOOK-GET-WITH-AUTHORS** — A test MUST verify that `get_with_authors()` uses `selectinload` (or equivalent eager-load) and returns the mocked `Book` instance with its `authors` relationship populated.

**R-UNIT-BOOK-SET-AUTHORS-CLEAR** — A test MUST verify that `set_authors(session, book_id, author_ids)` calls `p_clear_authors` first before any `p_add_author` call.

**R-UNIT-BOOK-SET-AUTHORS-LOOP** — A test MUST verify that `set_authors()` calls `p_add_author` once per author ID in `author_ids`.

**R-UNIT-BOOK-SET-AUTHORS-EMPTY** — A test MUST verify that `set_authors()` with `author_ids = []` calls `p_clear_authors` and makes zero `p_add_author` calls.

### 2.5 Coverage — LoanRepository Extras

**R-UNIT-LOAN-CANCEL** — A test MUST verify that `LoanRepository.cancel()` calls `pkg_loans.p_cancel` with the correct loan ID.

### 2.6 Coverage — ReturnRepository Extras

**R-UNIT-RETURN-PROCESS** — A test MUST verify that `ReturnRepository.create()` (or `process()` if named differently) calls `pkg_returns.p_process` with the correct bind parameters.

### 2.7 Mocking Strategy

**R-MOCK-SESSION** — Unit tests MUST use `unittest.mock.MagicMock` or `unittest.mock.AsyncMock` to mock the SQLAlchemy `Session` object. `pytest-mock` (`mocker` fixture) is ALLOWED as an alternative.

**R-MOCK-EXECUTE** — For write tests using `session.execute(text(...), ...)`, the mock MUST capture the call and the test MUST assert on the `str` representation of the SQL text argument to confirm the procedure name.

**R-MOCK-CALLPROC** — For OUT-param tests using the raw DBAPI cursor path, the mock chain MUST cover `session.connection().connection.cursor()`. The mock's `var()` return MUST be configured to return a predictable numeric value (e.g., `42`) so the test can assert the returned ID.

**R-MOCK-ORM-READ** — For read tests, `session.execute().scalar_one_or_none()` or `session.execute().scalars().all()` MUST be mocked to return a controlled fixture object. The test MUST assert the SQL construct is built (not that it executes correctly against Oracle).

**R-MOCK-ISOLATION** — Each test MUST use a fresh mock per test function. Shared mock state across tests is FORBIDDEN.

### 2.8 Integration Tests (SHOULD)

**R-INT-GATE** — Integration tests MUST be decorated with:
```python
@pytest.mark.skipif(
    not os.getenv("ORACLE_DSN"),
    reason="Requires live Oracle — set ORACLE_DSN to enable"
)
```

**R-INT-COVERAGE** — SHOULD have at least one integration test per repository that exercises the full round-trip: `create` → `get_by_id` → `update` → `delete`.

**R-INT-ISOLATION** — Integration tests SHOULD clean up (rollback or delete) their test data after each test to leave the database in a consistent state.

**R-INT-SCHEMA** — Integration tests SHOULD document in their module docstring that PR 1 schema (sequences + packages) MUST be applied to the target Oracle instance before running.

### 2.9 File Structure

**R-FILE-UNIT** — Unit test files MUST be located under `tests/unit/repositories/` with one file per repository:
```
tests/unit/repositories/
    __init__.py
    test_role_repository.py
    test_user_repository.py
    test_category_repository.py
    test_author_repository.py
    test_book_repository.py
    test_loan_repository.py
    test_return_repository.py
```

**R-FILE-INT** — Integration test files SHOULD be located under `tests/integration/repositories/` following the same naming convention.

**R-FILE-CONFTEST** — A `conftest.py` SHOULD exist at `tests/` or `tests/unit/repositories/` level to define shared fixtures (e.g., `mock_session`).

---

## 3. Acceptance Scenarios

### SCENARIO-TEST-COMPILE-01 — Compilation gate passes

**Given** the repository after PR 2 and PR 3 are merged
**When** `python -m compileall app main.py` is run
**Then** exit code is 0
**And** no errors are printed to stderr

### SCENARIO-TEST-RUNNER-01 — Full test suite passes without Oracle

**Given** a developer environment with no `ORACLE_DSN` set
**When** `python -m pytest` is run
**Then** exit code is 0
**And** all unit tests pass
**And** integration tests are SKIPPED (not FAILED)

### SCENARIO-TEST-RUNNER-02 — Full test suite passes with Oracle

**Given** a developer environment with `ORACLE_DSN` set to a valid Oracle XE instance
**And** PR 1 schema has been applied to that instance
**When** `python -m pytest` is run
**Then** exit code is 0
**And** both unit tests and integration tests pass

### SCENARIO-TEST-CREATE-01 — Unit test asserts correct procedure call for book create

**Given** `test_book_repository.py` contains a `test_create_calls_p_insert` test
**When** the test runs
**Then** it asserts that `callproc` was called with `"BIBLIOTECA.pkg_books.p_insert"` as the procedure name
**And** it asserts the bind list contains the expected title, isbn, and other column values
**And** it asserts the returned book's `id` equals the mocked OUT param value

### SCENARIO-TEST-UPDATE-01 — Unit test asserts correct procedure call for role update

**Given** `test_role_repository.py` contains a `test_update_calls_p_update` test
**When** the test runs
**Then** it asserts `session.execute` was called with SQL text containing `"pkg_roles.p_update"`
**And** the bind dict includes `p_id` matching the provided role ID

### SCENARIO-TEST-DELETE-FALSE-01 — Unit test covers not-found case for delete

**Given** `test_category_repository.py` contains a `test_delete_returns_false_when_not_found` test
**And** the mocked session raises a not-found exception
**When** the test runs
**Then** it asserts the method returns `False`
**And** it asserts `session.commit` was NOT called

### SCENARIO-TEST-READ-ORM-01 — Unit test verifies get_by_id uses ORM select

**Given** `test_author_repository.py` contains a `test_get_by_id_uses_select` test
**When** the test runs
**Then** it asserts that the argument passed to `session.execute` is a SQLAlchemy `Select` object (not a `TextClause`)

### SCENARIO-TEST-BOOK-AUTHORS-01 — Unit test verifies set_authors call order

**Given** `test_book_repository.py` contains a `test_set_authors_calls_clear_then_add` test
**And** `author_ids = [3, 7]`
**When** the test runs
**Then** it asserts `session.execute` was called 3 times in order:
  1. text containing `"p_clear_authors"` with `{"b": book_id}`
  2. text containing `"p_add_author"` with `{"b": book_id, "a": 3}`
  3. text containing `"p_add_author"` with `{"b": book_id, "a": 7}`

### SCENARIO-TEST-BOOK-AUTHORS-02 — Unit test verifies set_authors with empty list

**Given** `test_book_repository.py` contains a `test_set_authors_empty_list` test
**And** `author_ids = []`
**When** the test runs
**Then** `session.execute` is called exactly once (the clear call)
**And** no `p_add_author` call is made

### SCENARIO-TEST-LOAN-CANCEL-01 — Unit test verifies cancel procedure call

**Given** `test_loan_repository.py` contains a `test_cancel_calls_p_cancel` test
**When** the test runs
**Then** it asserts `session.execute` was called with text containing `"pkg_loans.p_cancel"`
**And** the bind dict contains the correct loan ID

### SCENARIO-TEST-NO-COMMIT-01 — Unit tests assert no session.commit

**Given** any `test_*_repository.py` file
**When** all write-path tests in the file run
**Then** none of them result in `session.commit` being called

### SCENARIO-TEST-ISOLATION-01 — Each test has independent mock state

**Given** two tests in `test_book_repository.py` that both call `create()`
**When** both tests run in the same pytest session
**Then** the mock call counts in test 2 are not influenced by calls from test 1

---

## 4. Rollback Plan

1. `git revert <pr3-sha>` removes `tests/unit/repositories/` and `tests/integration/repositories/`.
2. No Oracle schema or Python repository code is affected.
3. CI pipeline may fail on `python -m pytest` after revert if the pipeline step is configured to fail on no-tests-collected; this is expected and acceptable — re-run after revert with `--ignore=tests/` or remove the test step temporarily.

---

## 5. Out of Scope

- Oracle DDL (PR 1)
- Python repository implementation (PR 2)
- End-to-end tests involving FastAPI route handlers
- Performance / load tests
- Contract tests between services and repositories (deferred to service layer PRs)
- Code coverage percentage thresholds (SHOULD be addressed when CI is configured; not a hard gate for this PR)
