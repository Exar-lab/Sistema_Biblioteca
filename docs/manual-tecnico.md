# Manual Técnico — Sistema de Control de Biblioteca

**Versión:** 0.1.0  
**Stack:** Python 3.10+ · FastAPI · SQLAlchemy (sync) · Oracle DB · pytest  
**Fecha:** 2026-06-08

---

## Tabla de Contenidos

1. [Descripción del Proyecto](#1-descripción-del-proyecto)
2. [Arquitectura](#2-arquitectura)
3. [Estructura del Proyecto](#3-estructura-del-proyecto)
4. [Modelos de Dominio](#4-modelos-de-dominio)
5. [Capa de Aplicación](#5-capa-de-aplicación)
6. [Capa de Infraestructura](#6-capa-de-infraestructura)
7. [Capa de API](#7-capa-de-api)
8. [Autenticación y Seguridad](#8-autenticación-y-seguridad)
9. [Configuración](#9-configuración)
10. [Base de Datos](#10-base-de-datos)
11. [Manejo de Errores](#11-manejo-de-errores)
12. [Pruebas](#12-pruebas)
13. [Configuración Local](#13-configuración-local)
14. [Datos de Demostración](#14-datos-de-demostración)

---

## 1. Descripción del Proyecto

El Sistema de Control de Biblioteca es un backend REST API para gestionar el ciclo de vida completo de una biblioteca: gestión del catálogo (libros, autores, categorías), cuentas de usuario, operaciones de préstamo, devoluciones e informes administrativos.

La aplicación está construida siguiendo la **Arquitectura Hexagonal** (Puertos y Adaptadores). La lógica de negocio reside en servicios sin dependencias de frameworks; FastAPI y SQLAlchemy son detalles de implementación detrás de puertos.

Un frontend estático (HTML + CSS + JS vanilla) se sirve directamente desde FastAPI en `/` y `/static`, proporcionando vistas para login, catálogo, préstamos, devoluciones y el panel de reportes.

---

## 2. Arquitectura

### Arquitectura Hexagonal (Puertos y Adaptadores)

```
┌─────────────────────────────────────────────────┐
│                   Capa de API                    │
│    Routers FastAPI · Schemas Pydantic · Deps     │
└────────────────────┬────────────────────────────┘
                     │ llama a
┌────────────────────▼────────────────────────────┐
│             Capa de Aplicación                   │
│    Servicios · Puertos (Protocols) · Errores     │
│    Sin imports de FastAPI · Sin SQLAlchemy       │
└────────────────────┬────────────────────────────┘
                     │ implementa
┌────────────────────▼────────────────────────────┐
│           Capa de Infraestructura                │
│    Repositorios SQLAlchemy · Adaptadores Oracle  │
└─────────────────────────────────────────────────┘
```

**Regla clave:** La capa de aplicación no tiene conocimiento de FastAPI ni de SQLAlchemy. Depende únicamente de interfaces de puertos (Python `Protocol`) y lanza excepciones sin dependencias de framework desde `app/application/errors.py`.

### Flujo de Dependencias por Solicitud

```
HTTP Request
  → Router FastAPI
    → get_db() yields Session
    → Service (inyectado via Depends)
      → Repository Port (Protocol)
        → SQLAlchemy / Oracle (Infraestructura)
  ← Respuesta serializada por schema Pydantic
```

---

## 3. Estructura del Proyecto

```
Sistema_Biblioteca/
├── main.py                            # Factory de la app FastAPI, endpoint de salud, registro de routers
├── app/
│   ├── api/
│   │   ├── exception_handlers.py      # Mapea errores de dominio → códigos de estado HTTP
│   │   ├── dependencies.py            # Dependencias compartidas de FastAPI (get_current_user, AdminOnly)
│   │   └── v1/routers/               # Un archivo por dominio
│   │       ├── auth.py               # POST /login, POST /register, GET /me, PATCH /me/password
│   │       ├── authors.py
│   │       ├── books.py
│   │       ├── categories.py
│   │       ├── loans.py
│   │       ├── returns.py
│   │       ├── roles.py
│   │       ├── reports.py
│   │       └── users.py
│   ├── application/
│   │   ├── errors.py                  # Excepciones de dominio (sin HTTP, sin SQLAlchemy)
│   │   ├── ports/                     # Contratos de repositorios (clases Protocol)
│   │   └── services/                  # Casos de uso de negocio
│   ├── domain/
│   │   └── models/                    # Modelos ORM de SQLAlchemy
│   ├── infrastructure/
│   │   └── repositories/             # Implementaciones concretas SQLAlchemy + Oracle
│   ├── schemas/                       # Modelos Pydantic de request / response
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── roles.py
│   │   ├── dashboard.py
│   │   ├── catalog/                   # authors.py, books.py, categories.py
│   │   └── circulation/              # loans.py, returns.py
│   ├── core/
│   │   ├── config.py                  # Clase Settings de pydantic-settings
│   │   ├── database.py               # Engine, SessionLocal, get_db, smoke check
│   │   ├── security.py               # Hashing bcrypt, firma / decodificación JWT
│   │   └── base.py                   # Base declarativa de SQLAlchemy
│   └── static/                       # Frontend estático (HTML, CSS, JS)
├── database/
│   └── oracle_schema.sql             # DDL Oracle: tablas, triggers, secuencias, índices
├── scripts/
│   └── seed_demo_data.py             # Sembrador de datos de demostración determinístico
└── tests/
    ├── conftest.py                    # Variables de entorno predeterminadas para tests
    ├── integration/                  # Tests de integración de repositorios (requiere Oracle)
    └── unit/                         # Tests unitarios con sesiones mockeadas
```

---

## 4. Modelos de Dominio

Todos los modelos ORM residen en `app/domain/models/` y usan `schema="BIBLIOTECA"` para limitar cada tabla al usuario Oracle `BIBLIOTECA`.

### LibraryUser (`library_users`)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | Integer PK | Autoincremento via secuencia Oracle |
| `username` | String(50) | Único |
| `full_name` | String(120) | |
| `email` | String(255) | Único |
| `phone` | String(30) | Nullable |
| `password_hash` | String(255) | Hash bcrypt |
| `is_active` | BoolChar (`'Y'`/`'N'`) | Default `'Y'` |
| `role_id` | FK → roles | |
| `created_at`, `updated_at` | TIMESTAMP | Server default `SYSTIMESTAMP` |

Relaciones: `role` (muchos-a-uno), `loans` (uno-a-muchos).

### Book (`books`)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | Integer PK | |
| `title` | String(200) | |
| `isbn` | String(20) | Único, nullable |
| `description` | String(4000) | Nullable |
| `publication_date` | Date | Nullable |
| `publisher` | String(120) | Nullable |
| `edition` | String(40) | Nullable |
| `pages` | Integer | Nullable |
| `stock_total` | Integer | Default 0 |
| `stock_available` | Integer | Default 0; decrementado por `trg_loans_decrement_stock` |
| `is_active` | BoolChar | Default `'Y'` |
| `category_id` | FK → categories | Nullable |

Relaciones: `category` (muchos-a-uno), `authors` (muchos-a-muchos via `book_authors`), `loans` (uno-a-muchos).

### Loan (`loans`)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → library_users | |
| `book_id` | FK → books | |
| `loan_date` | Date | Default `TRUNC(SYSDATE)` |
| `due_date` | Date | |
| `return_date` | Date | Nullable; se establece al devolver |
| `status` | String(20) | `ACTIVE`, `RETURNED`, `CANCELLED` |

Relaciones: `user`, `book`, `return_` (uno-a-uno).

### Otros Modelos

- **Author** (`authors`): `id`, `name`, `bio`, `is_active`, timestamps.
- **Category** (`categories`): `id`, `name`, `description`, `is_active`, timestamps.
- **Role** (`roles`): `id`, `name`, `description`, timestamps.
- **Return_** (`returns`): `id`, `loan_id` (FK, único), `return_date`, `notes`, timestamps.

### Tipo BoolChar

Oracle no tiene un tipo booleano nativo. El proyecto usa un `TypeDecorator` de SQLAlchemy personalizado (`BoolChar`) que almacena `'Y'` / `'N'` en `CHAR(1)` y expone `True` / `False` a Python.

---

## 5. Capa de Aplicación

### Puertos (`app/application/ports/`)

Cada dominio tiene una interfaz `Protocol` que declara el contrato para su repositorio. Los servicios dependen de estos protocolos, nunca de las implementaciones concretas de SQLAlchemy.

Ejemplo — puerto `LoanRepository`:

```python
class LoanRepository(Protocol):
    def get_by_id(self, session, id) -> Loan | None: ...
    def list_all(self, session) -> list[Loan]: ...
    def create(self, session, data) -> Loan: ...          # raises OutOfStockError
    def update(self, session, id, data) -> Loan | None: ...
    def delete(self, session, id) -> bool: ...
    def get_by_user(self, session, user_id) -> list[Loan]: ...
    def get_by_book(self, session, book_id) -> list[Loan]: ...
    def has_overdue_loans(self, session, user_id) -> bool: ...
    def cancel(self, session, loan_id) -> bool: ...
```

### Servicios (`app/application/services/`)

Los servicios orquestan casos de uso llamando a los puertos y lanzando errores de dominio. No importan ningún símbolo de FastAPI o SQLAlchemy.

| Servicio | Responsabilidades |
|---|---|
| `AuthService` | Login (valida credenciales, emite JWT), registro, cambio de contraseña |
| `AuthorService` | CRUD autores, lanza `NotFoundError` |
| `BookService` | CRUD libros incluyendo asignación de autores |
| `CategoryService` | CRUD categorías |
| `LoanService` | Crear/actualizar/cancelar préstamos, valida estado activo del usuario y estado de mora |
| `ReturnService` | Crea registros de devolución, actualiza estado del préstamo |
| `RoleService` | CRUD roles |
| `ReportService` | Agrega métricas del panel de control |
| `UserService` | Gestión de usuarios (admin) |

### Errores de Dominio (`app/application/errors.py`)

| Excepción | Significado |
|---|---|
| `NotFoundError` | El recurso no existe |
| `OutOfStockError` | Sin stock disponible para un nuevo préstamo |
| `ConflictError` | Registro duplicado o en conflicto |
| `InvalidCredentialsError` | Usuario o contraseña incorrectos |
| `InactiveUserError` | Usuario inactivo intentó realizar una acción |

---

## 6. Capa de Infraestructura

### Repositorios SQLAlchemy (`app/infrastructure/repositories/`)

Implementaciones concretas de los protocolos de puertos. Patrón:

- **Lecturas** usan consultas ORM `select()` de SQLAlchemy.
- **Escrituras** para préstamos y devoluciones delegan exclusivamente a **procedimientos almacenados** de Oracle (`pkg_loans`, `pkg_returns`) via `callproc`.
- No hay `session.commit()` ni `session.rollback()` dentro de los repositorios — el ciclo de vida de la sesión es propiedad de `get_db()` en la capa de API.

### Repositorio de Préstamos — Integración con Procedimientos Almacenados

```python
# Insert via pkg_loans.p_insert con un parámetro OUT para el nuevo ID
with session.connection().connection.cursor() as cur:
    out_id = cur.var(int)
    cur.callproc("BIBLIOTECA.pkg_loans.p_insert", [
        data.user_id, data.book_id, data.loan_date, data.due_date, out_id
    ])
    new_id = out_id.getvalue()
session.expire_all()
return self.get_by_id(session, new_id)
```

`session.expire_all()` se llama después de cada escritura para que la lectura ORM subsiguiente refleje los cambios del lado de Oracle (decrementos de stock, actualizaciones de triggers).

**Detección de ORA-20001:** el trigger de Oracle `trg_loans_decrement_stock` lanza `-20001` cuando el stock es cero. El repositorio lo captura y lo traduce a `OutOfStockError`.

---

## 7. Capa de API

### Registro de Routers (`main.py`)

Todos los routers se montan bajo `/api/v1`:

```
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/auth/me
PATCH  /api/v1/auth/me/password

GET    /api/v1/authors          POST /api/v1/authors
GET    /api/v1/authors/{id}     PATCH /api/v1/authors/{id}    DELETE /api/v1/authors/{id}

GET    /api/v1/books            POST /api/v1/books
GET    /api/v1/books/{id}       PATCH /api/v1/books/{id}      DELETE /api/v1/books/{id}

GET    /api/v1/categories       POST /api/v1/categories
GET    /api/v1/categories/{id}  PATCH /api/v1/categories/{id} DELETE /api/v1/categories/{id}

GET    /api/v1/loans            POST /api/v1/loans
POST   /api/v1/loans/me                                       (préstamo de autoservicio)
GET    /api/v1/loans/{id}       PATCH /api/v1/loans/{id}
PATCH  /api/v1/loans/{id}/return
PATCH  /api/v1/loans/{id}/cancel
GET    /api/v1/loans/users/{user_id}
GET    /api/v1/loans/books/{book_id}

GET    /api/v1/returns          POST /api/v1/returns
GET    /api/v1/returns/{id}

GET    /api/v1/roles            POST /api/v1/roles
GET    /api/v1/roles/{id}       PATCH /api/v1/roles/{id}      DELETE /api/v1/roles/{id}

GET    /api/v1/users            POST /api/v1/users
GET    /api/v1/users/{id}       PATCH /api/v1/users/{id}      DELETE /api/v1/users/{id}

GET    /api/v1/reports/dashboard

GET    /health
```

### Niveles de Autorización

| Dependencia | Quién puede usar |
|---|---|
| `get_current_user` | Cualquier usuario autenticado (valida el token Bearer) |
| `AdminOnly` | Solo usuarios con rol `"admin"` (retorna 403 en caso contrario) |

Los préstamos siguen un modelo mixto: listar y crear por ID de usuario requieren admin; `POST /loans/me` y devolver préstamos propios funciona para cualquier usuario autenticado.

---

## 8. Autenticación y Seguridad

### Flujo JWT

1. El cliente envía `POST /api/v1/auth/login` con `{ username, password }`.
2. `AuthService.authenticate()` verifica el hash bcrypt con `verify_password()`.
3. En caso de éxito, `create_access_token()` firma un JWT con `sub` (ID de usuario), `username` y `role`.
4. La respuesta retorna `{ access_token, token_type: "bearer", user: UserRead }`.
5. Las solicitudes subsiguientes incluyen `Authorization: Bearer <token>`.
6. La dependencia `get_current_user` decodifica el token con `decode_token()` y carga el usuario desde la BD.

### Configuración del Token

| Configuración | Valor por defecto | Descripción |
|---|---|---|
| `SECRET_KEY` | Requerido | Clave de firma (debe mantenerse secreta) |
| `ALGORITHM` | `HS256` | Algoritmo de firma JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Tiempo de vida del token en minutos |

### Hashing de Contraseñas

`passlib` con esquema `bcrypt`. Nunca se almacenan ni se retornan contraseñas en texto plano en las respuestas.

---

## 9. Configuración

Las configuraciones se cargan desde `.env` via `pydantic-settings`. La función `get_settings()` se cachea con `@lru_cache` para que el archivo `.env` se lea solo una vez por proceso.

```
DATABASE_URL=oracle+oracledb://BIBLIOTECA:password@localhost:1521/?service_name=XEPDB1
SECRET_KEY=your-secret-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
SQLALCHEMY_ECHO=false
```

Copiar `.env.example` a `.env` para comenzar.

---

## 10. Base de Datos

### Configuración del Engine

Engine SQLAlchemy síncrono usando `oracledb` (modo thin por defecto):

```python
engine = create_engine(settings.DATABASE_URL, echo=settings.SQLALCHEMY_ECHO)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

### Ciclo de Vida de la Sesión

`get_db()` es una dependencia de FastAPI que cede una sesión y gestiona commit/rollback:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### Schema Oracle (`database/oracle_schema.sql`)

El script se ejecuta como `SYS`/DBA y crea (o re-crea de forma idempotente):

- **Usuario:** `BIBLIOTECA` con todos los permisos requeridos.
- **Tablas:** `library_users`, `roles`, `books`, `authors`, `categories`, `book_authors`, `loans`, `returns`.
- **Secuencias:** Una por tabla para la generación de claves primarias.
- **Triggers:**
  - `trg_loans_decrement_stock` — decrementa `books.stock_available` al insertar un préstamo; lanza `ORA-20001` cuando el stock es cero.
  - `trg_returns_increment_stock` — incrementa `books.stock_available` al insertar una devolución.
- **Procedimientos Almacenados:** Paquetes `pkg_loans` y `pkg_returns` para operaciones de escritura.
- **Índices:** En claves foráneas y columnas frecuentemente filtradas.

### Healthcheck

```
GET /health → { "status": "ok", "database": "up" }     # 200
            → { "status": "error", "database": "down" } # 503
```

Ejecuta `SELECT 1 FROM DUAL` para verificar la conectividad con Oracle.

---

## 11. Manejo de Errores

Los manejadores de excepciones registrados en `app/api/exception_handlers.py` traducen errores de dominio a respuestas HTTP con una forma consistente:

```json
{ "detail": "<mensaje de error>" }
```

| Excepción de Dominio | Estado HTTP |
|---|---|
| `NotFoundError` | 404 Not Found |
| `ConflictError` | 409 Conflict |
| `OutOfStockError` | 409 Conflict |
| `InvalidCredentialsError` | 401 Unauthorized |
| `InactiveUserError` | 403 Forbidden |

El `RequestValidationError` predeterminado de FastAPI sigue retornando 422 para cuerpos de solicitud malformados (fallos de validación de Pydantic).

---

## 12. Pruebas

### Estructura

```
tests/
├── conftest.py                      # Establece variables de entorno DATABASE_URL y SECRET_KEY para los tests
├── test_health_and_db_lifecycle.py
├── test_authors_slice.py
├── test_categories_slice.py
├── test_reports_slice.py
├── test_roles_slice.py
├── unit/
│   └── repositories/
│       ├── test_loan_repository.py
│       ├── test_return_repository.py
│       └── test_role_repository.py
└── integration/
    └── test_repositories_integration.py  # Requiere conexión Oracle en vivo
```

### Ejecutar Pruebas

```powershell
# Todas las pruebas (solo unitarias si Oracle no está disponible)
python -m pytest

# Slice específico
python -m pytest tests/test_authors_slice.py -v

# Pruebas de integración (requiere Oracle)
python -m pytest tests/integration/ -v
```

### Valores por Defecto para Tests (`conftest.py`)

Establece valores ficticios para que los tests unitarios no fallen por variables de entorno faltantes:

```python
os.environ.setdefault("DATABASE_URL", "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-jwt-auth")
```

---

## 13. Configuración Local

### Prerequisitos

- Python 3.10+
- Oracle XE con el PDB `XEPDB1` (o `FREEPDB1`) activo
- `sqlplus` disponible para el bootstrap del schema

### Pasos

```powershell
# 1. Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
python -m pip install -r requirements.txt

# 3. Configurar el entorno
Copy-Item .env.example .env
# Editar .env con DATABASE_URL y SECRET_KEY

# 4. Bootstrap del schema Oracle (ejecutar como SYS/DBA)
sqlplus / as sysdba @database/oracle_schema.sql

# 5. Sembrar datos de demostración (opcional)
python scripts/seed_demo_data.py

# 6. Iniciar el servidor
uvicorn main:app --reload
```

### Verificar Sintaxis (verificación previa a la ejecución)

```powershell
python -m compileall app main.py scripts
```

### Documentación de la API

Con el servidor en ejecución, visitar:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **Frontend:** `http://127.0.0.1:8000/`

---

## 14. Datos de Demostración

El script `scripts/seed_demo_data.py` inserta un conjunto de datos determinístico con fechas fijas para que el historial de préstamos sea reproducible entre ejecuciones. Es seguro volver a ejecutarlo.

### Credenciales de Demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| `demo.admin` | `DemoAdmin123!` | Admin |
| `demo.alice` | `DemoUser123!` | Usuario |
| `demo.ben` | `DemoUser123!` | Usuario |
| `demo.clara` | `DemoUser123!` | Usuario |
| `demo.dan` | `DemoUser123!` | Usuario |
| `demo.valeria` | `DemoUser123!` | Usuario |

### Validar Objetos de la Base de Datos

```sql
SELECT object_name, object_type, status
FROM user_objects
WHERE object_type IN ('TABLE', 'TRIGGER', 'INDEX', 'SEQUENCE')
ORDER BY object_type, object_name;
```
