# Design: Hexagonal Repository Layer (`hexagonal-repositories`)

## 1. Executive Summary

Build a ports-and-adapters stack for 8 entities. ORM models in `app/domain/models/`, `typing.Protocol` outbound ports in `app/application/ports/`, sync SQLAlchemy adapters in `app/infrastructure/repositories/`, thin services in `app/application/services/`, FastAPI routers in `app/api/v1/routers/`, and a single composition root `app/composition.py`. Oracle behaviors (CHAR(1) Y/N, trigger -20001, server-side status flips on returns) are isolated in adapters via a `BoolChar` TypeDecorator, error translation, and explicit `session.expire(loan)` after returns insert.

## 2. Module Layout

```
app/
  domain/
    models/
      __init__.py            # exports + Base re-export
      types.py               # BoolChar TypeDecorator
      role.py                # Role
      user.py                # LibraryUser
      category.py            # Category
      author.py              # Author
      book.py                # Book + book_authors Table
      loan.py                # Loan
      return_.py             # Return (module name suffixed to avoid keyword)
  application/
    errors.py                # OutOfStockError, NotFoundError, ConflictError
    ports/
      __init__.py
      base.py                # Repository[T] Protocol (generic CRUD)
      roles.py               # RoleRepository(Protocol)
      users.py               # LibraryUserRepository(Protocol)
      categories.py
      authors.py
      books.py               # BookRepository (with author wiring)
      loans.py               # LoanRepository
      returns.py             # ReturnRepository
    services/
      __init__.py
      roles.py               # RoleService
      users.py
      categories.py
      authors.py
      books.py
      loans.py               # LoanService (translates OutOfStockError)
      returns.py             # ReturnService (does session.expire on loan)
  infrastructure/
    repositories/
      __init__.py
      base.py                # SqlRepositoryBase[M] generic CRUD
      roles.py               # RoleRepositorySql
      users.py
      categories.py
      authors.py
      books.py               # BookRepositorySql (selectinload authors)
      loans.py               # LoanRepositorySql (Oracle -20001 -> OutOfStockError)
      returns.py             # ReturnRepositorySql (session.expire(loan))
  api/
    dependencies.py          # get_db re-export + service factories
    v1/
      router.py              # APIRouter aggregator (prefix /api/v1)
      routers/
        roles.py
        users.py
        categories.py
        authors.py
        books.py
        loans.py
        returns.py
  composition.py             # service factory functions used by Depends()
  main.py                    # registers app.api.v1.router
```

## 3. Architecture Decisions (ADRs)

### ADR-1: `typing.Protocol` outbound ports (structural subtyping)
- **Decision**: Ports declared as `class XRepository(Protocol)` with `@runtime_checkable` only where needed for tests.
- **Why**: Adapters don't need explicit inheritance. Tests build in-memory fakes without registering anything. Zero ABC ceremony.
- **Rejected**: `abc.ABC` + `ABCMeta` — couples test fakes to base class; not Pythonic; collides poorly with SQLAlchemy models if accidentally mixed.

### ADR-2: `BoolChar` TypeDecorator over `Enum` or string columns
- **Decision**: `BoolChar` extends `TypeDecorator` with `impl = CHAR(1)`, `cache_ok = True`. `process_bind_param` maps `True -> 'Y'`, `False -> 'N'`. `process_result_value` maps `'Y' -> True`, anything else -> `False`. Treats `None` as `False` only on result; raises on `None` bind for NOT NULL columns? No — pass through to let SQLAlchemy default fire.
- **Why**: Schema is fixed (Oracle CHECK constraint `IN ('Y','N')`). Domain wants `bool`. TypeDecorator localizes the coercion. Filters work because `True == 'Y'` is handled by `process_bind_param` automatically when SQLAlchemy compiles `Column == True`.
- **Rejected**: Mapping at service layer — leaks Oracle artifact into ports; every filter would need translation.
- **Lives in**: `app/domain/models/types.py` (re-exported from `app/domain/models/__init__.py`).

### ADR-3: Schema-qualified tables via `__table_args__`
- **Decision**: Every mapped class sets `__table_args__ = {"schema": "BIBLIOTECA"}`. Constants module not used — string is short and explicit.
- **Why**: Oracle user `BIBLIOTECA` owns tables; engine connects as the same user, so unqualified works, but qualifying makes cross-user reads safe and explicit. `book_authors` Table uses the same schema kw.

### ADR-4: Sync SQLAlchemy `Session` end-to-end
- **Decision**: Keep `Session`/`sessionmaker`; ports/services/repositories are all sync. Routers are `def`, not `async def`.
- **Why**: `oracledb` thin-mode async is immature; mixing sync+async sessions risks event-loop blocking. Existing engine is sync. Proposal explicitly scopes async migration OUT.
- **Tradeoff**: Worker concurrency comes from threadpool only. Acceptable for academic project.

### ADR-5: Generic CRUD via `SqlRepositoryBase[M]`
- **Decision**: Adapter base provides `get`, `list`, `create`, `update`, `delete`. Entity adapters extend with domain queries (e.g. `BookRepositorySql.list_with_authors`).
- **Why**: Removes ~70% boilerplate across 8 entities. Generic typed on the ORM model.
- **Note**: The PORT protocols are NOT generic at the public surface — each entity has its own port to keep service signatures explicit and OpenAPI-friendly. Generic lives only in the adapter base.

### ADR-6: Oracle -20001 trapped in `LoanRepositorySql.create()` only
- **Decision**: `create()` wraps `db.flush()` in `try/except DatabaseError as e`. Inspect `e.orig.args[0].code == 20001` (oracledb error code). On match, `raise OutOfStockError(book_id) from e`. Otherwise re-raise.
- **Why**: One place owns trigger translation; service catches `OutOfStockError` and never sees raw `DatabaseError`. Router maps to HTTP 409.
- **Rejected**: Global SQLAlchemy event handler — too magic; harder to test; obscures origin.

### ADR-7: `session.expire(loan)` after `ReturnRepositorySql.create()`
- **Decision**: After flushing the new return row, the adapter calls `db.expire(loan_instance, ["status", "return_date"])` if a loan instance was loaded in this session. ReturnService is responsible: it loads the loan first (or accepts loan id), creates the return, then expires the loaded loan.
- **Why**: Oracle trigger `trg_returns_restore_stock` updates `loans.status='RETURNED'` and `return_date` server-side. SQLAlchemy's identity map still holds the pre-trigger snapshot. Without explicit expire, the very next `GET /loans/{id}` in the same session returns stale `status='ACTIVE'`.
- **Open risk closure**: This satisfies the open risk listed in the proposal.

### ADR-8: `selectinload(Book.authors)` for N+1 elimination
- **Decision**: `BookRepositorySql.get()` and `.list()` apply `.options(selectinload(Book.authors))`. Authors relationship configured with `lazy="select"` (default), overridden per-query.
- **Why**: Defaulting `lazy="selectin"` on the relationship would cost on every Book read, including loan/return flows that don't need authors. Query-level option is surgical.

### ADR-9: Composition root in `app/composition.py`
- **Decision**: Factory functions per service, e.g. `def get_loan_service(db: Session = Depends(get_db)) -> LoanService`. Routers depend on these directly via `Depends(get_loan_service)`. No global container, no DI framework.
- **Why**: FastAPI `Depends` IS the container. Service factories instantiate the SQL repo with the session and inject it. Centralized in one file for audit.

### ADR-10: Domain exceptions, mapped to HTTP at router boundary
- **Decision**: `app/application/errors.py` defines `NotFoundError`, `ConflictError`, `OutOfStockError` (subclass of `ConflictError`). Routers catch these locally with `try/except` blocks or rely on a single `app/api/exception_handlers.py` registered in `main.py` via `app.add_exception_handler`.
- **Choice**: Use `app.add_exception_handler` — cleaner routers, single mapping table.
  - `NotFoundError -> 404`
  - `OutOfStockError -> 409` with `{"detail": "Book has no available stock", "code": "OUT_OF_STOCK"}`
  - `ConflictError -> 409`
- **Why**: Routers stay declarative. Domain errors never leak `DatabaseError` upward.

## 4. Component Contracts

### 4.1 Domain models — column signatures

```python
# app/domain/models/types.py
class BoolChar(TypeDecorator):
    impl = CHAR(1)
    cache_ok = True
    def process_bind_param(self, value, dialect): ...
    def process_result_value(self, value, dialect): ...
```

```python
# app/domain/models/role.py
class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "BIBLIOTECA"}
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.systimestamp())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.systimestamp())
```

```python
# app/domain/models/user.py
class LibraryUser(Base):
    __tablename__ = "library_users"
    __table_args__ = {"schema": "BIBLIOTECA"}
    id, username, full_name, email, phone, password_hash
    is_active: Mapped[bool] = mapped_column(BoolChar, server_default=text("'Y'"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("BIBLIOTECA.roles.id"), nullable=False)
    role: Mapped["Role"] = relationship(lazy="select")
    created_at, updated_at
```

```python
# app/domain/models/book.py
book_authors = Table(
    "book_authors", Base.metadata,
    Column("book_id", ForeignKey("BIBLIOTECA.books.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", ForeignKey("BIBLIOTECA.authors.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, server_default=func.systimestamp(), nullable=False),
    schema="BIBLIOTECA",
)

class Book(Base):
    __tablename__ = "books"
    __table_args__ = {"schema": "BIBLIOTECA"}
    id, title, isbn, description, publication_date, publisher, edition, pages
    stock_total: Mapped[int]
    stock_available: Mapped[int]
    is_active: Mapped[bool] = mapped_column(BoolChar, ...)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("BIBLIOTECA.categories.id"))
    category: Mapped["Category | None"] = relationship(lazy="select")
    authors: Mapped[list["Author"]] = relationship(secondary=book_authors, lazy="select")
```

Other entities (`Category`, `Author`, `Loan`, `Return`) follow the same column shape as the DB schema; `BoolChar` is used wherever the DB has CHAR(1) Y/N.

### 4.2 Port protocols — exact signatures

```python
# app/application/ports/base.py
M = TypeVar("M")

class Repository(Protocol[M]):
    def get(self, id: int) -> M | None: ...
    def list(self, *, limit: int = 100, offset: int = 0) -> list[M]: ...
    def create(self, data: dict[str, Any]) -> M: ...
    def update(self, id: int, data: dict[str, Any]) -> M | None: ...
    def delete(self, id: int) -> bool: ...
```

Per-entity ports extend conceptually but are declared standalone to keep MyPy happy with structural subtyping:

```python
# app/application/ports/books.py
class BookRepository(Protocol):
    def get(self, id: int) -> Book | None: ...
    def get_with_authors(self, id: int) -> Book | None: ...
    def list(self, *, limit: int = 100, offset: int = 0) -> list[Book]: ...
    def create(self, data: dict[str, Any]) -> Book: ...
    def update(self, id: int, data: dict[str, Any]) -> Book | None: ...
    def delete(self, id: int) -> bool: ...
    def set_authors(self, book_id: int, author_ids: list[int]) -> Book: ...

# app/application/ports/loans.py
class LoanRepository(Protocol):
    def get(self, id: int) -> Loan | None: ...
    def list_by_user(self, user_id: int, *, status: str | None = None) -> list[Loan]: ...
    def list(self, *, limit: int = 100, offset: int = 0) -> list[Loan]: ...
    def create(self, data: dict[str, Any]) -> Loan:
        """May raise OutOfStockError when Oracle trigger -20001 fires."""
    def update(self, id: int, data: dict[str, Any]) -> Loan | None: ...

# app/application/ports/returns.py
class ReturnRepository(Protocol):
    def get(self, id: int) -> Return | None: ...
    def get_by_loan(self, loan_id: int) -> Return | None: ...
    def list(self, *, limit: int = 100, offset: int = 0) -> list[Return]: ...
    def create(self, data: dict[str, Any], loan_instance: Loan | None = None) -> Return:
        """Creates the return row; expires loan_instance status/return_date after flush."""
```

Roles, users, categories, authors get vanilla CRUD ports mirroring `Repository[T]` shape.

### 4.3 Adapter base

```python
# app/infrastructure/repositories/base.py
class SqlRepositoryBase(Generic[M]):
    model: type[M]
    def __init__(self, db: Session) -> None:
        self.db = db
    def get(self, id: int) -> M | None:
        return self.db.get(self.model, id)
    def list(self, *, limit=100, offset=0) -> list[M]:
        return list(self.db.scalars(select(self.model).offset(offset).limit(limit)))
    def create(self, data: dict) -> M:
        obj = self.model(**data); self.db.add(obj); self.db.flush(); self.db.refresh(obj); return obj
    def update(self, id: int, data: dict) -> M | None:
        obj = self.get(id)
        if obj is None: return None
        for k, v in data.items(): setattr(obj, k, v)
        self.db.flush(); self.db.refresh(obj); return obj
    def delete(self, id: int) -> bool:
        obj = self.get(id)
        if obj is None: return False
        self.db.delete(obj); self.db.flush(); return True
```

### 4.4 LoanRepositorySql.create — error translation pattern

```python
# app/infrastructure/repositories/loans.py
class LoanRepositorySql(SqlRepositoryBase[Loan]):
    model = Loan
    _ORA_OUT_OF_STOCK = 20001

    def create(self, data: dict) -> Loan:
        try:
            return super().create(data)
        except DBAPIError as e:
            code = getattr(getattr(e.orig, "args", [None])[0], "code", None)
            if code == self._ORA_OUT_OF_STOCK:
                raise OutOfStockError(book_id=data.get("book_id")) from e
            raise
```

Note: `e.orig` for `oracledb` exposes a `_Error` with `.code`. Verified pattern documented in `database/oracle_schema.sql` lines 212-238 (the trigger).

### 4.5 ReturnRepositorySql.create — expire pattern

```python
# app/infrastructure/repositories/returns.py
class ReturnRepositorySql(SqlRepositoryBase[Return]):
    model = Return
    def create(self, data: dict, loan_instance: Loan | None = None) -> Return:
        ret = super().create(data)  # trigger fires here
        if loan_instance is not None:
            self.db.expire(loan_instance, ["status", "return_date"])
        return ret
```

### 4.6 BookRepositorySql.get_with_authors

```python
def get_with_authors(self, id: int) -> Book | None:
    stmt = select(Book).where(Book.id == id).options(selectinload(Book.authors))
    return self.db.scalars(stmt).first()
```

### 4.7 Services — orchestration shape

```python
# app/application/services/loans.py
class LoanService:
    def __init__(self, loans: LoanRepository, books: BookRepository, users: LibraryUserRepository) -> None:
        self._loans, self._books, self._users = loans, books, users

    def create(self, payload: LoanCreate) -> Loan:
        if self._users.get(payload.user_id) is None: raise NotFoundError("user", payload.user_id)
        if self._books.get(payload.book_id) is None: raise NotFoundError("book", payload.book_id)
        return self._loans.create(payload.model_dump())  # may raise OutOfStockError

    def get(self, id: int) -> Loan:
        loan = self._loans.get(id)
        if loan is None: raise NotFoundError("loan", id)
        return loan
```

```python
# app/application/services/returns.py
class ReturnService:
    def __init__(self, returns: ReturnRepository, loans: LoanRepository) -> None: ...

    def create(self, payload: ReturnCreate) -> Return:
        loan = self._loans.get(payload.loan_id)
        if loan is None: raise NotFoundError("loan", payload.loan_id)
        if loan.status == "RETURNED": raise ConflictError("loan already returned")
        existing = self._returns.get_by_loan(payload.loan_id)
        if existing is not None: raise ConflictError("return already exists for loan")
        return self._returns.create(payload.model_dump(), loan_instance=loan)
```

### 4.8 Composition root

```python
# app/composition.py
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    return RoleService(RoleRepositorySql(db))

def get_user_service(db: Session = Depends(get_db)) -> LibraryUserService:
    return LibraryUserService(LibraryUserRepositorySql(db), RoleRepositorySql(db))

def get_book_service(db: Session = Depends(get_db)) -> BookService:
    return BookService(BookRepositorySql(db), AuthorRepositorySql(db), CategoryRepositorySql(db))

def get_loan_service(db: Session = Depends(get_db)) -> LoanService:
    return LoanService(LoanRepositorySql(db), BookRepositorySql(db), LibraryUserRepositorySql(db))

def get_return_service(db: Session = Depends(get_db)) -> ReturnService:
    return ReturnService(ReturnRepositorySql(db), LoanRepositorySql(db))
```

### 4.9 Routers

```python
# app/api/v1/routers/loans.py
router = APIRouter(prefix="/loans", tags=["loans"])

@router.post("", response_model=LoanRead, status_code=201)
def create_loan(payload: LoanCreate, svc: LoanService = Depends(get_loan_service)) -> Loan:
    return svc.create(payload)

@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, svc: LoanService = Depends(get_loan_service)) -> Loan:
    return svc.get(loan_id)
```

```python
# app/api/v1/router.py
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(roles.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(authors.router)
api_router.include_router(books.router)
api_router.include_router(loans.router)
api_router.include_router(returns.router)
```

### 4.10 Exception handlers — main.py registration

```python
# app/api/exception_handlers.py
def register(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, lambda r, e: JSONResponse(404, {"detail": str(e)}))
    app.add_exception_handler(OutOfStockError, lambda r, e: JSONResponse(409, {"detail": str(e), "code": "OUT_OF_STOCK"}))
    app.add_exception_handler(ConflictError, lambda r, e: JSONResponse(409, {"detail": str(e)}))
```

## 5. Data Flow

### 5.1 Create loan (happy + out-of-stock)
```
POST /api/v1/loans  -> create_loan(router)
  -> LoanService.create(payload)
     -> LibraryUserRepository.get(user_id)
     -> BookRepository.get(book_id)
     -> LoanRepository.create(data)
        -> SQLAlchemy INSERT loans -> Oracle BEFORE INSERT trigger
           - stock_available > 0: UPDATE books.stock_available - 1
           - stock_available == 0: RAISE -20001
        -> on DBAPIError code 20001: raise OutOfStockError
  -> exception handler -> HTTP 409 {"detail": "...", "code": "OUT_OF_STOCK"}
  -> success -> HTTP 201 LoanRead
```

### 5.2 Create return (status flip + identity-map consistency)
```
POST /api/v1/returns -> create_return(router)
  -> ReturnService.create(payload)
     -> LoanRepository.get(loan_id)         # loan_instance in identity map, status='ACTIVE'
     -> conflict checks
     -> ReturnRepository.create(data, loan_instance=loan)
        -> INSERT returns -> Oracle AFTER INSERT trigger
           - UPDATE loans.status='RETURNED', return_date=...
           - UPDATE books.stock_available + 1
        -> db.expire(loan_instance, ["status","return_date"])  # next read reloads
  -> HTTP 201 ReturnRead
```

### 5.3 Read book with authors (no N+1)
```
GET /api/v1/books/{id} -> BookService.get_with_authors
  -> BookRepository.get_with_authors(id)
     -> SELECT books WHERE id=... + selectinload Book.authors
        => 2 queries total (books + IN (author_ids))
```

## 6. Integration Points

- `app/core/database.Base` — all ORM models extend it; `Base.metadata` shared.
- `app/core/database.get_db` — sole session source; re-exported by `app/api/dependencies.py` for back-compat.
- `app/main.py` — adds `app.include_router(api_router)` and `register_exception_handlers(app)`.
- `app/schemas/**` — `model_config = ConfigDict(from_attributes=True)` required on read schemas so routers can return ORM instances. Drop-field changes from proposal happen in the same change set.

## 7. Testing Strategy (design-level only)

- **Unit (services)**: in-memory fakes implementing the Protocol (just classes with the same method names). No ABC registration needed thanks to structural subtyping. Cover happy path + `NotFoundError` + `OutOfStockError`.
- **Adapter integration**: gated by `RUN_DB_TESTS`. Roundtrip `BoolChar`, verify -20001 translation by inserting a loan against a zero-stock book, verify `session.expire` makes the loan status reflect server change.
- **Router**: `TestClient`; happy paths + 404/409 mapping; OpenAPI surface check.

## 8. Risks (carried over + resolved)

| Risk | Status | Resolution |
|---|---|---|
| Oracle -20001 not caught uniformly | Resolved | Single trap in `LoanRepositorySql.create()` |
| BoolChar misbehavior with filters | Mitigated | TypeDecorator handles bind/result; adapter test required |
| Schema reductions break consumers | Low | Done atomically in this change before routers ship |
| Stale loan after return (identity map) | Resolved | `session.expire(loan, ["status","return_date"])` in `ReturnRepositorySql.create` |
| N+1 on book.authors | Resolved | `selectinload(Book.authors)` in `get_with_authors`/`list_with_authors` |
| `expire_on_commit` interaction | Open-Low | Default sessionmaker has `expire_on_commit=True`; after commit ORM auto-reloads anyway. The explicit `expire()` matters within request scope before commit (e.g., return route returns the loan along with the new return). Keep current `expire_on_commit` default. |

## 9. Rollback

Pure-additive. Delete `app/domain`, `app/application`, `app/infrastructure`, `app/api/v1`, `app/composition.py`, revert `main.py` two lines and `app/schemas/**` field drops. No DB changes.
