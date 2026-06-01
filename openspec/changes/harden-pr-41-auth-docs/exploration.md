## Exploration: Harden and document PR #41 JWT authentication improvements.

### Current State
PR #41 (`origin/feat/auth-jwt`) introduces JWT login (`/api/v1/auth/login`), authenticated profile (`/api/v1/auth/me`), password hashing, and role-gated role mutation endpoints using `require_role("Admin")`. Token decode currently returns `None` on JWT errors, but `get_current_user()` still does `int(payload.get("sub", 0))` without guarding conversion, so malformed `sub` can raise `ValueError` and leak a 500 path instead of a controlled 401. Role authorization uses exact role-name string matching (`"Admin"`), which is simple but brittle if role naming drifts (case, localization, data migration). Environment config now requires `SECRET_KEY`, and `.env.example` documents it, but README does not yet explain startup impact, auth flow, or troubleshooting. Existing test suite covers many CRUD slices but does not include auth-focused tests for token parsing or role-gate behavior.

### Affected Areas
- `app/api/dependencies.py` — `get_current_user` and `require_role` contain the main hardening points (`sub` parsing and role checks).
- `app/core/security.py` — token encode/decode utility behavior drives what dependency-layer validation must handle.
- `app/application/services/auth_service.py` — emits JWT claims (`sub`, `role`) and therefore defines expected claim contract.
- `app/api/v1/routers/auth.py` — login/me endpoints where test coverage should validate happy-path and failure contracts.
- `app/api/v1/routers/roles.py` — admin-only mutation routes depend on role authorization behavior.
- `app/core/config.py` and `.env.example` — `SECRET_KEY` requirement and defaults affect runtime startup and deploy safety.
- `README.md` — missing explicit JWT setup, role-policy expectations, and auth verification checklist.
- `tests/` (new auth-focused test module) — currently no direct regression coverage for JWT edge cases or role authorization semantics.

### Approaches
1. **Minimal hardening patch** — Add strict `sub` parse guards and focused tests/docs, keep current role-name policy.
   - Pros: Smallest delta; low risk to merge; directly fixes known 500 risk and documentation gap.
   - Cons: Keeps brittle literal-role coupling (`"Admin"`); future naming drift can still break authorization semantics.
   - Effort: Low

2. **Policy hardening patch** — Add `sub` guards plus normalized/centralized role policy (e.g., constant set + case normalization), with broader tests/docs.
   - Pros: Fixes immediate parsing issue and makes authorization behavior more explicit and resilient.
   - Cons: Slightly larger surface (dependency + tests + docs) and requires clear decision on canonical role policy.
   - Effort: Medium

### Recommendation
Use **Approach 2**. It resolves the immediate runtime safety issue and reduces future authorization regressions by making role policy explicit and testable. Keep scope controlled: no auth architecture rewrite, only claim parsing hardening, role-check normalization/policy centralization, and targeted tests + README/env documentation.

### Risks
- If role policy is changed without aligning seed data/migrations, legitimate admins could be denied.
- Test environment inconsistency (missing pytest in some runners) can hide regressions unless setup instructions are explicit.
- If claim-contract assumptions between `AuthService` and `get_current_user` diverge, valid tokens may be rejected.

### Ready for Proposal
Yes — tell the user we can proceed with a scoped proposal covering: (1) safe token subject parsing with guaranteed 401 on malformed claims, (2) explicit/normalized admin authorization policy with regression tests, and (3) JWT setup and operational docs (SECRET_KEY requirements, local verification commands, and expected 401/403 behavior).
