# Hexagonal Repository Layer Specification

## Purpose

Define the full data access, orchestration, and HTTP delivery layer for 8 entities (roles, library_users, categories, authors, books, book_authors, loans, returns) following a Ports and Adapters architecture on top of the existing sync SQLAlchemy + Oracle stack.

---

## Requirements

### Requirement: ORM Domain Models

The system MUST provide SQLAlchemy mapped classes for all 8 entities under `app/domain/models/`, each extending the shared `Base`. No FastAPI or Pydantic imports are permitted in the domain layer.

The `book_authors` association table MUST be defined as a plain `Table` object (not a mapped class) linking `books` and `authors`.

CHAR(1) Y/N database columns MUST be mapped via a `BoolChar` custom `TypeDecorator` that coerces `"Y"` → `True` and `"N"` → `False` on bind and on result.

The `roles` model MUST NOT include an `is_active` column. `authors` MUST NOT include `nationality`. `loans` MUST NOT include `notes`. `returns` MUST NOT include `condition` or `processed_by_user_id`.

#### Scenario: BoolChar bind roundtrip

- GIVEN a `BoolChar` TypeDecorator is in use on a model column
- WHEN a Python `True` value is set and the row is persisted
- THEN the database stores `"Y"` in the CHAR(1) column

#### Scenario: BoolChar result roundtrip

- GIVEN a row with `"Y"` stored in a CHAR(1) column
- WHEN the row is loaded via the ORM
- THEN the mapped attribute returns Python `True`

#### Scenario: BoolChar false roundtrip

- GIVEN a `BoolChar`-mapped column with `False` written
- WHEN the row is loaded back
- THEN the mapped attribute returns Python `False`

#### Scenario: Book authors relationship

- GIVEN a `Book` model instance loaded from the database
- WHEN the `authors` relationship is accessed
- THEN the related `Author` instances are returned without issuing additional N+1 queries (via `selectinload`)

---

### Requirement: Outbound Port Protocols

The system MUST define one `typing.Protocol` per entity under `app/application/ports/`. Each protocol MUST declare at minimum: `get(id) -> Model | None`, `list() -> list[Model]`, `create(data) -> Model`, `update(id, data) -> Model`, `delete(id) -> bool`.

Protocols MUST NOT reference SQLAlchemy, Oracle, or any infrastructure type. They describe capabilities in domain terms only.

#### Scenario: Protocol structural compatibility

- GIVEN a `*RepositorySql` adapter class
- WHEN it is used in place of the corresponding `typing.Protocol` port
- THEN Python's structural subtyping check passes (no `isinstance` required)

#### Scenario: Fake port satisfies protocol

- GIVEN an in-memory fake class that implements all methods of a port Protocol
- WHEN it is injected into an application service
- THEN the service executes without error

---

### Requirement: Repository Adapters

The system MUST provide one `*RepositorySql` class per entity under `app/infrastructure/repositories/`. All adapters MUST extend a generic `BaseRepository[Model]` that provides default `get`, `list`, `create`, `update`, and `delete` implementations using a synchronous SQLAlchemy `Session`.

Each adapter MUST accept the `Session` at call time (not at construction time) to remain compatible with FastAPI's `Depends`-scoped session.

`LoanRepositorySql.create` MUST catch `sqlalchemy.exc.DatabaseError` with Oracle error code `-20001` and re-raise it as `OutOfStockError`.

After a `ReturnRepositorySql.create` call, the session MUST call `session.expire(loan)` on the related `Loan` instance so that the next read reflects the trigger-updated `loans.status = 'RETURNED'`.

#### Scenario: Create loan with available stock

- GIVEN a book with stock > 0
- WHEN `LoanRepositorySql.create` is called
- THEN a `Loan` row is inserted and the created `Loan` is returned

#### Scenario: Create loan against zero-stock book

- GIVEN a book with stock = 0 and Oracle trigger raises ORA-20001
- WHEN `LoanRepositorySql.create` is called
- THEN `DatabaseError` with code -20001 is caught and `OutOfStockError` is raised

#### Scenario: Create return refreshes loan status

- GIVEN an active loan
- WHEN `ReturnRepositorySql.create` is called
- THEN the session expires the loan object so that subsequent reads show `status = 'RETURNED'`

#### Scenario: Get non-existent entity

- GIVEN an ID that does not exist in the database
- WHEN `BaseRepository.get(id)` is called
- THEN `None` is returned

---

### Requirement: Application Services

The system MUST provide one thin service class per entity under `app/application/services/`. Services MUST receive their port dependency via constructor injection and MUST NOT contain business logic beyond orchestration (delegate to ports, raise `NotFoundError` when `get` returns `None`).

Services MUST NOT import SQLAlchemy, oracledb, or any infrastructure module.

#### Scenario: Service get returns entity

- GIVEN a port fake that returns a model for a known ID
- WHEN the service's `get` method is called with that ID
- THEN the model is returned unchanged

#### Scenario: Service get raises NotFoundError

- GIVEN a port fake that returns `None` for an unknown ID
- WHEN the service's `get` method is called
- THEN `NotFoundError` is raised

#### Scenario: Service create delegates to port

- GIVEN a port fake that records `create` calls
- WHEN the service's `create` method is called with valid data
- THEN the port's `create` method is called exactly once with that data

---

### Requirement: Domain Error Types

The system MUST define `OutOfStockError`, `NotFoundError`, and `ConflictError` in `app/application/errors.py`. These MUST be plain Python exceptions with no FastAPI or HTTP imports.

#### Scenario: OutOfStockError is defined

- GIVEN the `app.application.errors` module is imported
- WHEN `OutOfStockError` is raised with a message
- THEN it is catchable as a standard `Exception`

---

### Requirement: FastAPI Routers

The system MUST expose a versioned REST API under `/api/v1/` with one router module per entity under `app/api/v1/routers/`. All routers MUST be aggregated in `app/api/v1/router.py` and registered in `main.py`.

Each entity router MUST implement:

| Method | Path | Success status |
|--------|------|---------------|
| GET | `/{entity}/` | 200 |
| GET | `/{entity}/{id}` | 200 |
| POST | `/{entity}/` | 201 |
| PUT | `/{entity}/{id}` | 200 |
| DELETE | `/{entity}/{id}` | 204 |

Routers MUST receive services via FastAPI `Depends` wired in `app/composition.py`. Routers MUST NOT instantiate repositories or sessions directly.

`GET /api/v1/books/{id}` MUST include the book's authors list in the response.

#### Scenario: List endpoint returns 200

- GIVEN the database contains at least one record for an entity
- WHEN `GET /api/v1/{entity}/` is called
- THEN the response status is 200 and the body is a JSON array

#### Scenario: Get existing resource returns 200

- GIVEN an entity with a known ID exists
- WHEN `GET /api/v1/{entity}/{id}` is called
- THEN the response status is 200 and the body contains the entity data

#### Scenario: Get non-existent resource returns 404

- GIVEN no entity exists for the requested ID
- WHEN `GET /api/v1/{entity}/{id}` is called
- THEN the response status is 404

#### Scenario: Create resource returns 201

- GIVEN a valid request body for a new entity
- WHEN `POST /api/v1/{entity}/` is called
- THEN the response status is 201 and the body contains the created entity with its assigned ID

#### Scenario: Create loan out of stock returns 409

- GIVEN a book with zero stock
- WHEN `POST /api/v1/loans/` is called for that book
- THEN the response status is 409 and the body contains an out-of-stock error detail

#### Scenario: Delete existing resource returns 204

- GIVEN an entity with a known ID exists
- WHEN `DELETE /api/v1/{entity}/{id}` is called
- THEN the response status is 204 and no body is returned

#### Scenario: Delete non-existent resource returns 404

- GIVEN no entity exists for the requested ID
- WHEN `DELETE /api/v1/{entity}/{id}` is called
- THEN the response status is 404

#### Scenario: Invalid request body returns 422

- GIVEN a request body with missing required fields
- WHEN `POST /api/v1/{entity}/` is called
- THEN the response status is 422 with Pydantic validation error details

#### Scenario: Book detail includes authors

- GIVEN a book linked to two authors in `book_authors`
- WHEN `GET /api/v1/books/{id}` is called
- THEN the response body contains an `authors` array with both authors

---

### Requirement: Schema Reconciliation

The system MUST remove orphan Pydantic fields that have no corresponding DB column:
- `AuthorRead.nationality` MUST be removed
- `LoanRead.notes` MUST be removed
- `ReturnRead.condition` and `ReturnRead.processed_by_user_id` MUST be removed
- `RoleBase.is_active` MUST be removed

#### Scenario: Author schema has no nationality field

- GIVEN the `AuthorRead` schema is serialized from an author ORM instance
- WHEN the JSON response is produced
- THEN the `nationality` key is absent from the response body

---

### Requirement: Composition Root and Dependency Injection

The system MUST define all DI factory functions in `app/composition.py`. `main.py` MUST NOT contain any repository or service instantiation. The composition root MUST wire session → repository → service → router in a single traceable location.

#### Scenario: DI graph is resolvable

- GIVEN FastAPI application starts
- WHEN a request to any entity endpoint is made
- THEN the full dependency chain (session → repo → service) is resolved without import errors

---

### Requirement: OpenAPI Documentation

The system MUST produce an OpenAPI schema at `/docs` that includes entries for every entity endpoint. All request and response models MUST be reflected accurately in the schema.

#### Scenario: OpenAPI lists all entity routes

- GIVEN the FastAPI application is running
- WHEN `GET /openapi.json` is called
- THEN the response includes paths for all 8 entities (roles, library_users, categories, authors, books, book_authors, loans, returns)
