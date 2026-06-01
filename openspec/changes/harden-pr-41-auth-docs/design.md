# Design: Harden PR #41 Auth & Docs

## Technical Approach

Apply a focused auth-hardening slice on top of PR #41 auth flow: keep existing FastAPI dependency-injection style, but enforce strict JWT claim validation in `get_current_user`, centralize admin role policy in one constant/normalizer, add regression tests, and document operational JWT setup in `README.md`. No auth rewrite, no DB model changes.

## Architecture Decisions

### Decision: JWT `sub` validation boundary

| Option | Tradeoff | Decision |
|---|---|---|
| Validate `sub` only in `AuthService` issuer | Safer tokens at source, but does not protect against externally forged/malformed tokens | ❌ |
| Validate in `get_current_user` after decode | Catches all inbound tokens at trust boundary; small dependency-layer change | ✅ |

Rationale: this is the runtime boundary where untrusted token data enters request authorization.

### Decision: Role policy representation

| Option | Tradeoff | Decision |
|---|---|---|
| Keep literal `"Admin"` checks | Smallest patch, brittle against case/localization drift | ❌ |
| Central policy constant + normalization helper (`strip().casefold()`) | Slightly more code, much more explicit and testable | ✅ |

Rationale: reduces regressions and aligns with proposal goal of explicitized authorization policy.

### Decision: Decode error contract

| Option | Tradeoff | Decision |
|---|---|---|
| Let decode raise and map globally | Can leak inconsistent 500/401 mapping if unhandled | ❌ |
| Return `None`/invalid payload and map to 401 in dependency | Preserves current pattern, gives stable API contract | ✅ |

Rationale: keeps behavior predictable without introducing framework-wide exception coupling.

## Data Flow

`Authorization: Bearer <jwt>`
→ `auth` router/dependency extracts token
→ `security.decode_access_token(token)`
→ `dependencies.get_current_user()` validates `sub` + role claims
→ user lookup (service/repository)
→ route handler

Failure paths:
- decode/claim parse failure → `401 Unauthorized`
- role mismatch in gate dependency → `403 Forbidden`

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/api/dependencies.py` | Modify | Add strict `sub` parsing guard (type + positive int), centralized role normalization, and role-gate helper using policy constants. |
| `app/core/security.py` | Modify | Keep decode contract aligned with dependency checks (invalid/expired token returns invalid payload marker or `None`). |
| `app/application/services/auth_service.py` | Modify | Ensure emitted JWT claims keep stable contract (`sub`, `username`, `role`) and consistent `sub` type. |
| `app/api/v1/routers/auth.py` | Modify | Keep login/me endpoints delegating to hardened dependencies; no business-rule logic in router. |
| `app/api/v1/routers/roles.py` | Modify | Replace literal admin gate usage with centralized role policy dependency. |
| `tests/test_auth.py` | Create | Add regression tests: malformed `sub` → 401, expired/invalid token → 401, admin gate deny/allow behavior. |
| `README.md` | Modify | Add `SECRET_KEY` requirement, JWT flow, and auth troubleshooting/verification commands. |
| `.env.example` | Modify | Ensure documented `SECRET_KEY` example and minimal guidance. |

## Interfaces / Contracts

```python
# app/api/dependencies.py
ADMIN_ROLE_CANONICAL = "admin"

def normalize_role(role: str | None) -> str:
    return (role or "").strip().casefold()

def parse_token_subject(payload: dict[str, object]) -> int | None:
    # accept int or numeric str; reject None/blank/non-numeric/non-positive
    ...
```

HTTP contract:
- Authenticated endpoints MUST return `401` for malformed/invalid token claims.
- Role-protected endpoints MUST return `403` for authenticated non-admin users.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Subject parsing + role normalization helpers | Pure function tests for edge cases (`None`, `""`, `"abc"`, `" 1 "`, case variants). |
| Integration | Auth dependency + route behavior | `TestClient` with dependency overrides/fake services; assert 401/403/200 contracts. |
| E2E | N/A in this slice | No browser/system tests; keep to pytest API slice scope. |

## Migration / Rollout

No migration required. Roll out as a patch release of auth behavior. If unexpected admin denials appear, rollback by reverting dependency/security changes and restoring previous role-gate behavior.

## Open Questions

- [ ] This slice currently does not contain PR #41 auth modules (`app/core/security.py`, `app/api/v1/routers/auth.py`, `app/application/services/auth_service.py`). Should this change target the PR #41 branch directly, or include those files as part of this patch?
- [ ] Canonical admin policy: should accepted values be strictly `admin` or include Spanish aliases (e.g., `administrador`) for backward compatibility?
