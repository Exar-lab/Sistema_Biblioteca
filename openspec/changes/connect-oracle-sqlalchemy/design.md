# Design: Connect FastAPI App to Oracle with Sync SQLAlchemy

## Technical Approach

Implement a minimal infrastructure layer for Oracle access using sync SQLAlchemy, driven by environment variables and exposed through a request-scoped FastAPI dependency. Keep architecture intentionally simple (`core` + optional API dependency module) to match project constraints and current codebase maturity.

## Architecture Decisions

| Topic | Options | Decision | Rationale |
|---|---|---|---|
| ORM mode | SQLAlchemy async, SQLAlchemy sync | **SQLAlchemy sync** | Matches proposal/spec and team learning curve; avoids async DB complexity now. |
| Oracle driver mode | `oracledb` thin, thick | **Thin mode (default)** | No Oracle Instant Client requirement for initial setup. |
| Settings loading | raw `os.getenv`, `pydantic-settings` | **`pydantic-settings` BaseSettings** | Typed config with `.env` support and validation. |
| DB dependency location | only `app/core/database.py`, plus `app/api/dependencies.py` | **`get_db` in `app/core/database.py`; optional re-export in `app/api/dependencies.py`** | Keeps source of truth in core and gives scalable import path for future endpoints. |
| Health check placement | startup hook, `/health` endpoint | **`/health` endpoint with SQL probe** | Aligns spec scenario requirements and gives runtime observability. |

## Data Flow

1. App start loads `Settings` from env/.env.
2. `database.py` builds Engine + `SessionLocal`.
3. Request needing DB calls `Depends(get_db)`.
4. Session yielded to route/service/repository.
5. On success: commit, then close.
6. On exception: rollback, then close.
7. `/health` runs `SELECT 1 FROM DUAL`; success => 200, DB error => 503.

```text
Env/.env -> Settings -> Engine/SessionLocal -> get_db() -> Route
                                          \-> /health SQL probe
```

## File Changes

| File | Action | Description |
|---|---|---|
| `requirements.txt` | Modify | Add DB/config dependencies with pins. |
| `app/core/config.py` | Create | `Settings` model and cached `get_settings()`. |
| `app/core/database.py` | Create | Engine, `SessionLocal`, `Base`, `get_db`, DB health probe helper. |
| `app/api/dependencies.py` | Create (optional) | Re-export `get_db` for route-level conventions. |
| `main.py` | Modify | Add `/health` endpoint using DB probe. |
| `.env.example` | Create | Non-secret env variable template and comments. |
| `README.md` | Modify | Oracle setup, `.env` usage, smoke-check instructions. |
| `AGENTS.md` | Modify | Add verification commands only if executable config remains valid. |

## Interfaces / Contracts

```python
# app/core/config.py
class Settings(BaseSettings):
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False

# app/core/database.py
engine = create_engine(settings.DATABASE_URL, echo=settings.SQLALCHEMY_ECHO, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

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

def run_db_smoke_check(db: Session) -> None:
    db.execute(text("SELECT 1 FROM DUAL"))
```

### Dependency pins

- `SQLAlchemy==2.0.44`
- `oracledb==3.4.0`
- `pydantic-settings==2.11.0`

## Environment Policy

Required/optional variables:

- `DATABASE_URL` (required), format example: `oracle+oracledb://USER:PASSWORD@HOST:1521/?service_name=FREEPDB1`
- `SQLALCHEMY_ECHO` (optional, default `false`)

`.env.example` MUST include placeholders only (no real usernames/passwords/hosts). `.env` MUST stay gitignored.

## DB Smoke/Health Strategy

- `/health` endpoint obtains a session via `SessionLocal()` or `Depends(get_db)` wrapper and executes `SELECT 1 FROM DUAL` using SQLAlchemy `text()`.
- Success response: `200` + `{"status": "ok", "database": "up"}`.
- Failure response: `503` + `{"status": "error", "database": "down"}`.

## Verification Strategy (local project venv)

1. `python -m pip install -r requirements.txt`
2. `python -m compileall app main.py`
3. `uvicorn main:app --reload`
4. `curl http://127.0.0.1:8000/health`

If a local venv is used:
- Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
- Then run the same commands.

## Migration/Model Scope and Extension Points

- **Out of scope now**: ORM table models, Alembic migrations, Oracle DDL/triggers implementation.
- **No migration required** for this change because only connection infrastructure is introduced.
- **Extension points**:
  - `Base` ready for future model modules.
  - `get_db` ready for repository/service injection.
  - Future `app/db/models/` and migration tooling can attach without breaking API dependency shape.

## Open Questions

- [ ] Keep `/health` as DB-inclusive only, or also expose lightweight `/health/live` without DB?
- [ ] Should first migration tooling be Alembic in the next change, or deferred until initial schema stabilizes?
