# Tasks: Connect FastAPI App to Oracle with SQLAlchemy

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 160-240 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-always |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Oracle config + session plumbing | PR 1 | Keep to infra only; no domain models/migrations. |
| 2 | FastAPI health wiring + docs | PR 1 | Include smoke verification and safe env docs. |

## Phase 1: Foundation / Infrastructure

- [x] 1.1 Update `requirements.txt` and local venv with `SQLAlchemy`, `oracledb`, and `pydantic-settings`; verify install via `python -m pip install -r requirements.txt`.
- [x] 1.2 Create `app/core/config.py` with `Settings` + cached `get_settings()` reading `DATABASE_URL` and optional `SQLALCHEMY_ECHO` from `.env`.
- [x] 1.3 Create `.env.example` with placeholder Oracle values only; confirm `.env` stays ignored in `.gitignore`.
- [x] 1.4 Create `app/core/database.py` with sync `create_engine`, `SessionLocal`, `Base`, `get_db()`, and a tiny `SELECT 1 FROM DUAL` smoke helper.

## Phase 2: FastAPI Wiring / Smoke Check

- [x] 2.1 Update `main.py` to add `/health` that opens a DB session, runs the smoke check, returns 200 on success, and 503 on DB failure.
- [x] 2.2 Add `app/api/dependencies.py` only if needed as a thin `get_db` re-export for future routes; do not add ORM models or migrations.
- [x] 2.3 Keep the existing root endpoint intact and ensure imports resolve cleanly with the new `app/core` package layout.

## Phase 3: Verification / Documentation

- [x] 3.1 Update `README.md` with venv activation, install command, `.env` setup, and `/health` smoke-check steps.
- [x] 3.2 Update `AGENTS.md` only if the verification path changes; include the health smoke command alongside `python -m compileall app main.py`.
- [x] 3.3 Verify locally with `python -m compileall app main.py`, `uvicorn main:app --reload`, and `curl http://127.0.0.1:8000/health`.
- [x] 3.4 Add formal pytest baseline for `/health` response contracts and `get_db()` lifecycle without requiring a live Oracle instance.
