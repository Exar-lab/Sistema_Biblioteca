# Delta for Core Persistence

## ADDED Requirements

### Requirement: SQLAlchemy Primary Persistence Path

The system MUST use SQLAlchemy repositories and services as the primary application persistence path for runtime reads and writes. FastAPI route handlers MUST NOT perform ad hoc raw SQL for normal catalog, circulation, user, or reporting workflows.

#### Scenario: Route persists through application data layer

- GIVEN a FastAPI endpoint creates or updates a library resource
- WHEN the endpoint performs persistence work
- THEN the request is handled through the service/repository data-access path backed by SQLAlchemy
- AND the route handler does not execute raw SQL directly.

#### Scenario: New persistence feature follows the primary path

- GIVEN a new application feature needs to read or write library data
- WHEN the feature is implemented
- THEN its runtime data access MUST use the established SQLAlchemy session, service, and repository path unless the behavior is explicitly database-owned.

### Requirement: Database Initialization and SQL Artifact Coexistence

The system MUST preserve Oracle `.sql` artifacts as first-class database initialization and operations assets while SQLAlchemy remains the application runtime persistence layer.

#### Scenario: Fresh Oracle database initialization

- GIVEN a developer or instructor needs to prepare a fresh Oracle database
- WHEN they follow the documented database setup path
- THEN the repository provides `.sql` artifacts for schema/bootstrap needs such as tables, constraints, triggers, sequences or identity definitions, and seed/reference data.

#### Scenario: SQL artifacts coexist with SQLAlchemy models

- GIVEN SQLAlchemy ORM mappings exist for application entities
- WHEN database-owned setup or Oracle-specific behavior is reviewed
- THEN the corresponding `.sql` files remain available and are not removed solely because ORM models exist.

#### Scenario: SQL artifact removal requires replacement rationale

- GIVEN an existing Oracle `.sql` artifact is proposed for removal
- WHEN the change is reviewed
- THEN the removal MUST identify the replacement mechanism and review rationale before acceptance.

### Requirement: Request-Scoped SQLAlchemy Session Usage

The system MUST provide request-scoped synchronous SQLAlchemy sessions for application persistence and MUST close or roll back sessions according to request outcome.

#### Scenario: Successful request uses one managed session

- GIVEN an API request performs one or more persistence operations
- WHEN the request completes successfully
- THEN the operations share the request-managed SQLAlchemy `Session`
- AND the transaction is committed and the session is closed by the database dependency lifecycle.

#### Scenario: Failed request rolls back session

- GIVEN an API request has opened a SQLAlchemy `Session`
- WHEN an unhandled exception or persistence error prevents successful completion
- THEN the transaction is rolled back
- AND the session is closed without leaking a connection.

#### Scenario: Direct session construction is avoided in handlers

- GIVEN a route handler needs database access
- WHEN the handler is reviewed
- THEN it MUST receive persistence capability through FastAPI dependency injection rather than constructing an engine or session directly.

### Requirement: Oracle-Specific Database Artifacts Remain Database-Owned

The system MUST keep Oracle-specific artifacts and invariants in Oracle-owned `.sql` assets when they are schema, trigger, constraint, sequence/identity, seed, maintenance, or manual DBA concerns.

#### Scenario: Trigger-owned stock update

- GIVEN the Oracle schema owns stock or return side effects through a trigger
- WHEN a return is recorded through the application
- THEN the application MUST let the database-owned invariant execute
- AND the application MAY refresh or re-read affected state to present the resulting stock or loan status.

#### Scenario: Constraint or trigger rejects invalid data

- GIVEN Oracle enforces an invariant through a constraint or trigger
- WHEN SQLAlchemy persistence attempts an invalid operation
- THEN the application MUST surface a user-appropriate failure without replacing the database invariant with conflicting Python logic.

#### Scenario: Manual DBA script remains out of runtime path

- GIVEN an Oracle maintenance or diagnostic script exists under database artifacts
- WHEN the FastAPI application handles normal runtime requests
- THEN that script MUST NOT be required for per-request application flow.

### Requirement: Single Ownership of Business Rules

The system MUST avoid duplicated or conflicting business-rule enforcement between Python services/repositories and Oracle triggers/constraints. Each rule MUST have one declared owner, while the other layer MAY validate inputs, translate errors, or present results.

#### Scenario: Database-owned invariant is translated, not duplicated

- GIVEN Oracle owns an invariant such as stock protection or trigger-updated return state
- WHEN the database rejects or changes a persistence operation
- THEN SQLAlchemy repositories/services MUST translate or refresh the result for application use
- AND MUST NOT implement a competing version of the same invariant that can diverge from Oracle behavior.

#### Scenario: Application-owned workflow rule remains in services

- GIVEN a workflow rule is not enforced by Oracle artifacts, such as blocking a user with overdue loans from creating a new loan
- WHEN the application evaluates the workflow
- THEN the rule MUST be enforced in the application service layer using SQLAlchemy-backed reads
- AND the route handler MUST only surface the service outcome.

#### Scenario: Ownership is clear before changing a rule

- GIVEN a persistence-related rule is modified
- WHEN the change is reviewed
- THEN the review MUST identify whether the rule is owned by SQLAlchemy-backed application code or Oracle `.sql` artifacts.

### Requirement: Persistence Verification Coverage

The system SHOULD include focused verification for the highest-risk persistence flows affected by SQLAlchemy and Oracle coexistence.

#### Scenario: Catalog persistence verification

- GIVEN catalog entities are managed through the application
- WHEN catalog create, read, update, or delete behavior is verified
- THEN the verification SHOULD exercise the SQLAlchemy service/repository path rather than route-level raw SQL.

#### Scenario: Circulation persistence verification

- GIVEN loan and return flows affect stock, loan status, and user eligibility
- WHEN persistence behavior is verified
- THEN tests or documented Oracle-gated checks SHOULD cover loan creation, return recording, stock/trigger effects, and overdue-user blocking.

#### Scenario: Oracle-gated checks are documented

- GIVEN a verification requires a running Oracle database or Oracle-specific artifact
- WHEN the check cannot run as a normal local unit test
- THEN the required environment and command SHOULD be documented so developers can run it intentionally.
