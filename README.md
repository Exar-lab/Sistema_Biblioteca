<div align="center">

# 📚 Library Management System

**A FastAPI + Oracle backend for managing books, users, loans, returns, and administrative reports.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi)
![Oracle](https://img.shields.io/badge/Oracle-Database-F80000?style=for-the-badge&logo=oracle)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=for-the-badge&logo=pytest)

</div>

---

## ✨ Overview

This project is a **Library Management System** built with **FastAPI**, **SQLAlchemy**, and **Oracle**.

The repository is currently in an **API-first stage**: it exposes JWT authentication, catalog management, loans, returns, roles, reports, and a database healthcheck. A server-rendered web interface is planned for a later stage using **Jinja2 + Bootstrap**.

---

## 🧱 Current Stack

| Area | Technology |
| --- | --- |
| API | FastAPI |
| Persistence | SQLAlchemy + Oracle (`oracledb`) |
| Authentication | JWT with `python-jose` and password hashing with `passlib[bcrypt]` |
| Configuration | `pydantic-settings` |
| Testing | `pytest` + `TestClient` |
| Frontend | Static HTML, CSS, and vanilla JavaScript served from `app/static` |

---

## 🚀 Features

<table>
  <tr>
    <td><strong>Authentication</strong></td>
    <td>User registration, login, JWT access tokens, and authenticated profile endpoint.</td>
  </tr>
  <tr>
    <td><strong>Catalog</strong></td>
    <td>CRUD operations for books, authors, categories, and roles.</td>
  </tr>
  <tr>
    <td><strong>Loans</strong></td>
    <td>Loan creation and return handling with stock business rules.</td>
  </tr>
  <tr>
    <td><strong>Reports</strong></td>
    <td>Administrative dashboard endpoints for library metrics.</td>
  </tr>
  <tr>
    <td><strong>Healthcheck</strong></td>
    <td>Application and database status available at <code>/health</code>.</td>
  </tr>
</table>

---

## 📁 Project Structure

```text
.
├── main.py                         # FastAPI entry point and health endpoints
├── app/
│   ├── api/v1/routers/             # HTTP routes by domain
│   ├── application/services/        # Application business logic
│   ├── infrastructure/repositories/ # SQLAlchemy data access
│   ├── schemas/                     # Pydantic request/response models
│   └── core/                        # Settings, database, and security
├── database/
│   └── oracle_schema.sql            # Oracle bootstrap script
└── tests/                           # Unit and integration tests
```

---

## ⚙️ Local Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Create environment variables

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure at least:

| Variable | Required | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Oracle connection string. |
| `SECRET_KEY` | Yes | Secret used to sign JWT tokens. |
| `SQLALCHEMY_ECHO` | No | Enables SQL logging when needed. |
| `ALGORITHM` | No | Defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Defaults to `30`. |

---

## 🗄️ Oracle Bootstrap

The script `database/oracle_schema.sql` creates or updates the `BIBLIOTECA` user, tables, triggers, indexes, sequences, and initial role data.

### Requirements

- Oracle XE with the `XEPDB1` PDB active.
- Execute the script as `SYS` or as a DBA-privileged user.

### Run the script

```powershell
sqlplus / as sysdba @database/oracle_schema.sql
```

The script asks for the `BIBLIOTECA` password and is designed to be idempotent.

### Validate database objects

```sql
SELECT object_name, object_type, status
FROM user_objects
WHERE object_type IN ('TABLE', 'TRIGGER', 'INDEX', 'SEQUENCE')
ORDER BY object_type, object_name;
```

---

## 🧪 Development

### Verify Python syntax

```powershell
python -m compileall app main.py
```

### Run the development server

```powershell
uvicorn main:app --reload
```

### Check application health

```powershell
curl http://127.0.0.1:8000/health
```

Expected response when Oracle is available:

```json
{"status":"ok","database":"up"}
```

If the database is unavailable, the endpoint returns `503`.

---

## 🔐 Authentication and API

| Endpoint | Description |
| --- | --- |
| `POST /api/v1/auth/login` | Returns an `access_token` and the user profile. |
| `GET /api/v1/auth/me` | Returns the authenticated user. |
| `/api/v1/authors` | Author management endpoints. |
| `/api/v1/books` | Book catalog endpoints. |
| `/api/v1/categories` | Category management endpoints. |
| `/api/v1/loans` | Loan management endpoints. |
| `/api/v1/returns` | Return handling endpoints. |
| `/api/v1/reports` | Administrative report endpoints. |
| `/api/v1/roles` | Role endpoints; administrator role required. |

---

## 🎨 Frontend

The web UI is a static multi-page frontend served by FastAPI from `/static`.

Folder layout:

```text
app/
└── static/
    ├── index.html
    ├── css/
    ├── js/
    └── pages/
```

Available views include:

- Login
- Catalog
- Loans
- Returns
- Reports dashboard

---

## ✅ Verification

Run the recommended checks before submitting changes:

```powershell
python -m compileall app main.py
python -m pytest
```

---

## 🧭 Real Next Steps

- Expand test coverage for business flows.
- Smoke-test the static web interface against a running backend.
- Document seed users or initial data if they are added.

---

<div align="center">

Made for a clear, practical, and maintainable library control system.

</div>
