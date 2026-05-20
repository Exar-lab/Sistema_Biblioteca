# Proposal: Hexagonal Repository Layer for All Entities

## Intent

The project has schemas, config, and a sync SQLAlchemy engine, but ZERO domain/application/infrastructure/router code. We need a complete data access + service + HTTP layer for the 8 core entities (`roles`, `library_users`, `categories`, `authors`, `books`, `book_authors`, `loans`, `returns`) following hexagonal architecture so business logic stays independent of FastAPI and Oracle. Success = full CRUD reachable via `/api/v1/*` endpoints, repositories isolated behind ports, Oracle trigger semantics preserved, and tests possible with in-memory fakes.

## Scope

### In Scope
- SQLAlchemy ORM mapped classes for all 8 entities under `app/domain/models/`
- `typing.Protocol` outbound ports per entity under `app/application/ports/`
- SQLAlchemy adapter repositories under `app/infrastructure/repositories/` (incl. generic `BaseRepository`)
- Thin application services under `app/application/services/` orchestrating ports
- FastAPI routers under `app/api/v1/routers/` for every entity + registration in `main.py`
- `BoolChar` `TypeDecorator` to map Oracle `CHAR(1) Y/N` to Python `bool`
- Oracle error translation layer: catch `-20001` (stock=0) and raise domain `OutOfStockError`
- Schema/ORM reconciliation (drop or map orphan Pydantic fields)
- Composition root for dependency injection via FastAPI `Depends`

### Out of Scope
- Authentication / JWT / `python-jose` / `passlib` (no auth in this change; routers are unauthenticated)
- Dashboard / reports queries (`DashboardSummary`, `ReportsDashboard`)
- Async migration — stays sync (`Session`, not `AsyncSession`)
- Alembic migrations — DB schema is owned by `database/oracle_schema.sql`
- Frontend / UI work
- Stock recalculation logic — owned by Oracle triggers, repos stay transparent

## Capabilities

### New Capabilities
- `domain-models`: SQLAlchemy ORM classes for the 8 entities, including Oracle-specific mappings (schema prefix, IDENTITY PKs, `BoolChar`)
- `repository-ports`: `typing.Protocol` outbound ports defining CRUD + entity-specific queries
- `repository-adapters`: SQLAlchemy implementations of the ports with Oracle error translation
- `application-services`: Thin use-case orchestration per aggregate (roles, users, catalog, circulation)
- `rest-api-v1`: FastAPI routers exposing CRUD for all entities under `/api/v1/`

### Modified Capabilities
- None (no prior specs exist)

## Approach

**Hexagonal with `typing.Protocol` ports.** Three layers, dependency inward only:

1. **Domain** — pure SQLAlchemy mapped classes extending existing `Base`. No FastAPI imports. `BoolChar` TypeDecorator centralizes Y/N coercion.
2. **Application** — outbound ports as `Protocol` classes (structural subtyping, no ABC inheritance). Services receive ports via constructor, return Pydantic schemas.
3. **Infrastructure** — concrete `*RepositorySql` classes implementing ports; catch `DatabaseError` with Oracle code `-20001` and re-raise as `OutOfStockError`.
4. **API** — routers depend on services via `Depends`; services wired in composition root (`app/composition.py`).

Generic `BaseRepository[Model]` provides `get/list/create/update/delete`; entity repos extend with domain-specific queries (e.g. `BookRepository.find_by_isbn`, `LoanRepository.list_active_by_user`).

### Schema/DB mismatch resolutions (pragmatic — align to DB reality)
- `AuthorRead.nationality` → REMOVE from schema (DB has `birth_date`/`death_date` instead)
- `LoanRead.notes` → REMOVE (no DB column)
- `ReturnRead.condition`, `processed_by_user_id` → REMOVE; keep `notes`
- `RoleBase.is_active` → REMOVE (no DB column on `roles`)
- `library_users.is_active` and similar CHAR(1) cols → mapped via `BoolChar`

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/domain/models/` | New | 8 ORM classes + `book_authors` association table + `BoolChar` |
| `app/application/ports/` | New | Protocol per entity |
| `app/application/services/` | New | Thin orchestration services |
| `app/application/errors.py` | New | `OutOfStockError`, `NotFoundError`, `ConflictError` |
| `app/infrastructure/repositories/` | New | Base + 8 SQLAlchemy adapters |
| `app/api/v1/routers/` | New | Routers for roles, users, categories, authors, books, loans, returns |
| `app/api/v1/router.py` | New | Aggregates routers under `/api/v1` |
| `app/composition.py` | New | DI factories for services |
| `app/schemas/**` | Modified | Drop orphan fields (nationality, notes, condition, role.is_active) |
| `main.py` | Modified | Register v1 router |
| `tests/` | New | Unit tests with in-memory fake repos; integration tests gated by `RUN_DB_TESTS` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Oracle `-20001` not caught uniformly across loan paths | Med | Centralize translation in `LoanRepositorySql.create()` with explicit `DatabaseError.args[0].code` check |
| `BoolChar` TypeDecorator misbehaves with SQLAlchemy expressions (filters, defaults) | Med | Unit test the TypeDecorator with `process_bind_param`/`process_result_value` round-trips |
| Schema reductions break consumers expecting fields (none yet, but routers will use schemas) | Low | Done before routers are built; document in this proposal |
| Trigger ordering on `returns` insert (sets `loans.status='RETURNED'`) collides with ORM session state | Med | After `returns.create()`, `session.expire(loan)` to force reload from DB |
| Many-to-many `book_authors` association eager/lazy loading n+1 | Med | Use `selectinload(Book.authors)` in list queries |

## Rollback Plan

All work lands in net-new directories (`app/domain/`, `app/application/`, `app/infrastructure/`, `app/api/v1/`). To roll back: remove these directories, revert `main.py` to its current bare state, and revert the schema field deletions. Existing tests (`tests/test_health_and_db_lifecycle.py`) are untouched and remain green.

## Dependencies

- No new pip dependencies required for this change (SQLAlchemy + oracledb already present)
- Oracle schema must remain at the version defined in `database/oracle_schema.sql`

## Success Criteria

- [ ] All 8 entities have ORM models, ports, repositories, services, and routers
- [ ] `BoolChar` round-trips bool ↔ `Y`/`N` correctly
- [ ] Loan creation against a zero-stock book returns HTTP 409 with `OutOfStockError` translated from Oracle `-20001`
- [ ] Return creation flips `loans.status` to `RETURNED` and the API reflects it (trigger-driven, verified by repo re-fetch)
- [ ] `GET /api/v1/books/{id}` includes nested authors without n+1
- [ ] Existing health/db-lifecycle tests still pass; new unit tests cover services with in-memory fake ports
- [ ] `main.py` registers the v1 router and OpenAPI shows endpoints for every entity
