# Design: Adopt SQLAlchemy as the FastAPI Persistence Layer

Adopt SQLAlchemy as the bounded, teachable runtime persistence layer for the FastAPI + Oracle library app. FastAPI routes stay thin, request-scoped sessions are injected with `Depends`, application services own workflow rules, repository adapters own ORM queries and Oracle error translation, and Oracle `.sql` scripts remain the source of truth for schema, triggers, constraints, indexes, and seed/setup artifacts.

## Decision summary

| Area | Design decision |
|---|---|
| SQLAlchemy style | Use synchronous SQLAlchemy 2.x with `oracledb` because the app is currently synchronous and teachable for a 3-week project. |
| Transaction boundary | One `Session` per request from `app.core.database.get_db`; commit on success, rollback on error, always close. |
| Route responsibilities | Routes validate/serialize with Pydantic and call services. They do not run raw SQL or construct sessions. |
| Service responsibilities | Services coordinate business workflows, checks, and domain errors. They do not import SQLAlchemy. |
| Repository responsibilities | Repository adapters perform SQLAlchemy ORM reads/writes and translate infrastructure/database exceptions. |
| Model/schema boundary | ORM models map Oracle tables; Pydantic schemas define API request/response contracts. Do not use schemas as persistence models. |
| Oracle artifacts | `.sql` scripts remain first-class, database-owned artifacts for tables, constraints, triggers, indexes, identity/sequence behavior, seed data, and DBA setup. |
| Rule ownership | Each persistence rule has one owner: Python service for workflow rules, Oracle `.sql` for database invariants. The other layer may validate, refresh, or translate errors. |

## Current code alignment

The repository already contains the main building blocks this design should standardize rather than replace:

- `app/core/database.py`: engine, `SessionLocal`, request-scoped `get_db`, health smoke query.
- `app/core/base.py`: import-safe SQLAlchemy `Base`.
- `app/domain/models/*`: SQLAlchemy ORM mappings for Oracle tables.
- `app/schemas/*`: Pydantic v2 request/response schemas with `from_attributes=True`.
- `app/application/ports/*`: repository protocols/contracts used by services.
- `app/application/services/*`: business workflow layer with no infrastructure imports.
- `app/infrastructure/repositories/*`: SQLAlchemy repository adapters.
- `app/composition.py` and `app/api/dependencies.py`: service/repository wiring and FastAPI dependency exports.
- `database/oracle_schema.sql`: Oracle-owned schema, triggers, indexes, and seed/bootstrap logic.

## Module layout

Keep the architecture small and explicit:

```text
app/
  api/
    dependencies.py          # Re-export get_db and service factories
    exception_handlers.py    # Domain error -> HTTP response
    v1/routers/              # Thin FastAPI route handlers
  application/
    errors.py                # Domain/application exceptions
    ports/                   # Repository Protocols used by services
    services/                # Workflow/business orchestration
  core/
    base.py                  # Declarative Base only
    config.py                # Settings, DATABASE_URL, SQLALCHEMY_ECHO
    database.py              # Engine, SessionLocal, get_db lifecycle
  domain/models/             # SQLAlchemy ORM mappings to Oracle tables
  infrastructure/repositories/ # SQLAlchemy adapters for ports
  schemas/                   # Pydantic API schemas
database/
  oracle_schema.sql          # DB-owned DDL, triggers, indexes, seed/setup
```

### Import rules

| Layer | May import | Must not import |
|---|---|---|
| `api` | schemas, services, dependencies, domain errors | repository implementations directly, `SessionLocal`, raw SQL for normal workflows |
| `application/services` | ports, domain errors, plain Python/date helpers | SQLAlchemy, FastAPI, repository implementations |
| `application/ports` | `typing.Protocol`, `Any` | SQLAlchemy concrete classes unless a narrow type is intentionally chosen |
| `infrastructure/repositories` | SQLAlchemy, ORM models, domain errors for translation | FastAPI routes or request objects |
| `domain/models` | SQLAlchemy mapping primitives and custom types | Pydantic schemas, services, routers |
| `schemas` | Pydantic | SQLAlchemy sessions/queries |
| `core/database` | settings, SQLAlchemy engine/session tools | route/service/repository business logic |

## Dependency injection and session lifecycle

### Runtime path

1. A route receives a request and declares:
   - `db: Session = Depends(get_db)`
   - `service: SomeService = Depends(get_some_service)`
2. `get_db` creates one SQLAlchemy `Session` for the request.
3. The route calls one service method and passes the session.
4. The service calls one or more repository methods using that same session.
5. Repositories call SQLAlchemy ORM queries/mutations and `flush()` when IDs/server-side effects are needed before response creation.
6. `get_db` commits if the request completes normally.
7. `get_db` rolls back if an exception escapes.
8. `get_db` closes the session in all cases.

### Dependency contract

`app/core/database.py` is the only runtime module that constructs sessions:

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

Rules:

- Route handlers use `Depends(get_db)`; they do not call `SessionLocal()`.
- Service factories in `app/composition.py` stay stateless. Repositories do not store a session on `self`.
- A request shares the same session across all repository calls so multi-step workflows commit or roll back together.
- Health checks may use `SessionLocal()` directly only because they are infrastructure diagnostics, not application workflow handlers.

## Model and schema boundaries

### ORM models

ORM models in `app/domain/models` map the existing Oracle schema exactly:

- Table names and schema: `__tablename__`, `__table_args__ = {"schema": "BIBLIOTECA"}`.
- Columns mirror `database/oracle_schema.sql` names, nullability, defaults, and FK relationships.
- Oracle-owned defaults use `server_default`, for example `SYSTIMESTAMP` and `'Y'`.
- Many-to-many book authors use a SQLAlchemy association `Table`, not an extra API object unless the product later needs one.
- Custom Oracle representations, such as `CHAR(1)` booleans, stay behind a small type adapter like `BoolChar`.

ORM models are not API contracts. They may be returned from services because Pydantic response schemas have `from_attributes=True`, but API field shape is still controlled by `app/schemas`.

### Pydantic schemas

Pydantic schemas in `app/schemas` remain the external contract:

- `*Create`: fields allowed on creation.
- `*Update`: optional fields allowed on update.
- `*Read`: fields returned to clients.
- Sensitive fields, such as passwords, must not appear in read schemas.
- Schema aliases and validation belong here, not in repositories.

Repositories may accept a schema or dict and convert with `model_dump(exclude_unset=True)` as the current base repository does.

## Repository and service usage

### Default CRUD path

Use the existing lightweight repository base for simple tables:

```text
route -> service -> repository port -> SQLAlchemy adapter -> Oracle
```

Example responsibilities:

- Route: `POST /roles` accepts `RoleCreate`, injects `Session` and `RoleService`, returns `RoleRead`.
- Service: calls `repo.create(session, payload)` and raises `NotFoundError`/`ConflictError` when needed.
- Repository: constructs `Role(**data)`, adds it, flushes, refreshes, returns ORM object.

### When to add custom repository methods

Add a method to the repository port and SQLAlchemy adapter when a query is reusable or domain-specific, for example:

- `LoanRepository.get_by_user(session, user_id)`
- `LoanRepository.has_overdue_loans(session, user_id)`
- `BookRepository.get_with_authors(session, book_id)`
- `BookRepository.set_authors(session, book, author_ids)`

Do not add a repository method for one-off formatting that belongs in schemas or the route response.

### When to add service logic

Add service logic when a workflow spans multiple checks or has business meaning:

- Verify referenced user/book exists before creating a loan.
- Block users with active overdue loans.
- Ensure a return is linked to an existing active loan.
- Convert a duplicate, conflict, or database-owned failure into a domain error.

Keep services free of SQLAlchemy imports. They should depend on repository ports so unit tests can use simple fakes.

## Oracle `.sql` artifacts remain source of truth

SQLAlchemy is the application runtime persistence layer. It does not replace the Oracle setup scripts.

Keep `database/oracle_schema.sql` as the authoritative artifact for:

- `CREATE USER`, grants, and schema setup.
- Tables, primary keys, foreign keys, checks, unique constraints.
- Identity columns or sequences.
- Triggers, including updated timestamp triggers and stock/return side effects.
- Indexes.
- Seed/reference data.
- Manual DBA setup or maintenance logic.

SQLAlchemy models must mirror these artifacts; they should not silently redefine ownership. Do not use `Base.metadata.create_all()` as the normal Oracle initialization path unless a future change explicitly introduces migrations and documents how they relate to `.sql` scripts.

## Rule ownership matrix

| Rule or behavior | Owner | Application behavior |
|---|---|---|
| Table shape, constraints, indexes | Oracle `.sql` | ORM models mirror shape; app surfaces errors cleanly. |
| `updated_at` timestamp changes | Oracle trigger | ORM may refresh/expire if response needs updated value. |
| Decrement stock on loan insert | Oracle trigger | Repository flushes; translates Oracle out-of-stock error to `OutOfStockError`. |
| Restore stock and mark loan returned on return insert | Oracle trigger | Repository expires or refreshes affected loan fields after flush. |
| Block user with overdue active loans | Python service | Service queries via repository and raises `ConflictError`. |
| API payload validation | Pydantic schema | Route receives typed payload; service receives schema/dict. |
| HTTP status and response shape | FastAPI route/exception handlers | Domain errors translated once in API layer. |

## Error translation

Repositories are the boundary for infrastructure-specific errors:

- Oracle user-defined errors, such as `ORA-20001` from the checkout stock trigger, are caught in the SQLAlchemy adapter and raised as domain errors like `OutOfStockError`.
- Services raise domain errors for workflow failures (`NotFoundError`, `ConflictError`).
- API exception handlers translate domain errors into HTTP responses.
- Routes should not parse Oracle error strings.

## Data flow examples

### Create loan

1. `POST /loans` receives `LoanCreate`.
2. Route injects `Session` and `LoanService`.
3. `LoanService.create` checks user exists, book exists, and user has no active overdue loans.
4. `LoanRepositorySql.create` inserts the loan and flushes.
5. Oracle trigger decrements stock or raises out-of-stock error.
6. Repository translates out-of-stock Oracle error to `OutOfStockError`.
7. `get_db` commits on success or rolls back on error.

### Record return

1. `POST /returns` receives `ReturnCreate`.
2. Service loads the loan and delegates return creation.
3. Repository inserts the return and flushes.
4. Oracle trigger updates loan status/return date and restores stock.
5. Repository expires or refreshes stale loan fields when the response needs them.
6. `get_db` commits the full request.

## Testing and verification

### Fast local checks

- `python -m compileall app main.py`
- `python -m pytest tests/unit`
- Route/session lifecycle tests with monkeypatched `SessionLocal`.
- Service tests using fake repository ports.

### Oracle-gated checks

Run only when Oracle and `DATABASE_URL` are configured:

- Repository integration tests for catalog CRUD.
- Loan creation with available stock.
- Loan creation when Oracle trigger rejects out-of-stock.
- Return creation and trigger-updated loan/stock state.
- Health endpoint against a running database.

Document Oracle-gated commands in project docs if they differ from `python -m pytest`.

## Implementation plan

1. **Stabilize database core**
   - Keep `app/core/base.py` import-safe.
   - Keep `app/core/database.py` as the only engine/session factory.
   - Ensure `DATABASE_URL` supports `oracle+oracledb://...`.

2. **Mirror Oracle schema with ORM models**
   - Audit each ORM model against `database/oracle_schema.sql`.
   - Confirm table names, schema, columns, nullability, defaults, FKs, and relationships.
   - Avoid adding ORM-only columns that do not exist in Oracle.

3. **Standardize repositories and ports**
   - Use `SqlRepositoryBase` for normal CRUD.
   - Add explicit port methods for domain queries.
   - Translate Oracle-specific exceptions inside repository adapters.

4. **Keep services as workflow owner**
   - Move route-level business checks into services.
   - Keep services typed against ports and domain errors.
   - Use fake repositories for unit tests.

5. **Keep routes thin**
   - Route handlers inject `Session` and service.
   - No raw SQL in route handlers for normal catalog, circulation, user, or reporting workflows.
   - Use exception handlers for domain errors.

6. **Preserve SQL artifacts**
   - Treat `database/oracle_schema.sql` as required setup documentation and artifact.
   - Update `.sql` first when database-owned behavior changes.
   - Update ORM models to mirror the changed DB artifact.

7. **Verify high-risk flows**
   - Unit-test service rules.
   - Integration-test Oracle trigger interactions where available.
   - Keep Oracle-gated tests clearly marked/documented.

## Rollout guidance

This can be adopted incrementally by entity:

1. Start with low-risk CRUD entities (`roles`, `categories`, `authors`).
2. Move to relationship-heavy catalog flows (`books`, `book_authors`).
3. Move to trigger-sensitive circulation flows (`loans`, `returns`).
4. Add reporting queries last, using repositories/services and SQLAlchemy query constructs. If a report requires Oracle-specific SQL, isolate it in a repository method and document why it is database-specific.

Do not introduce Alembic or async SQLAlchemy in this change unless the team explicitly chooses that added complexity. The current synchronous path is simpler and consistent with the existing app.

## Out of scope

- Replacing Oracle `.sql` scripts with ORM migrations.
- Adding React or a separate frontend architecture.
- Rewriting the app to async SQLAlchemy.
- Designing full authentication/session security beyond the persistence boundary.
- Optimizing every query before functional flows are complete.

## Acceptance checklist

- [ ] Routes receive `Session` through `Depends(get_db)` and do not construct sessions directly.
- [ ] Normal runtime persistence flows use service/repository methods backed by SQLAlchemy.
- [ ] Services contain workflow rules and do not import SQLAlchemy or FastAPI.
- [ ] Repositories contain SQLAlchemy code and translate Oracle-specific persistence errors.
- [ ] ORM models mirror `database/oracle_schema.sql` rather than replacing it.
- [ ] Oracle `.sql` artifacts remain in the repo and are documented as setup/DB-owned behavior.
- [ ] Trigger-owned behavior is refreshed/expired or translated by repositories when needed.
- [ ] Unit and Oracle-gated verification paths are documented.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| ORM model drifts from Oracle schema | Review model changes alongside `database/oracle_schema.sql`; prefer DB artifact as source. |
| Business rule duplicated in trigger and service | Use the rule ownership matrix in reviews before changing persistence behavior. |
| Session leaks or partial commits | Keep one `get_db` dependency; avoid committing in repositories/services. |
| Oracle trigger side effects look stale in SQLAlchemy | Use `session.refresh()` or `session.expire()` in repository adapters after trigger-owned writes. |
| Architecture becomes too abstract for students | Keep repositories thin, services explicit, and avoid generic framework expansion until duplication proves it is needed. |

## SDD result contract

status: completed
phase: design
skill_resolution: paths-injected
artifacts:
  - openspec/changes/adopt-sqlalchemy-persistence/design.md
  - openspec/changes/adopt-sqlalchemy-persistence/specs/core/spec.md
summary:
  - Designed a synchronous SQLAlchemy adoption approach for the FastAPI + Oracle app.
  - Covered module layout, DI/session lifecycle, ORM/Pydantic boundaries, repository/service usage, Oracle `.sql` coexistence, rule ownership, tests, and rollout.
  - Kept the approach bounded to the current app structure and teachable for the project scope.
engram:
  status: unavailable
  notes: No Engram memory tools were exposed in this subagent runtime, so persistence was limited to requested files.
