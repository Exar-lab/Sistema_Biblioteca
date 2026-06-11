<div align="center">

# Library Management System

FastAPI + Oracle application for managing a library catalog, users, loans, returns, and administrative reports.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi)
![Oracle](https://img.shields.io/badge/Oracle-Database-F80000?style=for-the-badge&logo=oracle)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=for-the-badge&logo=pytest)

</div>

---

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload
```

Then open:

- Web UI: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/health`

> Configure `.env` before running the app against Oracle.

---

## Current scope

The system currently includes an API-first backend, a static multi-page frontend served by FastAPI, Oracle schema scripts, demo data seeding, and automated tests.

| Area | Available functionality |
| --- | --- |
| Authentication | Registration, login, JWT access tokens, authenticated profile, password change |
| Users and roles | Admin/Usuario roles, user listing, profile updates, active-account management |
| Catalog | CRUD for books, authors, categories, and book filtering/search support |
| Loans | Loan creation, user loan history, return and cancellation flows |
| Returns | Return records and return update endpoints |
| Reports | Dashboard metrics through `/api/v1/reports/dashboard` |
| Frontend | Static pages for login, catalog, books, authors, categories, users, loans, returns, and reports |
| Database | Oracle schema bootstrap with tables, sequences, indexes, triggers, and initial role data |

---

## Stack

| Area | Technology |
| --- | --- |
| Backend | FastAPI |
| Database access | SQLAlchemy + `oracledb` |
| Database | Oracle XE / Oracle PDB |
| Schemas | Pydantic v2 |
| Configuration | `pydantic-settings` + `.env` |
| Authentication | `python-jose` JWT + `passlib[bcrypt]` |
| Frontend | Static HTML, CSS, and vanilla JavaScript in `app/static` |
| Testing | pytest + FastAPI `TestClient` |

---

## Project structure

```text
.
├── main.py                         # FastAPI app, routers, static frontend, health endpoint
├── app/
│   ├── api/v1/routers/             # HTTP endpoints by domain
│   ├── application/services/        # Business rules and use cases
│   ├── core/                        # Settings, database session, security helpers
│   ├── infrastructure/repositories/ # SQLAlchemy data access
│   ├── schemas/                     # Pydantic request/response models
│   └── static/                      # Static frontend assets and pages
├── database/
│   └── oracle_schema.sql            # Oracle bootstrap script
├── docs/                            # User and technical manuals
├── scripts/
│   └── seed_demo_data.py            # Deterministic demo data loader
└── tests/                           # Slice and unit tests
```

---

## Environment variables

Create `.env` from `.env.example` and configure these values:

| Variable | Required | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Oracle SQLAlchemy connection string. |
| `SECRET_KEY` | Yes | Secret used to sign JWT tokens. Keep it private. |
| `SQLALCHEMY_ECHO` | No | Enables SQL logging when set to `true`. |
| `ALGORITHM` | No | Defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Defaults to `30`. |

Never commit a real `.env` file or production secrets.

---

## Oracle bootstrap

`database/oracle_schema.sql` creates or updates the `BIBLIOTECA` user, schema objects, triggers, indexes, sequences, and initial roles.

Requirements:

- Oracle XE with the `XEPDB1` PDB active.
- `sqlplus` available in the terminal.
- SYS or DBA-privileged access to execute the bootstrap script.

Run:

```powershell
sqlplus / as sysdba @database/oracle_schema.sql
```

The script asks for the `BIBLIOTECA` password and is designed to be rerunnable.

---

## Demo data

After the Oracle schema is ready, seed deterministic demo records:

```powershell
python scripts/seed_demo_data.py
```

Demo credentials:

| Username | Password | Role |
| --- | --- | --- |
| `demo.admin` | `DemoAdmin123!` | Admin |
| `demo.alice` | `DemoUser123!` | Usuario |
| `demo.ben` | `DemoUser123!` | Usuario |
| `demo.clara` | `DemoUser123!` | Usuario |
| `demo.dan` | `DemoUser123!` | Usuario |
| `demo.valeria` | `DemoUser123!` | Usuario |

---

## API reference

Interactive OpenAPI documentation is available at `/docs` when the app is running.

| Route group | Purpose |
| --- | --- |
| `/api/v1/auth` | Login, registration, current user, password change |
| `/api/v1/users` | User listing, lookup, updates, active status |
| `/api/v1/roles` | Role management |
| `/api/v1/authors` | Author management |
| `/api/v1/books` | Book catalog management |
| `/api/v1/categories` | Category management |
| `/api/v1/loans` | Loans, user history, returns, cancellations |
| `/api/v1/returns` | Return records |
| `/api/v1/reports` | Administrative dashboard metrics |

---

## Frontend pages

The frontend is served from `/static`, with `/` redirecting to `/static/index.html`.

Key pages:

- `/static/index.html`
- `/static/pages/admin-dashboard.html`
- `/static/pages/catalogo.html`
- `/static/pages/libros.html`
- `/static/pages/autores.html`
- `/static/pages/categorias.html`
- `/static/pages/usuarios.html`
- `/static/pages/prestamos.html`
- `/static/pages/mis-prestamos.html`
- `/static/pages/reportes.html`

---

## Development commands

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the app:

```powershell
uvicorn main:app --reload
```

Verify Python syntax:

```powershell
python -m compileall app main.py scripts
```

Run tests:

```powershell
python -m pytest
```

Check health:

```powershell
curl http://127.0.0.1:8000/health
```

Expected response when Oracle is reachable:

```json
{"status":"ok","database":"up"}
```

If Oracle is unavailable, the health endpoint returns `503`.

---

## Documentation

- `docs/manual-tecnico.md` — Spanish technical manual.
- `docs/technical-manual.md` — English technical manual.
- `docs/Manual_de_Usuario.html` / `docs/Manual_de_Usuario.pdf` — user manual artifacts.

---

## Next steps

- Expand test coverage for the most important business flows.
- Smoke-test the static frontend against a running Oracle-backed backend.
- Keep Oracle-specific setup and trigger behavior documented as the schema evolves.
