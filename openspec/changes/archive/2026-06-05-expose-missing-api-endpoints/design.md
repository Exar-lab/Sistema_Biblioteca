# Design: Expose Missing API Endpoints

## Technical Approach
Thin FastAPI routers over the existing service → port → repository hexagon. Routers do DI + HTTP only; services hold rules; repositories own persistence (writes via `pkg_*` procs, reads via ORM SELECT). Fix the registration handoff first, then expose `/auth/register`; add a `/users` router + `UserService`; push optional book filters down to the repository SELECT using Oracle-safe SQL.

## Architecture Decisions

| Concern | Choice | Alternative rejected | Rationale |
|---|---|---|---|
| Layer for filtering logic | Repository builds the SELECT; service forwards filters; router parses query params | Filter in service via Python list comprehension | DB-side filtering scales and matches existing read-via-ORM pattern |
| Case-insensitive match | `UPPER(col) LIKE UPPER(:val)` with `%term%` | `ILIKE` | ILIKE is PostgreSQL-only; this is Oracle |
| User write path | Reuse `UserService` → `user_repository` (pkg procs) | Direct ORM insert in service | Writes MUST go through stored procedures per repo contract |
| Register handoff | Pass an **object** (not dict) with `password_hash` to `create()` | Change repo to accept dict | Repo accesses `data.attr`; all other services pass schema objects — keep the contract consistent |
| Authz on `/users` | `AdminOnly` dependency from `app/api/dependencies.py` | New custom guard | Already exists and is the project convention |

### Decision: register() shape mismatch (the bug)
**Current**: `register()` does `raw = data.model_dump(); raw["password_hash"] = ...; create(session, raw)`. `UserRepository.create()` then calls `data.username`, `data.full_name`, `data.is_active`, `data.role_id` — attribute access on a **dict** → `AttributeError`.
**Fix**: build an object the repo can read by attribute. Construct a `UserCreate.model_copy(update={...})`-style object is wrong (it keeps `password`, not `password_hash`). Instead define an internal `UserCreateWithHash` (a small Pydantic model: `UserBase` fields + `password_hash: str`) and pass an instance. Repo stays untouched.

## Data Flow

    POST /auth/register ─→ AuthService.register ─→ build UserCreateWithHash ─→ user_repository.create (pkg_library_users.p_insert) ─→ UserRead

    GET /books/?title=&author=&category= ─→ BookService.list_books(filters) ─→ book_repository.list_all(filters)
                                                                                        │
                                                              SELECT Book [JOIN book_authors/authors] WHERE UPPER(...) LIKE ...

## File Changes

| File | Action | Description |
|---|---|---|
| `app/application/services/auth_service.py` | Modify | Fix `register()` to pass an object with `password_hash`, not a dict |
| `app/schemas/users.py` | Modify | Add internal `UserCreateWithHash` (UserBase + `password_hash: str`) |
| `app/application/services/user_service.py` | Create | List/get/update/set-active coordinating `user_repository` |
| `app/api/v1/routers/users.py` | Create | `/users` router: list, get, update, activate/deactivate (AdminOnly) |
| `app/api/v1/routers/auth.py` | Modify | Add `POST /register` → `service.register` |
| `app/api/v1/routers/books.py` | Modify | Accept optional `title/author/category` query params |
| `app/application/services/book_service.py` | Modify | `list_books` accepts optional filters, forwards them |
| `app/infrastructure/repositories/book_repository.py` | Modify | `list_all` accepts filters; build WHERE with LIKE + author join |
| `app/application/ports/book_repository.py` | Modify | Widen `list_all` signature with optional filters |
| `main.py` | Modify | `include_router(users_router, prefix="/api/v1")` |

## Interfaces / Contracts

```python
# schemas/users.py
class UserCreateWithHash(UserBase):
    password_hash: str

# ports/book_repository.py
def list_all(self, session, *, title=None, author=None, category=None) -> list[Any]: ...

# book_repository.list_all (Oracle-safe)
stmt = select(Book)
if author:
    stmt = stmt.join(Book.authors)  # selectin already eager-loads authors for output
if title:
    stmt = stmt.where(func.upper(Book.title).like(f"%{title.upper()}%"))
if author:
    stmt = stmt.where(
        func.upper(Author.first_name + " " + Author.last_name).like(f"%{author.upper()}%")
    )
if category:
    stmt = stmt.join(Book.category).where(func.upper(Category.name).like(f"%{category.upper()}%"))
stmt = stmt.distinct()
```

`UserService` mirrors `BookService`: ctor takes the port; methods `list_users`, `get_user` (raise `NotFoundError`), `update_user`, `set_active(session, id, active)` (calls `update` with `is_active` toggled). Router factory `get_user_service()` wraps the `user_repository` singleton, matching the auth/books DI pattern.

## DI & Schema Rules
- Routers obtain services via `get_x_service()` factory + `Annotated[Service, Depends(...)]`; DB via `Annotated[Session, Depends(get_db)]`. No new DI mechanism.
- Responses use `UserRead` / `BookRead` only — never expose `password_hash`. `UserRead` already omits it; keep it that way.
- `/users` mutating routes guarded by `AdminOnly`; book filter is public.
- `category` filter is treated as genre taxonomy (no new model), per proposal.

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | `register()` passes object with `password_hash`; `list_all` builds correct WHERE | Mock repo / inspect compiled SQL |
| Integration | register creates user; `/users` CRUD; filtered `/books` returns subset, no password_hash leak | FastAPI TestClient against test DB/proc |
| Regression | existing book/auth endpoint tests | Run full suite |

## Migration / Rollout
No DB migration — reuses existing tables and `pkg_*` procedures. Rollback: remove users router include, `/register` route, filter params, and revert service/repo changes.

## Sequencing
1. Add `UserCreateWithHash` + fix `AuthService.register()` (bug first).
2. Add `POST /auth/register`.
3. Add `UserService` + `/users` router + `main.py` include.
4. Widen book port → repo `list_all` filters → service → router query params.

## Open Questions
- [ ] Confirm `pkg_library_users.p_update` is the path for activate/deactivate (no dedicated proc seen) — design assumes full update with toggled `is_active`.
