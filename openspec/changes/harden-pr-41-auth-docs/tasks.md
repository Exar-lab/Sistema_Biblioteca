# Tasks: Harden PR #41 Auth & Docs

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 180-260 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Auth hardening + docs patch | PR 1 | Base = `feat/auth-jwt`; include tests/docs in the same slice. |
| 2 | Not needed | — | Keep the change in one reviewable PR unless scope grows unexpectedly. |

## Phase 1: Foundation / Policy Helpers

- [x] 1.1 Add JWT claim helpers in `app/api/dependencies.py` to validate `sub` safely and normalize role names before authorization checks.
- [x] 1.2 Keep `app/core/security.py` decode behavior aligned with dependency handling so invalid/malformed tokens always map to `None`.
- [x] 1.3 Update `app/application/services/auth_service.py` to emit stable JWT claims (`sub`, `username`, `role`) with consistent role casing.

## Phase 2: Core Auth & Role Wiring

- [x] 2.1 Update `get_current_user()` in `app/api/dependencies.py` to return 401 for missing/malformed `sub` instead of raising 500 on `int()` conversion.
- [x] 2.2 Replace literal admin checks with a centralized admin policy in `app/api/dependencies.py` and use it from `AdminOnly`.
- [x] 2.3 Review `app/api/v1/routers/auth.py` and `app/api/v1/routers/roles.py` for dependency imports/usages that must match the hardened auth contract.

## Phase 3: Testing / Verification

- [x] 3.1 Create `tests/test_auth.py` with regression coverage for malformed token, missing `sub`, and valid token → `/auth/me` success.
- [x] 3.2 Add role-gate tests for `/api/v1/roles/` verifying admin allow and non-admin 403 denial via dependency overrides.
- [x] 3.3 Run `python -m pytest tests/test_auth.py tests/test_roles_slice.py` and confirm the auth slice still passes.

## Phase 4: Cleanup / Documentation

- [x] 4.1 Update `README.md` with `SECRET_KEY` setup, JWT login/me flow, and troubleshooting notes for 401/403 auth failures.
- [x] 4.2 Refresh `.env.example` comments/defaults if needed so JWT env vars match the documented setup.
