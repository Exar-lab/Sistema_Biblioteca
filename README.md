<div align="center">

<h1>📚 Sistema de Control de Biblioteca</h1>

<p>
  Plataforma web para administrar usuarios, catálogo, préstamos, devoluciones y reportes de una biblioteca.
</p>

<p>
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="Oracle" src="https://img.shields.io/badge/Oracle-F80000?style=for-the-badge&logo=oracle&logoColor=white">
  <img alt="Jinja2" src="https://img.shields.io/badge/Jinja2-B41717?style=for-the-badge&logo=jinja&logoColor=white">
  <img alt="Bootstrap" src="https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white">
</p>

</div>

---

## 🎯 Objetivo

Construir un sistema de biblioteca simple, mantenible y funcional que permita gestionar libros, autores, categorías, usuarios, préstamos, devoluciones y reportes visuales.

El proyecto está pensado para un desarrollo de **3 semanas**, por eso se prioriza una arquitectura clara y una interfaz rápida de construir.

---

## 💡 Stack recomendado

<table>
  <tr>
    <th>Área</th>
    <th>Tecnología</th>
    <th>Motivo</th>
  </tr>
  <tr>
    <td><strong>Backend</strong></td>
    <td>FastAPI</td>
    <td>Rápido, moderno y fácil de documentar.</td>
  </tr>
  <tr>
    <td><strong>Base de datos</strong></td>
    <td>Oracle</td>
    <td>Permite trabajar con triggers, vistas y procedimientos.</td>
  </tr>
  <tr>
    <td><strong>Frontend</strong></td>
    <td>Jinja2 + Bootstrap</td>
    <td>Ideal para avanzar rápido sin sumar complejidad innecesaria.</td>
  </tr>
  <tr>
    <td><strong>Interactividad</strong></td>
    <td>Vanilla JS</td>
    <td>Suficiente para filtros, confirmaciones y gráficos simples.</td>
  </tr>
</table>

> React puede ser una alternativa si el equipo quiere practicar una tecnología moderna, pero para este alcance conviene **Jinja2 + Bootstrap**. Menos herramientas, menos fricción, más foco en el dominio.

---

## 📋 Módulos del sistema

### 🔐 Usuarios y seguridad

- Registro e inicio de sesión con contraseña hasheada.
- Roles principales:
  - **Administrador**: gestiona usuarios, catálogo, préstamos, devoluciones y reportes.
  - **Usuario / lector**: consulta libros, solicita préstamos y revisa su historial.
- Sesiones mediante JWT o cookies seguras.
- Gestión de cuentas activas e inactivas.

### 📖 Catálogo

- CRUD de libros con título, ISBN, año y cantidad de ejemplares disponibles.
- CRUD de autores.
- Relación **N:M** entre libros y autores.
- CRUD de categorías o géneros.
- Búsqueda y filtros por título, autor y categoría.

### 🔄 Préstamos y devoluciones

- Registro de préstamo por usuario, libro, fecha de préstamo y fecha límite de devolución.
- Registro de devoluciones.
- Actualización automática del stock mediante trigger en Oracle.
- Bloqueo de nuevos préstamos para usuarios con préstamos vencidos.
- Historial de préstamos por usuario.

### 📊 Reportes y gráficos

- Libros más prestados en gráfico de barras.
- Préstamos por mes en gráfico de líneas.
- Usuarios con más préstamos.
- Libros con stock bajo.

### 🛠️ Administración

- Gestión de usuarios.
- Activación y desactivación de cuentas.
- Panel con estadísticas generales:
  - Total de libros.
  - Préstamos activos.
  - Devoluciones pendientes.

---

## 🗄️ Tablas propuestas

El modelo inicial contempla **8 tablas principales**. Esto cubre relaciones **1:N** y **N:M**, además de dejar espacio para triggers, vistas y procedimientos almacenados.

<table>
  <tr>
    <th>Tabla</th>
    <th>Descripción</th>
  </tr>
  <tr>
    <td><code>USUARIO</code></td>
    <td>Datos del lector o administrador.</td>
  </tr>
  <tr>
    <td><code>ROL</code></td>
    <td>Roles del sistema: Administrador y Usuario.</td>
  </tr>
  <tr>
    <td><code>LIBRO</code></td>
    <td>Datos del libro y stock disponible.</td>
  </tr>
  <tr>
    <td><code>AUTOR</code></td>
    <td>Datos del autor.</td>
  </tr>
  <tr>
    <td><code>LIBRO_AUTOR</code></td>
    <td>Relación N:M entre libros y autores.</td>
  </tr>
  <tr>
    <td><code>CATEGORIA</code></td>
    <td>Géneros o tipos de libro.</td>
  </tr>
  <tr>
    <td><code>PRESTAMO</code></td>
    <td>Registro de cada préstamo.</td>
  </tr>
  <tr>
    <td><code>DEVOLUCION</code></td>
    <td>Registro de devoluciones.</td>
  </tr>
</table>

---

## ✅ Reglas de negocio principales

| Regla | Descripción |
| --- | --- |
| Stock disponible | Un libro solo puede prestarse si tiene ejemplares disponibles. |
| Usuario bloqueado | Un usuario con préstamos vencidos no puede solicitar nuevos préstamos. |
| Devolución | Al registrar una devolución, Oracle debe actualizar el stock automáticamente. |
| Administrador | Tiene acceso total a la gestión del sistema. |
| Usuario lector | Solo puede consultar catálogo, hacer préstamos permitidos y ver su historial. |

---

## ⚙️ Setup local (FastAPI + Oracle)

1. Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Si ya existe `venv/` en el proyecto, también podés usar `./venv/Scripts/Activate.ps1`.

2. Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

3. Configurar variables de entorno:

```powershell
Copy-Item .env.example .env
```

Luego editá `.env` con tu conexión Oracle real (`DATABASE_URL`).

4. Verificar sintaxis y ejecutar:

```powershell
python -m compileall app main.py
uvicorn main:app --reload
```

5. Smoke check de salud:

```powershell
curl http://127.0.0.1:8000/health
```

Respuesta esperada con DB disponible:

```json
{"status":"ok","database":"up"}
```

Si Oracle no está disponible o las credenciales son inválidas, el endpoint responde `503`.

---

## 🗄️ Persistencia: SQLAlchemy + Oracle SQL

El backend usa **SQLAlchemy como capa principal de persistencia en tiempo de ejecución**. Las rutas de FastAPI deben delegar en servicios/repositorios y no ejecutar SQL crudo para flujos normales de la aplicación.

Los archivos `.sql` de `database/` siguen siendo artefactos de primer nivel para Oracle:

- creación/bootstrap del esquema;
- constraints, índices, secuencias o identities;
- triggers, por ejemplo reglas de stock y devolución;
- datos iniciales o de referencia;
- scripts manuales de diagnóstico o mantenimiento.

Regla de ownership:

| Responsabilidad | Dueño |
| --- | --- |
| CRUD y consultas de la app | SQLAlchemy en repositorios/servicios |
| Ciclo de sesión por request | `app.core.database.get_db` |
| Reglas de workflow, como bloqueo por mora | Servicios de aplicación |
| Invariantes propias de Oracle, como triggers/constraints | Scripts `.sql` en `database/` |

No borres un `.sql` solo porque exista un modelo ORM. Si se elimina o reemplaza un artefacto Oracle, el cambio debe explicar cuál es el reemplazo y por qué.

Checklist liviano para revisar slices:

- Las rutas FastAPI son finas: validan entrada, inyectan dependencias y delegan.
- Los servicios no importan FastAPI ni SQLAlchemy; coordinan reglas de aplicación.
- Los repositorios concentran ORM, SQLAlchemy y consultas agregadas/reportes.
- Los errores de dominio se traducen a HTTP en `app/api/exception_handlers.py`, no en cada ruta.
- `database/oracle_schema.sql` sigue declarando triggers, constraints e índices propios de Oracle.
- Cada regla nueva declara ownership: servicio de aplicación, repositorio o artefacto Oracle.

---

## 🧭 Próximos pasos

- [ ] Definir los modelos Pydantic del dominio.
- [ ] Diseñar el modelo relacional para Oracle.
- [ ] Crear los scripts SQL iniciales.
- [ ] Implementar autenticación y roles.
- [ ] Construir las primeras vistas con Jinja2 + Bootstrap.

---

<div align="center">
  <strong>Proyecto académico — Programación III</strong>
  <br>
  FastAPI + Oracle + Jinja2 + Bootstrap
</div>
