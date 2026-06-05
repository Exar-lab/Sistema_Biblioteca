# Proposal: Expose Missing API Endpoints

## Intent

Expose the remaining API endpoints required by the library system scope and fix the registration service handoff before making registration public.

## Scope

### In Scope
- Add `POST /api/v1/auth/register` backed by a safe registration flow.
- Fix `AuthService.register()` so it passes data in the shape expected by `UserRepository.create()`.
- Add a `/api/v1/users` router for user listing, lookup, update, and active-state management.
- Add `title`, `author`, and `category` filters to `GET /api/v1/books/`.
- Treat categories as the project's genre taxonomy unless a separate genre model is later required.

### Out of Scope
- Password reset, logout, refresh tokens, or session revocation.
- UI/templates for these endpoints.
- Replacing categories with a separate genre entity.

## Capabilities

### New Capabilities
- `user-api-management`: Public registration and administrative user API endpoints, including inactive-account handling.

### Modified Capabilities
- `catalog-api`: Book listing gains query-parameter filtering by title, author, and category.

## Approach

Use thin FastAPI routers over the existing service/repository structure. Keep business rules in services, not routers. Fix registration before exposing it. Add a user service if needed to keep `/users` behavior consistent with the current application layer. Extend the book repository/service list path to accept optional filters while preserving the current response shape.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/api/v1/routers/auth.py` | Modified | Add registration endpoint. |
| `app/application/services/auth_service.py` | Modified | Fix registration handoff to repository. |
| `app/api/v1/routers/users.py` | New | Expose user management endpoints. |
| `app/application/services/user_service.py` | New | Coordinate user management behavior. |
| `app/api/v1/routers/books.py` | Modified | Accept catalog filter query params. |
| `app/application/services/book_service.py` | Modified | Pass filters to repository. |
| `app/infrastructure/repositories/book_repository.py` | Modified | Apply title/author/category filters. |
| `main.py` | Modified | Include users router. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Registration fails due to schema/repository mismatch | High | Fix service handoff before adding endpoint tests. |
| Author filtering breaks book response loading | Medium | Use explicit joins/eager loading and preserve existing schema output. |
| User endpoints expose unsafe fields | Medium | Return read schemas only; never expose password hashes. |

## Rollback Plan

Remove the new users router include, registration route, filter parameters, and related service/repository changes. Existing CRUD routers remain unaffected.

## Dependencies

- Existing user, auth, book, category, and author repositories/schemas.

## Success Criteria

- [ ] Registration endpoint creates users without runtime shape errors.
- [ ] Users router exposes list/read/update/active-state operations.
- [ ] Book listing filters by title, author, and category.
- [ ] Existing endpoint tests continue to pass.
