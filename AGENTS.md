# AGENTS.md

## Project status
- The project now has a minimal FastAPI app, Pydantic schemas, and a Python dependency manifest.
- No CI or formal test config exists yet. Add test commands here only after the corresponding executable config exists.

## Commands
- Setup dependencies: `python -m pip install -r requirements.txt`
- Run development server: `uvicorn main:app --reload`
- Verify Python syntax: `python -m compileall app main.py`

## Intended stack
- Backend: FastAPI.
- Database: Oracle.
- Frontend recommendation for this project: server-rendered Jinja2 templates with Bootstrap, plus small vanilla JS where needed.
- Avoid adding React unless the team explicitly chooses the extra complexity; the project target is a 3-week build with an even-skill team.

## Product scope
- Sistema de Control de Biblioteca.
- Users/security: registration, login with hashed passwords, Admin and Usuario roles, secure cookie or JWT sessions, inactive-account handling.
- Catalog: CRUD for books, authors, categories/genres; books and authors are many-to-many; search/filter by title, author, and category.
- Loans: create loans, record returns, enforce due-date blocking for users with overdue loans, keep per-user loan history.
- Oracle should handle stock update on return via trigger if the database model supports it.
- Reports/dashboard: most-borrowed books, loans by month, users with most loans, low-stock books, totals for books, active loans, pending returns.

## Development guidance
- Keep the architecture simple and teachable: FastAPI routes/services/templates are preferable to a complex framework split until real duplication appears.
- Model the loan and stock rules before coding UI; stock consistency and overdue-loan blocking are core business rules.
- Treat Oracle-specific SQL, triggers, and migrations as first-class project artifacts; document any manual DB setup needed.
- When adding dependencies, commit the manifest/lockfile and update this file with the exact setup and verification commands.
