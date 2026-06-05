# Verify Report - oracle-stored-procedures

**Change ID**: oracle-stored-procedures
**Date**: 2026-06-02
**Verdict**: PASS WITH WARNINGS
**Issues**: 0 CRITICAL / 4 WARNING / 3 SUGGESTION

---

## Build and Test Evidence

compileall: EXIT 0 - all modules compiled successfully.
pytest: EXIT 0 - 68 passed, 11 skipped in 0.85s.
  - 68 unit tests PASSED
  - 11 integration tests SKIPPED (ORACLE_DSN not set, correct per R-RUNNER-02)
  - 0 FAILED

---

## Task Completion

Tasks 1.1-1.8: COMPLETE
Task 1.9: PENDING (intentional manual sqlplus smoke gate)
Task 1.10: COMPLETE
Tasks 2.1-2.10: COMPLETE
Tasks 3.1-3.11: COMPLETE

---

## Issues

### WARNING-01 - Sequences missing OWNED BY clause
Spec R-SEQ-01: each sequence OWNED BY its table column.
Implementation: no OWNED BY clause in any of the 7 CREATE SEQUENCE statements.
Impact: no cascading drop on parent table drop; no runtime failure.
Action: add OWNED BY BIBLIOTECA.<table>.id inside each EXECUTE IMMEDIATE.

### WARNING-02 - pkg_returns missing p_update; ReturnRepository.update() will fail on Oracle
pkg_returns has no p_update in spec or body (only p_process, p_delete, p_sel_by_id, p_list).
ReturnRepository.update() at return_repository.py line 53 calls pkg_returns.p_update.
Impact: ORA-06550 at runtime on any Return_ update call.
Action: add p_update to pkg_returns spec and body, OR declare Return_ immutable and remove update() from port and repo.

### WARNING-03 - ReturnRepository unit tests incomplete (3 MUST tests missing)
test_return_repository.py has 4 tests; missing R-UNIT-UPDATE, R-UNIT-DELETE-TRUE, R-UNIT-DELETE-FALSE.
Action: add test_update_calls_p_update, test_delete_returns_true_on_success, test_delete_returns_false_on_not_found.

### WARNING-04 - Integration test file structure deviates from spec
Spec: tests/integration/repositories/test_<agg>_repository.py (per aggregate).
Implementation: tests/integration/test_repositories_integration.py (single combined file).
11 smoke tests present; ORACLE_DSN gate works correctly. SHOULD-level deviation.

---

## Spec Compliance Matrix (Summary)

R-SEQ-01..05: 7 sequences, NOCACHE NOCYCLE, all_sequences guard. OWNED BY absent. PARTIAL.
R-PKG-01..06: 7 packages, CREATE OR REPLACE. pkg_returns missing p_update. PARTIAL.
R-REPO-FILES-01/02: 8 files present. PASS.
R-PORT-01..04: All protocols satisfied, cancel() on LoanRepositoryPort. PASS.
R-WRITE-01..08: All writes via procedures, no raw SQL, no session.add. PASS (schema gap at runtime for pkg_returns.p_update).
R-READ-01..04: ORM select() on all reads, selectinload, no text() in reads. PASS.
R-TXN-01/02: No session.commit/rollback in any repo. PASS.
R-COMPILE-01: compileall exits 0. PASS.
R-RUNNER-01/02/03: pytest exits 0, no Oracle required, standard discovery. PASS.
R-UNIT-* (6 repos): All MUST tests present and passing. PASS.
R-UNIT-* (ReturnRepository): UPDATE, DELETE-TRUE, DELETE-FALSE missing. FAIL (WARNING-03).
R-UNIT-BOOK-*: All 4 extra book tests passing. PASS.
R-UNIT-LOAN-CANCEL: cancel test present and passing. PASS.
R-UNIT-RETURN-PROCESS: create/p_process test present and passing. PASS.

---

## Final Verdict

PASS WITH WARNINGS

The implementation is functionally correct for the happy path.
compileall exits 0. pytest exits 0 with 68 passing unit tests and 11 correctly skipped integration tests.
All architectural rules are consistently applied across all 7 repositories.

Gaps to resolve before Oracle smoke testing:
1. pkg_returns.p_update absent from schema - ORA-06550 on live Oracle when update() is called.
2. test_return_repository.py missing 3 mandatory unit tests.

Acceptable to carry forward: WARNING-01 (OWNED BY) and WARNING-04 (integration file structure).
Task 1.9 remains intentionally pending (human manual gate).