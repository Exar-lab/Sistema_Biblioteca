# Delta Spec: expose-missing-api-endpoints

## Capabilities

| Capability | Type | Domains |
|---|---|---|
| `user-api-management` | NEW | Auth registration, User CRUD |
| `catalog-api` | MODIFIED | Book listing with filters |

---

# user-api-management Specification (NEW)

## Purpose

Expose public user registration and administrative user management endpoints.
Define the invariant that password hashes MUST NEVER appear in any API response.

## Requirements

### Requirement: User Registration

The system MUST expose `POST /api/v1/auth/register`.
The endpoint MUST accept a `UserCreate` payload and return `UserRead` on success.
The endpoint MUST NOT require authentication.
The system MUST hash the plain password before persisting; the hash MUST NOT appear in the response.
The system MUST raise `ConflictError` (→ 409) when the username or email already exists.

#### Scenario: Successful registration

- GIVEN no existing user with the submitted username and email
- WHEN `POST /api/v1/auth/register` is called with valid `UserCreate` payload
- THEN the system returns `201 Created` with a `UserRead` body
- AND the response MUST NOT contain `password` or `password_hash` fields

#### Scenario: Duplicate username or email

- GIVEN a user already exists with the submitted username or email
- WHEN `POST /api/v1/auth/register` is called
- THEN the system returns `409 Conflict` with `{"detail": "<message>"}`

#### Scenario: Invalid payload

- GIVEN the request body is missing required fields or violates constraints (e.g., `password` shorter than 8 chars)
- WHEN `POST /api/v1/auth/register` is called
- THEN the system returns `422 Unprocessable Entity`

---

### Requirement: AuthService.register() Shape Fix

`AuthService.register()` MUST pass an object with attribute access (not a plain `dict`) to `UserRepository.create()`.

**Bug**: The current implementation calls `self._user_repository.create(session, raw)` where `raw` is a `dict`. `UserRepository.create()` accesses fields via dot notation (`data.username`, `data.full_name`, etc.), so a plain `dict` raises `AttributeError` at runtime.

**Fixed contract**: The object passed to `create()` MUST expose `.username`, `.full_name`, `.email`, `.phone`, `.password_hash`, `.is_active`, and `.role_id` as attributes. The `password` (plain-text) key MUST NOT be present; `password_hash` MUST be present.

#### Scenario: Registration reaches repository without AttributeError

- GIVEN a valid `UserCreate` payload
- WHEN `AuthService.register()` processes it
- THEN `UserRepository.create()` is called with an object where `data.username` (and all other required attributes) resolves without error
- AND `data.password_hash` holds the bcrypt hash of the original plain password
- AND `data` has no `password` attribute

---

### Requirement: User Listing

The system MUST expose `GET /api/v1/users/` (admin-accessible).
The endpoint MUST return `list[UserRead]`.
The response MUST NOT include `password_hash` in any item.

#### Scenario: List all users

- GIVEN the database contains at least one user
- WHEN `GET /api/v1/users/` is called with a valid auth token
- THEN the system returns `200 OK` with a JSON array of `UserRead` objects

#### Scenario: Empty list

- GIVEN no users exist
- WHEN `GET /api/v1/users/` is called
- THEN the system returns `200 OK` with an empty JSON array `[]`

---

### Requirement: User Lookup by ID

The system MUST expose `GET /api/v1/users/{user_id}`.
The endpoint MUST return `UserRead` when the user exists.
The system MUST raise `NotFoundError` (→ 404) when `user_id` does not match any record.

#### Scenario: User found

- GIVEN a user with `id = N` exists
- WHEN `GET /api/v1/users/N` is called
- THEN the system returns `200 OK` with the matching `UserRead`

#### Scenario: User not found

- GIVEN no user with `id = N` exists
- WHEN `GET /api/v1/users/N` is called
- THEN the system returns `404 Not Found` with `{"detail": "User not found."}`

---

### Requirement: User Update

The system MUST expose `PATCH /api/v1/users/{user_id}`.
The endpoint MUST accept a `UserUpdate` payload (all fields optional).
If `password` is provided it MUST be hashed before passing to the repository; the hash MUST NOT appear in the response.
The system MUST raise `NotFoundError` (→ 404) when `user_id` does not exist.

#### Scenario: Partial update

- GIVEN a user with `id = N` exists
- WHEN `PATCH /api/v1/users/N` is called with `{"full_name": "New Name"}`
- THEN the system returns `200 OK` with updated `UserRead`
- AND all other fields retain their previous values

#### Scenario: Update non-existent user

- GIVEN no user with `id = N` exists
- WHEN `PATCH /api/v1/users/N` is called
- THEN the system returns `404 Not Found`

---

### Requirement: User Active-State Toggle

The system MUST expose `PATCH /api/v1/users/{user_id}/active` accepting `{"is_active": bool}`.
The system MUST raise `NotFoundError` (→ 404) when `user_id` does not exist.

#### Scenario: Deactivate user

- GIVEN a user with `id = N` and `is_active = true`
- WHEN `PATCH /api/v1/users/N/active` is called with `{"is_active": false}`
- THEN the system returns `200 OK` with `UserRead` where `is_active = false`

#### Scenario: Activate user

- GIVEN a user with `id = N` and `is_active = false`
- WHEN `PATCH /api/v1/users/N/active` is called with `{"is_active": true}`
- THEN the system returns `200 OK` with `UserRead` where `is_active = true`

---

### Requirement: Password Never Exposed

The system MUST NOT include `password` (plain-text) or `password_hash` in any `UserRead` response, on any endpoint.

#### Scenario: Registration response has no credentials

- GIVEN a successful `POST /api/v1/auth/register` call
- WHEN the response body is inspected
- THEN the JSON object MUST NOT contain keys `password` or `password_hash`

#### Scenario: User update with password change has no credentials in response

- GIVEN `PATCH /api/v1/users/{id}` is called with a new `password`
- WHEN the response body is inspected
- THEN the JSON object MUST NOT contain keys `password` or `password_hash`

---

# Delta for catalog-api (MODIFIED)

## MODIFIED Requirements

### Requirement: Book Listing with Filters

The system MUST expose `GET /api/v1/books/` accepting optional query parameters `title`, `author`, and `category`.
All three parameters are optional; omitting them returns the full unfiltered book list (existing behavior preserved).
Filtering MUST be case-insensitive substring matching for `title` and `author`.
Filtering by `category` MUST match the category name (case-insensitive substring).
Multiple filters, when provided together, MUST be applied as AND conditions.
The response shape MUST remain `list[BookRead]` unchanged.

(Previously: `GET /api/v1/books/` accepted no query parameters and always returned all books.)

#### Scenario: List all books (unfiltered — existing behavior preserved)

- GIVEN at least one book exists
- WHEN `GET /api/v1/books/` is called with no query parameters
- THEN the system returns `200 OK` with all books as `list[BookRead]`

#### Scenario: Filter by title

- GIVEN books with titles "Clean Code" and "Clean Architecture" exist
- WHEN `GET /api/v1/books/?title=clean` is called
- THEN the system returns both books
- AND books whose titles do not contain "clean" (case-insensitive) are excluded

#### Scenario: Filter by author name

- GIVEN books by "Robert Martin" and "Kent Beck" exist
- WHEN `GET /api/v1/books/?author=martin` is called
- THEN only books with an author whose name contains "martin" (case-insensitive) are returned

#### Scenario: Filter by category

- GIVEN books in category "Programming" and "History" exist
- WHEN `GET /api/v1/books/?category=prog` is called
- THEN only books whose category name contains "prog" (case-insensitive) are returned

#### Scenario: Combined filters narrow results

- GIVEN multiple books exist across authors and categories
- WHEN `GET /api/v1/books/?title=code&category=programming` is called
- THEN only books matching BOTH conditions are returned

#### Scenario: No match returns empty list

- GIVEN no book matches the provided filter
- WHEN `GET /api/v1/books/?title=nonexistentxyz` is called
- THEN the system returns `200 OK` with `[]`

---

## Validation Rules Summary

| Field | Rule |
|---|---|
| `username` | required, 3–50 chars |
| `full_name` | required, 2–120 chars |
| `email` | required, 5–255 chars, must match email pattern |
| `password` (create) | required, 8–128 chars (plain-text, SecretStr) |
| `password` (update) | optional, 8–128 chars when provided |
| `phone` | optional, max 30 chars |
| `is_active` | optional, bool, defaults to `true` |
| `role_id` | optional, integer > 0 |
| `title` filter | optional, string, no length restriction |
| `author` filter | optional, string, no length restriction |
| `category` filter | optional, string, no length restriction |

## Business Rules

1. A `password_hash` MUST NEVER appear in any API response body.
2. Registration MUST fail with 409 if the username or email duplicates an existing record.
3. Deactivating a user MUST NOT delete them; they remain queryable via admin endpoints.
4. Book filter parameters are purely additive; they MUST NOT alter stock, author associations, or any persisted data.
5. Category is the system's genre taxonomy; no separate genre entity is introduced by this change.

## Endpoint Summary

| Method | Path | Auth | Status Codes |
|---|---|---|---|
| POST | /api/v1/auth/register | None | 201, 409, 422 |
| GET | /api/v1/users/ | Required | 200, 401 |
| GET | /api/v1/users/{id} | Required | 200, 401, 404 |
| PATCH | /api/v1/users/{id} | Required | 200, 401, 404, 422 |
| PATCH | /api/v1/users/{id}/active | Required | 200, 401, 404, 422 |
| GET | /api/v1/books/ | None | 200 |
