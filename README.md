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
