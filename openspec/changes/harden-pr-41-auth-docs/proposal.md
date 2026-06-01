# Proposal: Harden PR #41 Auth & Docs

## Intent

Prevent 500 errors on malformed JWT claims and reduce future authorization regressions. We must harden token parsing, explicitize role policies, and document JWT operational behavior for developers.

## Scope

### In Scope
- Add strict parsing guards for JWT `sub` to return controlled 401s instead of 500s.
- Centralize and normalize role validation (e.g., case-insensitive or constant-based) replacing bare `"Admin"` strings.
- Add regression tests covering token parsing failures and role-gate behavior.
- Document JWT requirements (`SECRET_KEY`), auth flows, and troubleshooting in `README.md`.

### Out of Scope
- Complete auth architecture rewrite or migration to new auth providers.
- Changes to database models or database role seeding.

## Capabilities

### New Capabilities
- `authentication`: Covers JWT token handling, login/me endpoints, token validation guards, and role-based authorization policy.

### Modified Capabilities
- None

## Approach

Implement **Policy hardening patch**: Add `sub` validation guards within `get_current_user()` to intercept malformed tokens early. Centralize role policy to a constant or normalized Enum to eliminate brittle literal matching. Write targeted pytest functions for these specific auth boundaries. Update `README.md` to clarify deployment and troubleshooting expectations.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/api/dependencies.py` | Modified | Add `sub` parsing guard; use centralized role policy. |
| `app/core/security.py` | Modified | Ensure decode behavior aligns with dependency expectations. |
| `README.md` | Modified | Add JWT operational setup and troubleshooting docs. |
| `tests/test_auth.py` | New | Add regression tests for token parsing and roles. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Denying legitimate admins if role policy drifts from DB | Medium | Ensure new normalized check accommodates existing casing/DB conventions. |
| Test environment inconsistency hiding regressions | Low | Add explicit test setup instructions in `README.md`. |

## Rollback Plan

Revert the specific commits modifying `dependencies.py` and `security.py` to restore the original PR #41 behavior if valid tokens are unexpectedly rejected.

## Dependencies

- None

## Success Criteria

- [ ] Malformed JWT `sub` claims return 401, not 500.
- [ ] Role checks use a centralized constant/policy, not bare string literals.
- [ ] Test suite explicitly covers invalid tokens and role denial.
- [ ] `README.md` explains `SECRET_KEY` usage and auth troubleshooting.
