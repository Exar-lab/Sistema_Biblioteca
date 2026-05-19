# Core Infrastructure Specification

## Purpose

Defines the database connection lifecycle, configuration, and health monitoring for the Library System, connecting FastAPI to Oracle Database via SQLAlchemy in sync mode.

## Requirements

### Requirement: Database Configuration

The system MUST load database connection settings securely from environment variables without hardcoded credentials.

#### Scenario: Load Database URL
- GIVEN the application starts
- WHEN `DATABASE_URL` is set in the environment or `.env`
- THEN the system uses this URL to configure the Oracle driver

### Requirement: Session Management

The system MUST manage database connections securely using a request-scoped lifecycle for route dependencies, while one-off smoke checks MUST close their session after use.

#### Scenario: Request dependency completes successfully
- GIVEN an active API request using the `get_db` dependency
- WHEN the request completes successfully
- THEN the session is committed and closed securely

#### Scenario: Request dependency fails
- GIVEN an active API request using the `get_db` dependency
- WHEN an unhandled exception occurs
- THEN the database session is rolled back and closed

#### Scenario: Health smoke check completes
- GIVEN the `/health` endpoint opens a short-lived database session
- WHEN the smoke query completes or fails
- THEN the session is closed without requiring the request dependency commit path

### Requirement: Health Monitoring

The system MUST expose an endpoint to verify connectivity to the Oracle database.

#### Scenario: Database is available
- GIVEN the Oracle database is running and reachable
- WHEN a client requests the `/health` endpoint
- THEN the system responds with HTTP 200 and indicates a successful `SELECT 1 FROM DUAL` check

#### Scenario: Database is unreachable
- GIVEN the Oracle database is down or credentials are wrong
- WHEN a client requests the `/health` endpoint
- THEN the system responds with an HTTP 50x error indicating database unavailability

### Requirement: Developer Setup

The repository MUST provide local setup commands for the database dependencies and thin-mode driver usage.

#### Scenario: Developer clones repository
- GIVEN a fresh clone
- WHEN the developer reads `README.md`
- THEN they find explicit `python -m pip install -r requirements.txt` and `.env` setup instructions
