# Sistema de Control de Biblioteca

Sistema de biblioteca construido con FastAPI, SQLAlchemy y Oracle. Hoy el repositorio está en etapa **API-first**: expone autenticación JWT, catálogo, préstamos, devoluciones, roles, reportes y un healthcheck. La interfaz web está prevista para una etapa posterior con Jinja2 y Bootstrap.

## Stack actual

| Área | Tecnología |
| --- | --- |
| API | FastAPI |
| Persistencia | SQLAlchemy + Oracle (`oracledb`) |
| Auth | JWT con `python-jose` y hash de contraseñas con `passlib[bcrypt]` |
| Configuración | `pydantic-settings` |
| Pruebas | `pytest` + `TestClient` |
| Frontend previsto | Jinja2 + Bootstrap |

## Qué cubre el proyecto

- Registro e inicio de sesión con token JWT.
- Perfil autenticado en `/api/v1/auth/me`.
- CRUD de libros, autores, categorías y roles.
- Préstamos y devoluciones con reglas de stock.
- Dashboard de reportes para administración.
- Healthcheck de aplicación y base de datos en `/health`.
- Interfaz web futura con templates Jinja2 y estilos Bootstrap.

## Estructura principal

- `main.py` - entrada FastAPI y health endpoints.
- `app/api/v1/routers/` - rutas HTTP por dominio.
- `app/application/services/` - lógica de aplicación.
- `app/infrastructure/repositories/` - acceso a datos con SQLAlchemy.
- `app/schemas/` - modelos Pydantic de entrada/salida.
- `app/core/` - configuración, DB y seguridad.
- `database/oracle_schema.sql` - bootstrap Oracle.
- `tests/` - pruebas unitarias e integración.

## Setup local

1. Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

3. Crear variables de entorno:

```powershell
Copy-Item .env.example .env
```

Editar `.env` con al menos:

- `DATABASE_URL`
- `SECRET_KEY`

Opcionales:

- `SQLALCHEMY_ECHO`
- `ALGORITHM` (por defecto `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (por defecto `30`)

## Bootstrap Oracle

El script `database/oracle_schema.sql` crea o actualiza el usuario `BIBLIOTECA`, tablas, triggers, índices, secuencias y datos iniciales de roles.

Requisitos del script:

- Oracle XE con el PDB `XEPDB1` activo.
- Ejecutarlo como `SYS` o un usuario con privilegios DBA.

Ejemplo:

```powershell
sqlplus / as sysdba @database/oracle_schema.sql
```

El script pide una contraseña para `BIBLIOTECA` y es idempotente. Para validar que quedó bien:

```sql
SELECT object_name, object_type, status
FROM user_objects
WHERE object_type IN ('TABLE', 'TRIGGER', 'INDEX', 'SEQUENCE')
ORDER BY object_type, object_name;
```

## Desarrollo

```powershell
python -m compileall app main.py
uvicorn main:app --reload
```

Healthcheck:

```powershell
curl http://127.0.0.1:8000/health
```

Respuesta esperada si Oracle está disponible:

```json
{"status":"ok","database":"up"}
```

Si la base no responde, el endpoint devuelve `503`.

## Auth y API

- `POST /api/v1/auth/login` devuelve `access_token` y el perfil del usuario.
- `GET /api/v1/auth/me` retorna el usuario autenticado.
- Endpoints principales: `/api/v1/authors`, `/books`, `/categories`, `/loans`, `/returns`, `/reports`, `/roles`.
- Los endpoints de `roles` exigen usuario autenticado con rol administrador.

## Frontend previsto

La UI se implementará con **Jinja2 + Bootstrap** cuando el equipo avance sobre la capa visual. La decisión mantiene el proyecto simple: FastAPI puede renderizar templates server-side sin sumar la complejidad de un frontend separado.

Cuando se agregue esta capa, se espera crear:

- `app/templates/` para páginas Jinja2.
- `app/static/` para CSS, JS e imágenes.
- Vistas para login, catálogo, préstamos, devoluciones y reportes.

## Verificación

Comandos recomendados:

```powershell
python -m compileall app main.py
python -m pytest
```

## Próximos pasos reales

- Completar cobertura de pruebas para flujos de negocio.
- Implementar la interfaz web con Jinja2 + Bootstrap.
- Documentar datos iniciales o usuarios semilla si se agregan.
