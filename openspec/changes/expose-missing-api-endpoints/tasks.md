# Tasks: Expose Missing API Endpoints

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 380–500 (additions across 10 files + 2 new files) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → auth bug fix + register endpoint · PR 2 → users CRUD router · PR 3 → book filters |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending (ask user before apply) |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Fix register() bug + expose POST /auth/register | PR 1 | Self-contained; unblocks smoke testing of registration |
| 2 | UserService + /users router + main.py wiring | PR 2 | Depends on PR 1 (UserCreateWithHash must exist) |
| 3 | Book filter query params end-to-end | PR 3 | Independent of PRs 1-2; can run in parallel with PR 2 |

---

## Phase 1: Foundation — Schema & Bug Fix

- [x] 1.1 **`app/schemas/users.py`** — Add `UserCreateWithHash` dataclass after `UserCreate`. Fields: all `UserBase` fields + `password_hash: str`. Must NOT inherit from `UserCreate` and must NOT include a `password` field. Add `UserCreateWithHash` to `__all__`.
  - Acceptance: `UserCreateWithHash(username="x", full_name="y", email="a@b.c", phone=None, is_active=True, role_id=None, password_hash="hash")` instantiates without error; `hasattr(instance, "password")` is `False`.

- [x] 1.2 **`app/schemas/users.py`** — Add `UserActiveToggle` schema with a single field `is_active: bool`. Add to `__all__`.
  - Acceptance: schema validates `{"is_active": false}` and rejects a missing `is_active` field with 422.

- [x] 1.3 **`app/application/services/auth_service.py`** — Fix `register()`: replace the `dict`-based handoff with a `UserCreateWithHash` instance. Import `UserCreateWithHash` from `app.schemas.users`. Build the instance from `data` fields + computed `password_hash`. Pass the instance (not a dict) to `self._user_repository.create()`.
  - Acceptance: calling `register()` with a valid `UserCreate` reaches `user_repository.create()` with an object where `obj.username`, `obj.password_hash` resolve as attributes and `hasattr(obj, "password")` is `False`.

- [x] 1.4 **`app/infrastructure/repositories/user_repository.py`** — Add `get_by_username()` method (present in port Protocol but missing from concrete class). Query: `select(LibraryUser).where(LibraryUser.username == username)`, return `scalar_one_or_none()`.
  - Acceptance: method exists on `UserRepository`; calling with a known username returns the ORM instance; unknown username returns `None`.

- [x] 1.5 **VALIDATE** — Inspect Oracle `BIBLIOTECA.pkg_library_users.p_update` signature to confirm it accepts `p_is_active` as a parameter. Check via `app/infrastructure/repositories/user_repository.py` existing `update()` call (line 48–67): the `p_is_active` bind variable is already present. Confirm this covers the `set_active` use case — no separate proc is needed.
  - RESULT: VALIDATED ✓ — `:p_is_active` is present in the `text()` call at line 60. No change needed.

---

## Phase 2: Core Implementation — Auth Register Endpoint

- [x] 2.1 **`app/application/services/auth_service.py`** — Extend `register()` to check for duplicate username/email before calling the repository. Query `self._user_repository.get_by_username(session, data.username)`; if found, raise `ConflictError("Username already registered.")`.
  - Acceptance: duplicate username → `ConflictError` → 409 via exception handler; unique username → proceeds to `create()`.

- [x] 2.2 **`app/api/v1/routers/auth.py`** — Add `POST /register` endpoint. Import `UserCreate`, `UserRead`. Handler signature: `(payload: UserCreate, db: DbSession, service: AuthServiceDep) -> UserRead`. Status code 201. No auth dependency. Delegate to `service.register(db, payload)`.
  - Acceptance: `POST /api/v1/auth/register` with valid body returns 201 + `UserRead`; response JSON has no `password` or `password_hash` keys.

---

## Phase 3: Core Implementation — Users CRUD

- [x] 3.1 **`app/application/services/user_service.py`** — Create file. Implement `UserService` with constructor `__init__(self, user_repository: UserRepository)`. Methods:
  - `list_users(session) → list[Any]`: delegates to `self._user_repository.list_all(session)`.
  - `get_user(session, user_id: int) → Any`: calls `get_by_id`; raises `NotFoundError("User not found.")` if `None`.
  - `update_user(session, user_id: int, data: UserUpdate) → Any`: fetches user first (raises 404 if missing); builds a merged object or passes `data` to `self._user_repository.update()`; hashes `data.password` if provided (use `hash_password`), sets `password_hash` on the object passed to repo; returns updated user.
  - `set_active(session, user_id: int, is_active: bool) → Any`: fetches user (raises 404 if missing); calls `self._user_repository.update()` with a minimal object that carries existing fields + toggled `is_active` (re-uses `p_update` which already binds `p_is_active`).
  - Acceptance: each method independently testable; `NotFoundError` raised for missing IDs; no `password_hash` in return values (ORM model field is excluded by `UserRead`).

- [x] 3.2 **`app/application/services/user_service.py`** — Add `__all__ = ["UserService"]` and a module-level singleton `user_service = UserService(user_repository)` importing from `app.infrastructure.repositories.user_repository`.

- [x] 3.3 **`app/api/v1/routers/users.py`** — Create file. Router: `APIRouter(prefix="/users", tags=["Users"])`. DI helpers: `get_user_service()` factory returning `UserService(user_repository)`. Annotated aliases for `DbSession` and `UserServiceDep`. Implement these endpoints (all guarded by `AdminOnly` from `app.api.dependencies`):
  - `GET /` → `list_users(db, service)` → `list[UserRead]`, status 200.
  - `GET /{user_id}` → `get_user(db, service, user_id)` → `UserRead`, status 200.
  - `PATCH /{user_id}` → `update_user(db, service, user_id, payload: UserUpdate)` → `UserRead`, status 200.
  - `PATCH /{user_id}/active` → `set_active(db, service, user_id, payload: UserActiveToggle)` → `UserRead`, status 200.
  - Acceptance: all four routes registered; unauthenticated request → 401; non-admin → 403; unknown ID → 404.

- [x] 3.4 **`main.py`** — Import `users_router` from `app.api.v1.routers.users` and call `app.include_router(users_router, prefix="/api/v1")` alongside the existing router registrations.
  - Acceptance: `GET /api/v1/users/` appears in `/docs`; smoke test returns 401 without a token.

---

## Phase 4: Core Implementation — Book Filters

- [ ] 4.1 **`app/application/ports/book_repository.py`** — Widen `list_all` signature in the `BookRepository` Protocol: `def list_all(self, session: Any, *, title: str | None = None, author: str | None = None, category: str | None = None) -> list[Any]`.
  - Acceptance: existing concrete class still satisfies Protocol after this change (Python structural typing — adding keyword-only params with defaults is backward-compatible).

- [ ] 4.2 **`app/infrastructure/repositories/book_repository.py`** — Rewrite `list_all()` to accept optional `title`, `author`, `category` keyword-only params. Build a SQLAlchemy `select(Book)` statement and conditionally chain:
  - `title`: `stmt = stmt.where(func.upper(Book.title).like(f"%{title.upper()}%"))`
  - `author`: `stmt = stmt.join(Book.authors).where(func.upper(Author.first_name + " " + Author.last_name).like(f"%{author.upper()}%"))` — add `.distinct()` to avoid duplicate rows.
  - `category`: `stmt = stmt.join(Book.category).where(func.upper(Category.name).like(f"%{category.upper()}%"))`.
  - Import `func` from `sqlalchemy` and `Author`, `Category` from their domain models.
  - Acceptance: no filter → returns all books (existing behavior); `title="clean"` → only books with "CLEAN" in title; author and category filters work independently and in combination; no duplicate rows when author join is applied.

- [ ] 4.3 **`app/application/services/book_service.py`** — Update `list_books()` to accept and forward `title`, `author`, `category` optional kwargs: `def list_books(self, session: Any, *, title: str | None = None, author: str | None = None, category: str | None = None) -> list[Any]`. Forward all three to `self._repository.list_all(session, title=title, author=author, category=category)`.
  - Acceptance: calling `list_books(session)` with no filters still works; each filter kwarg propagates to the repository.

- [ ] 4.4 **`app/api/v1/routers/books.py`** — Update the `GET /` handler to accept three optional `Query` params: `title: str | None = Query(default=None)`, `author: str | None = Query(default=None)`, `category: str | None = Query(default=None)`. Pass them to `service.list_books(db, title=title, author=author, category=category)`.
  - Acceptance: `GET /api/v1/books/?title=clean` returns filtered results; `GET /api/v1/books/` with no params returns full list; `/docs` shows all three query parameters on the endpoint.

---

## Phase 5: Testing

- [ ] 5.1 **Unit test — `AuthService.register()` fix** — Write a test using a mock `UserRepository`. Call `register()` with a valid `UserCreate`. Assert the object passed to `mock_repo.create()` has `password_hash` as an attribute and does NOT have a `password` attribute. Assert no `AttributeError` is raised.
  - Spec ref: "Registration reaches repository without AttributeError".

- [ ] 5.2 **Unit test — duplicate username** — Mock `get_by_username` to return a user. Assert `register()` raises `ConflictError`.
  - Spec ref: "Duplicate username or email → 409".

- [ ] 5.3 **Unit test — `BookRepository.list_all()` filters** — Write tests with an in-memory SQLite or mock session asserting: no-filter returns all; `title="code"` excludes non-matching books; `author="martin"` triggers the author join; combined filters apply as AND.
  - Spec ref: "Combined filters narrow results", "No match returns empty list".

- [ ] 5.4 **Integration test — `POST /api/v1/auth/register`** — Use FastAPI `TestClient`. POST valid payload → assert 201 + `UserRead` body. Assert body JSON has no `password` or `password_hash` keys. POST duplicate username → assert 409.
  - Spec ref: "Successful registration", "Duplicate username or email".

- [ ] 5.5 **Integration test — `/users` CRUD** — Authenticated admin token. `GET /api/v1/users/` → 200, list. `GET /api/v1/users/{id}` → 200 for existing, 404 for unknown. `PATCH /api/v1/users/{id}` → 200 with updated field. `PATCH /api/v1/users/{id}/active` with `{"is_active": false}` → 200, `is_active` false in response. Unauthenticated → 401. Non-admin token → 403.
  - Spec ref: all `/users` requirement scenarios.

- [ ] 5.6 **Regression test — existing book/auth tests pass unchanged** — Run the full existing test suite. No previously passing test may break. Book `GET /` with no params must still return the full list.
  - Spec ref: "List all books (unfiltered — existing behavior preserved)".

---

## Phase 6: Cleanup

- [ ] 6.1 **`app/schemas/users.py`** — Verify `UserCreateWithHash` and `UserActiveToggle` are in `__all__`; remove any leftover debug imports or `TODO` comments.

- [ ] 6.2 **`app/api/v1/routers/users.py`** — Add `__all__ = ["router", "get_user_service"]` at module end.

- [ ] 6.3 **`app/infrastructure/repositories/book_repository.py`** — Confirm `func` import is present in the SQLAlchemy imports block; confirm `Author` and `Category` models are imported without circular dependencies. If a circular import is detected, import them lazily inside `list_all()`.
