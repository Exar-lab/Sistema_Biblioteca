# Proposal: Adopt SQLAlchemy as the Primary Persistence Layer

Make SQLAlchemy the default application persistence path for the FastAPI + Oracle library system while keeping Oracle `.sql` artifacts as first-class operational assets. This is a consolidation change: the project already contains SQLAlchemy, Oracle connectivity, ORM/repository structure, and `database/oracle_schema.sql`; this proposal clarifies ownership boundaries and limits scope to what a 3-week student project can deliver safely.

## Intent

Use SQLAlchemy for application CRUD and business persistence so FastAPI routes and services interact with one consistent Python data-access layer. Keep raw Oracle SQL files for database setup and Oracle-specific behavior that is clearer, safer, or required at the database level.

## Scope

### In Scope

- Treat SQLAlchemy ORM models, sessions, and repositories as the primary path for application reads/writes.
- Standardize request-scoped database access through `app.core.database.get_db` and service/repository dependencies.
- Keep synchronous SQLAlchemy (`Session`) rather than introducing async DB access.
- Preserve `.sql` artifacts for:
  - schema/bootstrap scripts,
  - Oracle triggers and constraints,
  - seed/reference data,
  - DBA/manual setup notes,
  - Oracle-specific smoke or maintenance scripts.
- Document the ownership rule: application behavior uses SQLAlchemy; database-owned invariants stay in Oracle SQL.
- Add or update focused verification for catalog, loan, return, and stock/overdue rules where practical.

### Out of Scope

- Deleting existing `.sql` files just because SQLAlchemy exists.
- Introducing Alembic or a full migration framework unless the team explicitly chooses it later.
- Rewriting the architecture to a complex framework split beyond the current route/service/repository pattern.
- Migrating to async SQLAlchemy.
- Replacing Oracle triggers with Python-only stock logic when the schema already owns those invariants.
- Building new frontend features as part of this persistence decision.

## Affected Areas

| Area | Impact | Notes |
|------|--------|-------|
| `app/core/database.py` | Confirm/standardize | Remains the SQLAlchemy engine/session boundary and FastAPI DB dependency. |
| `app/domain/models/` | Confirm/harden | ORM models remain the Python representation of application persistence entities. |
| `app/infrastructure/repositories/` | Confirm/harden | Repositories remain the only place application code performs SQLAlchemy queries. |
| `app/application/services/` | Confirm/harden | Services keep business rules and avoid direct SQLAlchemy imports where already isolated. |
| `app/api/**` | Confirm/harden | Routes receive services/session dependencies; no raw SQL in route handlers. |
| `database/*.sql` | Preserve | SQL files remain authoritative for Oracle bootstrap, triggers, constraints, seed data, and manual DBA setup. |
| `requirements.txt` | Verify only | SQLAlchemy and `oracledb` are already present; avoid dependency churn. |
| `tests/` | Targeted additions | Add practical repository/service checks where they reduce risk without requiring a large Oracle CI setup. |
| `README.md` / setup docs | Clarify | Explain when to use SQLAlchemy versus `.sql` scripts. |

## Coexistence Rules for SQLAlchemy and `.sql`

| Concern | Owner | Rationale |
|---------|-------|-----------|
| Application CRUD | SQLAlchemy repositories | Keeps FastAPI code teachable, testable, and consistent. |
| Query composition for screens/APIs | SQLAlchemy repositories/services | Avoids scattering raw SQL through routes. |
| Oracle schema creation/bootstrap | `.sql` artifacts | Easy for students/instructors to run and inspect directly in Oracle. |
| Triggers, constraints, sequences/identity details | `.sql` artifacts | These are database-level invariants and Oracle-specific behavior. |
| Seed/reference data | `.sql` artifacts, optionally loaded by documented steps | Keeps demo setup reproducible. |
| Emergency diagnostics/manual DBA scripts | `.sql` artifacts | Not part of app runtime; useful for class demonstrations and troubleshooting. |
| Future schema migrations | Deferred decision | Do not add Alembic in this change; revisit only if manual SQL becomes unmanageable. |

## Practical Approach

1. **Declare SQLAlchemy as the app runtime path.** New FastAPI features should call services/repositories instead of executing ad hoc SQL in routes.
2. **Keep Oracle SQL as database documentation and setup.** Do not delete `database/oracle_schema.sql`; update it when database-level rules change.
3. **Avoid dual ownership.** If a rule is enforced by a trigger/constraint, Python should surface and translate the result rather than duplicate conflicting logic.
4. **Test the highest-risk flows.** Prioritize loans, returns, stock changes, and overdue blocking over broad low-value CRUD tests.
5. **Keep the implementation simple.** Prefer current synchronous SQLAlchemy and existing FastAPI dependency injection patterns.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Confusion between ORM models and `.sql` schema as sources of truth | Medium | Document ownership: SQLAlchemy owns app access; `.sql` owns Oracle bootstrap/database invariants. |
| Schema drift between ORM mappings and Oracle scripts | Medium | Add review checklist and targeted tests/smoke checks for mapped columns and core flows. |
| Duplicated business rules in Python and triggers diverge | Medium | Let Oracle triggers/constraints enforce DB invariants; repositories translate DB errors where needed. |
| Over-engineering for a 3-week project | Medium | Keep sync SQLAlchemy, no Alembic, no async migration, no new framework layers in this change. |
| Oracle-dependent tests are hard to run on every machine | Medium | Keep unit tests with fakes where possible and gate Oracle integration tests with environment variables. |

## Rollback Plan

This proposal is mainly a standards/consolidation decision. If it causes churn or blocks delivery:

1. Stop adding new SQLAlchemy-specific refactors beyond existing code.
2. Revert documentation/spec changes that declare SQLAlchemy as mandatory.
3. Keep existing `.sql` files untouched so Oracle setup remains available.
4. Preserve working FastAPI health and database smoke checks.
5. Reassess whether a smaller per-feature persistence rule is enough for the course deadline.

## Success Criteria

- [ ] Project documentation clearly says SQLAlchemy is the primary application persistence layer.
- [ ] `.sql` artifacts are explicitly preserved for Oracle bootstrap, triggers, constraints, seed data, and manual setup.
- [ ] New app persistence code uses repositories/services instead of raw SQL in routes.
- [ ] No existing Oracle SQL artifact is removed without a named replacement and review rationale.
- [ ] Core catalog and circulation flows can be verified with `python -m pytest` and/or documented Oracle-gated checks.
- [ ] The team can explain which layer owns a persistence change before implementing it.

## Next Step

Proceed to the OpenSpec spec/design phase to capture concrete requirements and scenarios for SQLAlchemy-vs-Oracle-SQL ownership, then plan small verification tasks around catalog, loans, returns, stock, and overdue blocking.
