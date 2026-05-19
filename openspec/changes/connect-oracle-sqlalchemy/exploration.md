## Exploration: Connect FastAPI app to Oracle using SQLAlchemy

### Current State
At the start of this change, the project exposed a minimal FastAPI app in `main.py` with no database integration, no settings module, and no SQLAlchemy usage. `requirements.txt` contained only `fastapi`, `pydantic`, and `uvicorn[standard]`. The OpenSpec init context (`openspec/config.yaml`) already defined Oracle as the target database and emphasized simple, teachable architecture.

### Affected Areas
- `requirements.txt` — must include SQLAlchemy and Oracle driver dependencies for reproducible installs.
- `main.py` — will eventually consume DB wiring (directly or via imported dependency module) to validate startup/usage.
- `AGENTS.md` — should be updated in apply phase with exact dependency setup and verification commands.
- `README.md` — should document environment variables and local Oracle connection setup for contributors.
- `openspec/config.yaml` — confirms constraints (Oracle-first artifacts, simple architecture, no strict TDD yet).
- `venv/` (environment only, not committed) — confirms Python 3.13 virtual environment exists and is the install target.

### Approaches
1. **Sync SQLAlchemy + python-oracledb (thin mode default)** — Use `create_engine()` + `SessionLocal` and FastAPI dependency-injected per-request sessions.
   - Pros: Simplest integration path for current minimal app; broad SQLAlchemy examples; easier for team learning in 3-week scope.
   - Cons: Blocking DB calls in request thread; async endpoints still rely on threadpool behavior if DB access is sync.
   - Effort: Low

2. **Async SQLAlchemy + python-oracledb async dialect** — Use `create_async_engine()` and `AsyncSession` with async dependencies.
   - Pros: Better long-term concurrency story; aligns with FastAPI async style.
   - Cons: More moving parts for first DB milestone; Oracle async support/dialect nuances can add onboarding friction.
   - Effort: Medium

### Recommendation
Start with **Approach 1 (sync SQLAlchemy + `oracledb`)** for the first integration milestone, then evolve to async only if profiling or throughput needs justify complexity. This matches project constraints (simple and teachable architecture, short delivery window) while still using modern Oracle driver tooling. Use env-driven settings (`DATABASE_URL` and optional pool/session knobs) from day one to avoid hardcoded credentials.

### Risks
- Oracle connection URL formatting errors (service name vs SID) can block startup despite correct code.
- Driver mode confusion (thin vs thick/Instant Client) may break local setups if documentation is unclear.
- Missing dependency pinning can create non-reproducible installs across teammates.
- Session lifecycle mistakes (not closing/rollback) can leak connections under load.

### Ready for Proposal
Yes — propose a change that introduces dependency updates, env-based DB configuration, SQLAlchemy engine/session scaffolding, and setup documentation without yet implementing domain models.
