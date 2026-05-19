# Proposal: Connect FastAPI App to Oracle with SQLAlchemy

Add Oracle database integration using sync SQLAlchemy to enable the data persistence layer for the Library System, following simple teachable architecture constraints.

## Quick path

1. Configure dependencies (`sqlalchemy`, `oracledb`, `pydantic-settings`).
2. Create environment-driven settings model (`app.core.config`).
3. Set up Engine, `SessionLocal`, and FastAPI `get_db` dependency (`app.core.database`).
4. Document the setup procedure in `README.md` and update `AGENTS.md`.

## Details

| Topic | Decision |
|-------|----------|
| Database Driver | Use `oracledb` in default thin mode. Simplifies installation without needing Oracle Instant Client. |
| ORM Strategy | Use sync SQLAlchemy. Aligns with the team's learning curve and project simplicity constraints. |
| Configuration | Use `pydantic-settings` to inject `DATABASE_URL` via environment variables. Prevents hardcoded credentials. |
| Session Lifecycle | Use a request-scoped `Depends(get_db)` generator to ensure connections are closed safely after each request. |
| Smoke Check | Exclude table models for now. Rely on a minimal health check endpoint (e.g., `SELECT 1 FROM DUAL`) to verify connectivity. |

## Checklist

- [ ] `requirements.txt` updated with `sqlalchemy`, `oracledb`, and `pydantic-settings`.
- [ ] `app/core/config.py` created for env-based settings.
- [ ] `app/core/database.py` created for Engine, SessionLocal, and `get_db` dependency.
- [ ] Minimal smoke check endpoint exposed in `main.py`.
- [ ] `README.md` updated with environment setup instructions for Oracle.
- [ ] `AGENTS.md` updated with execution commands if required.

## Next step

Proceed to `sdd-spec` phase to define the required behaviors and scenarios.