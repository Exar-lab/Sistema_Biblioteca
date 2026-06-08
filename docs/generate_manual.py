"""Genera el manual de usuario como un archivo HTML auto-contenido con imágenes en base64."""

import base64
from pathlib import Path

SCREENSHOTS = Path(__file__).parent / "screenshots"
OUT = Path(__file__).parent / "Manual_de_Usuario.html"


def b64(name: str) -> str:
    data = (SCREENSHOTS / name).read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode()


HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Manual de Usuario — Sistema de Control de Biblioteca</title>
<style>
  :root {{
    --primary: #4f46e5;
    --primary-dark: #3730a3;
    --accent: #06b6d4;
    --bg: #f8fafc;
    --surface: #ffffff;
    --text: #1e293b;
    --text-2: #475569;
    --text-3: #94a3b8;
    --border: #e2e8f0;
    --radius: 12px;
    --shadow: 0 4px 24px rgba(0,0,0,0.08);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.7; }}

  /* ── Cover ── */
  .cover {{
    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 55%, var(--accent) 100%);
    color: #fff; text-align: center; padding: 80px 40px 70px;
  }}
  .cover-icon {{ font-size: 64px; margin-bottom: 24px; }}
  .cover h1 {{ font-size: 2.6rem; font-weight: 800; margin-bottom: 12px; letter-spacing: -0.5px; }}
  .cover p  {{ font-size: 1.15rem; opacity: .85; max-width: 540px; margin: 0 auto 32px; }}
  .cover-meta {{ display: inline-flex; gap: 32px; background: rgba(255,255,255,.15); border-radius: 50px; padding: 12px 32px; font-size: .9rem; }}
  .cover-meta span {{ display: flex; align-items: center; gap: 6px; }}

  /* ── Layout ── */
  .wrap {{ max-width: 960px; margin: 0 auto; padding: 0 24px 80px; }}

  /* ── TOC ── */
  .toc {{ background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow); padding: 36px 40px; margin: 48px 0 40px; }}
  .toc h2 {{ font-size: 1.25rem; font-weight: 700; margin-bottom: 20px; color: var(--primary); }}
  .toc ol {{ list-style: none; counter-reset: toc; padding: 0; }}
  .toc ol li {{ counter-increment: toc; padding: 7px 0; border-bottom: 1px solid var(--border); display: flex; align-items: baseline; gap: 10px; }}
  .toc ol li:last-child {{ border: none; }}
  .toc ol li::before {{ content: counter(toc, decimal-leading-zero); color: var(--primary); font-weight: 700; font-size: .85rem; min-width: 28px; }}
  .toc a {{ color: var(--text); text-decoration: none; }}
  .toc a:hover {{ color: var(--primary); }}
  .toc .sub {{ padding-left: 38px; font-size: .92rem; color: var(--text-2); border: none; }}

  /* ── Sections ── */
  .section {{ margin-bottom: 64px; }}
  .section-header {{
    display: flex; align-items: center; gap: 14px;
    border-left: 5px solid var(--primary); padding: 18px 24px;
    background: var(--surface); border-radius: 0 var(--radius) var(--radius) 0;
    box-shadow: var(--shadow); margin-bottom: 28px;
  }}
  .section-num {{ background: var(--primary); color: #fff; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .9rem; flex-shrink: 0; }}
  .section-header h2 {{ font-size: 1.45rem; font-weight: 700; }}
  .section-header .icon {{ font-size: 1.6rem; }}

  .subsection {{ margin: 32px 0 24px; }}
  .subsection h3 {{ font-size: 1.1rem; font-weight: 600; color: var(--primary-dark); margin-bottom: 12px; padding-bottom: 6px; border-bottom: 2px solid var(--border); }}

  p {{ margin-bottom: 14px; color: var(--text-2); }}
  strong {{ color: var(--text); }}

  /* ── Screenshot ── */
  .screenshot-wrap {{ margin: 20px 0 28px; }}
  .screenshot-wrap img {{ width: 100%; border-radius: var(--radius); box-shadow: 0 2px 20px rgba(0,0,0,0.12); border: 1px solid var(--border); display: block; }}
  .caption {{ text-align: center; font-size: .82rem; color: var(--text-3); margin-top: 8px; font-style: italic; }}

  /* ── Steps ── */
  .steps {{ list-style: none; padding: 0; counter-reset: steps; margin: 16px 0 24px; }}
  .steps li {{ counter-increment: steps; display: flex; gap: 14px; margin-bottom: 14px; }}
  .steps li::before {{
    content: counter(steps);
    background: var(--primary); color: #fff; border-radius: 50%;
    min-width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
    font-size: .82rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;
  }}
  .steps li p {{ margin: 0; }}

  /* ── Callouts ── */
  .callout {{ border-radius: var(--radius); padding: 16px 20px; margin: 18px 0; display: flex; gap: 14px; }}
  .callout.info    {{ background: #eff6ff; border: 1px solid #bfdbfe; }}
  .callout.warning {{ background: #fffbeb; border: 1px solid #fde68a; }}
  .callout.danger  {{ background: #fff1f2; border: 1px solid #fecdd3; }}
  .callout-icon {{ font-size: 1.3rem; flex-shrink: 0; margin-top: 2px; }}
  .callout p {{ margin: 0; color: var(--text); }}

  /* ── Role badge ── */
  .role {{ display: inline-block; padding: 2px 10px; border-radius: 50px; font-size: .78rem; font-weight: 600; }}
  .role.admin   {{ background: #ede9fe; color: var(--primary); }}
  .role.usuario {{ background: #d1fae5; color: #065f46; }}

  /* ── Table ── */
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0 24px; font-size: .9rem; }}
  th {{ background: var(--primary); color: #fff; padding: 10px 14px; text-align: left; font-weight: 600; }}
  td {{ padding: 9px 14px; border-bottom: 1px solid var(--border); color: var(--text-2); }}
  tr:hover td {{ background: #f1f5f9; }}
  th:first-child {{ border-radius: var(--radius) 0 0 0; }}
  th:last-child  {{ border-radius: 0 var(--radius) 0 0; }}

  /* ── Footer ── */
  .footer {{ text-align: center; padding: 32px; color: var(--text-3); font-size: .85rem; border-top: 1px solid var(--border); margin-top: 40px; }}

  @media print {{
    body {{ background: #fff; }}
    .cover {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .section-header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .section-num {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>

<!-- ══════════════════ COVER ══════════════════ -->
<div class="cover">
  <div class="cover-icon">📚</div>
  <h1>Sistema de Control de Biblioteca</h1>
  <p>Manual de Usuario — Guía completa para administradores y usuarios del sistema</p>
  <div class="cover-meta">
    <span>📅 Junio 2026</span>
    <span>🔖 Versión 1.0</span>
    <span>🏫 Proyecto Final — Programación III</span>
  </div>
</div>

<div class="wrap">

<!-- ══════════════════ TOC ══════════════════ -->
<div class="toc" id="toc">
  <h2>📋 Tabla de contenidos</h2>
  <ol>
    <li><a href="#s1">Introducción al sistema</a></li>
    <li><a href="#s2">Requisitos y acceso</a></li>
    <li><a href="#s3">Inicio de sesión</a></li>
    <li><a href="#s4">Panel de administración (Dashboard)</a></li>
    <li><a href="#s5">Gestión del catálogo — Libros</a></li>
    <li class="sub"><a href="#s5-1">Consultar y filtrar libros</a></li>
    <li class="sub"><a href="#s5-2">Crear un nuevo libro</a></li>
    <li class="sub"><a href="#s5-3">Editar un libro</a></li>
    <li class="sub"><a href="#s5-4">Eliminar un libro</a></li>
    <li><a href="#s6">Gestión de autores</a></li>
    <li><a href="#s7">Gestión de categorías</a></li>
    <li><a href="#s8">Gestión de usuarios</a></li>
    <li><a href="#s9">Gestión de préstamos (Admin)</a></li>
    <li><a href="#s10">Mis préstamos (Usuario)</a></li>
    <li><a href="#s11">Reportes y estadísticas</a></li>
    <li><a href="#s12">Catálogo público</a></li>
    <li><a href="#s13">Roles y permisos</a></li>
    <li><a href="#s14">Preguntas frecuentes</a></li>
  </ol>
</div>


<!-- ══════════════════ 1. INTRODUCCIÓN ══════════════════ -->
<div class="section" id="s1">
  <div class="section-header">
    <div class="section-num">1</div>
    <span class="icon">ℹ️</span>
    <h2>Introducción al sistema</h2>
  </div>
  <p>El <strong>Sistema de Control de Biblioteca</strong> es una aplicación web diseñada para centralizar y simplificar la administración de una biblioteca: catálogo de libros, gestión de autores y categorías, control de préstamos y devoluciones, y generación de reportes estadísticos.</p>
  <p>El sistema maneja dos tipos de usuarios:</p>
  <table>
    <tr><th>Rol</th><th>Capacidades principales</th></tr>
    <tr><td><span class="role admin">admin</span></td><td>Acceso total: gestión de libros, autores, categorías, usuarios, préstamos y reportes</td></tr>
    <tr><td><span class="role usuario">usuario</span></td><td>Consulta del catálogo y visualización de su propio historial de préstamos</td></tr>
  </table>
  <p>La interfaz está optimizada para uso en computadoras de escritorio y portátiles con navegadores modernos.</p>
</div>


<!-- ══════════════════ 2. REQUISITOS ══════════════════ -->
<div class="section" id="s2">
  <div class="section-header">
    <div class="section-num">2</div>
    <span class="icon">⚙️</span>
    <h2>Requisitos y acceso</h2>
  </div>
  <p><strong>Requisitos del navegador:</strong> Google Chrome, Mozilla Firefox, Microsoft Edge o Safari en sus versiones recientes (2023 en adelante).</p>
  <p><strong>Acceso:</strong> Navegue a la dirección del servidor proporcionada por el administrador (por ejemplo <code>http://localhost:8000</code>). El sistema redirecciona automáticamente a la pantalla de inicio de sesión.</p>
  <div class="callout info">
    <span class="callout-icon">💡</span>
    <p>No se requiere instalación de software adicional. El sistema funciona completamente desde el navegador.</p>
  </div>
</div>


<!-- ══════════════════ 3. LOGIN ══════════════════ -->
<div class="section" id="s3">
  <div class="section-header">
    <div class="section-num">3</div>
    <span class="icon">🔐</span>
    <h2>Inicio de sesión</h2>
  </div>
  <p>Al abrir el sistema aparece la pantalla de inicio de sesión. Ingrese su correo electrónico y contraseña para acceder.</p>

  <div class="screenshot-wrap">
    <img src="{b64('01_login.png')}" alt="Pantalla de inicio de sesión"/>
    <p class="caption">Figura 1 — Pantalla de inicio de sesión</p>
  </div>

  <ol class="steps">
    <li><p>Ingrese su <strong>correo electrónico</strong> en el primer campo.</p></li>
    <li><p>Ingrese su <strong>contraseña</strong> en el segundo campo.</p></li>
    <li><p>Haga clic en <strong>"Iniciar sesión"</strong>.</p></li>
    <li><p>Si las credenciales son correctas, el sistema lo redirige automáticamente según su rol: el administrador va al <em>Dashboard</em> y el usuario regular al <em>Catálogo</em>.</p></li>
  </ol>

  <div class="callout warning">
    <span class="callout-icon">⚠️</span>
    <p>Si su cuenta está <strong>inactiva</strong>, el sistema mostrará un mensaje de error y no permitirá el acceso. Contacte al administrador para reactivarla.</p>
  </div>
</div>


<!-- ══════════════════ 4. DASHBOARD ══════════════════ -->
<div class="section" id="s4">
  <div class="section-header">
    <div class="section-num">4</div>
    <span class="icon">📊</span>
    <h2>Panel de administración (Dashboard)</h2>
  </div>
  <p><span class="role admin">admin</span> Al iniciar sesión, el administrador accede al panel de control con un resumen en tiempo real del estado de la biblioteca.</p>

  <div class="screenshot-wrap">
    <img src="{b64('02_dashboard.png')}" alt="Dashboard de administración"/>
    <p class="caption">Figura 2 — Panel de administración</p>
  </div>

  <p>El dashboard muestra:</p>
  <table>
    <tr><th>Indicador</th><th>Descripción</th></tr>
    <tr><td>Total de libros</td><td>Cantidad total de títulos en el catálogo</td></tr>
    <tr><td>Préstamos activos</td><td>Préstamos vigentes actualmente</td></tr>
    <tr><td>Préstamos vencidos</td><td>Préstamos que superaron su fecha de devolución</td></tr>
    <tr><td>Devoluciones pendientes</td><td>Libros que aún no han sido devueltos</td></tr>
    <tr><td>Libros con stock bajo</td><td>Títulos con 2 o menos ejemplares disponibles</td></tr>
    <tr><td>Libros más prestados</td><td>Ranking de los títulos con más préstamos</td></tr>
    <tr><td>Préstamos por mes</td><td>Gráfico de evolución mensual de préstamos</td></tr>
  </table>

  <div class="callout info">
    <span class="callout-icon">💡</span>
    <p>Los datos del dashboard se actualizan cada vez que carga la página.</p>
  </div>
</div>


<!-- ══════════════════ 5. LIBROS ══════════════════ -->
<div class="section" id="s5">
  <div class="section-header">
    <div class="section-num">5</div>
    <span class="icon">📖</span>
    <h2>Gestión del catálogo — Libros</h2>
  </div>
  <p><span class="role admin">admin</span> El módulo de libros permite consultar, crear, editar y eliminar los títulos del catálogo. Se accede desde el menú lateral → <strong>Libros</strong>.</p>

  <div class="subsection" id="s5-1">
    <h3>5.1 Consultar y filtrar libros</h3>
    <div class="screenshot-wrap">
      <img src="{b64('03_libros.png')}" alt="Listado de libros"/>
      <p class="caption">Figura 3 — Listado de libros con filtros</p>
    </div>
    <p>La tabla principal muestra todos los libros con su título, autores, categoría, stock disponible/total y estado. Puede filtrar usando:</p>
    <ul style="margin: 12px 0 16px 20px; color: var(--text-2);">
      <li style="margin-bottom:6px;"><strong>Buscar por título</strong> — filtro de texto en tiempo real</li>
      <li style="margin-bottom:6px;"><strong>Categoría</strong> — selector desplegable</li>
      <li style="margin-bottom:6px;"><strong>Stock</strong> — "Stock bajo (≤2)" o "Sin stock"</li>
    </ul>
    <p>El stock se muestra como <strong>disponible / total</strong>. Si el stock disponible es 0, aparece en rojo; si es ≤ 2, aparece en naranja.</p>
  </div>

  <div class="subsection" id="s5-2">
    <h3>5.2 Crear un nuevo libro</h3>
    <div class="screenshot-wrap">
      <img src="{b64('04_libro_nuevo_modal.png')}" alt="Modal para crear libro"/>
      <p class="caption">Figura 4 — Formulario de creación de libro</p>
    </div>
    <ol class="steps">
      <li><p>Haga clic en el botón <strong>"+ Nuevo libro"</strong> en la esquina superior derecha.</p></li>
      <li><p>Complete el campo <strong>Título</strong> (obligatorio, mínimo 2 caracteres).</p></li>
      <li><p>Complete los campos opcionales: ISBN, Editorial, Edición, Páginas, Fecha de publicación, Descripción.</p></li>
      <li><p>Defina el <strong>Stock total</strong> (número de ejemplares físicos).</p></li>
      <li><p>Seleccione una <strong>Categoría</strong> del desplegable (opcional).</p></li>
      <li><p>Seleccione uno o varios <strong>Autores</strong> — use Ctrl+clic para seleccionar múltiples.</p></li>
      <li><p>Haga clic en <strong>"Guardar"</strong>. El libro aparecerá en la tabla inmediatamente.</p></li>
    </ol>
  </div>

  <div class="subsection" id="s5-3">
    <h3>5.3 Editar un libro</h3>
    <ol class="steps">
      <li><p>En la fila del libro, haga clic en el ícono de lápiz <strong>✏️</strong>.</p></li>
      <li><p>El formulario se abre con los datos actuales precargados.</p></li>
      <li><p>Modifique los campos necesarios y haga clic en <strong>"Guardar"</strong>.</p></li>
    </ol>
    <div class="callout info">
      <span class="callout-icon">💡</span>
      <p>El campo <strong>Stock disponible</strong> lo gestiona automáticamente el sistema al registrar préstamos y devoluciones. No se modifica manualmente.</p>
    </div>
  </div>

  <div class="subsection" id="s5-4">
    <h3>5.4 Eliminar un libro</h3>
    <ol class="steps">
      <li><p>En la fila del libro, haga clic en el ícono de basura <strong>🗑️</strong>.</p></li>
      <li><p>Aparece un diálogo de confirmación con el título del libro.</p></li>
      <li><p>Haga clic en <strong>"Eliminar"</strong> para confirmar o <strong>"Cancelar"</strong> para abortar.</p></li>
    </ol>
    <div class="callout danger">
      <span class="callout-icon">🚨</span>
      <p>Esta acción es <strong>irreversible</strong>. Solo elimine libros que no tengan préstamos activos asociados.</p>
    </div>
  </div>
</div>


<!-- ══════════════════ 6. AUTORES ══════════════════ -->
<div class="section" id="s6">
  <div class="section-header">
    <div class="section-num">6</div>
    <span class="icon">✍️</span>
    <h2>Gestión de autores</h2>
  </div>
  <p><span class="role admin">admin</span> Acceda desde el menú lateral → <strong>Autores</strong>.</p>

  <div class="screenshot-wrap">
    <img src="{b64('05_autores.png')}" alt="Listado de autores"/>
    <p class="caption">Figura 5 — Listado de autores</p>
  </div>

  <div class="screenshot-wrap">
    <img src="{b64('06_autor_nuevo_modal.png')}" alt="Modal para crear autor"/>
    <p class="caption">Figura 6 — Formulario de creación de autor</p>
  </div>

  <p>El módulo permite administrar la base de datos de autores del catálogo:</p>
  <ol class="steps">
    <li><p>Haga clic en <strong>"+ Nuevo autor"</strong>.</p></li>
    <li><p>Ingrese <strong>Nombre</strong> y <strong>Apellido</strong> (ambos obligatorios).</p></li>
    <li><p>Opcionalmente: fecha de nacimiento, fecha de fallecimiento y una breve biografía.</p></li>
    <li><p>Haga clic en <strong>"Guardar"</strong>.</p></li>
  </ol>

  <p>Puede buscar autores por nombre usando la barra de búsqueda. Los botones de editar y eliminar funcionan igual que en el módulo de libros.</p>
</div>


<!-- ══════════════════ 7. CATEGORÍAS ══════════════════ -->
<div class="section" id="s7">
  <div class="section-header">
    <div class="section-num">7</div>
    <span class="icon">🏷️</span>
    <h2>Gestión de categorías</h2>
  </div>
  <p><span class="role admin">admin</span> Acceda desde el menú lateral → <strong>Categorías</strong>.</p>

  <div class="screenshot-wrap">
    <img src="{b64('07_categorias.png')}" alt="Listado de categorías"/>
    <p class="caption">Figura 7 — Listado de categorías</p>
  </div>

  <p>Las categorías organizan el catálogo (ej.: Ciencia Ficción, Historia, Tecnología). Para crear una nueva:</p>
  <ol class="steps">
    <li><p>Haga clic en <strong>"+ Nueva categoría"</strong>.</p></li>
    <li><p>Ingrese el <strong>Nombre</strong> de la categoría (obligatorio).</p></li>
    <li><p>Opcionalmente agregue una <strong>Descripción</strong>.</p></li>
    <li><p>Haga clic en <strong>"Guardar"</strong>.</p></li>
  </ol>

  <div class="callout warning">
    <span class="callout-icon">⚠️</span>
    <p>No puede eliminar una categoría que tenga libros asignados. Primero reasigne o elimine esos libros.</p>
  </div>
</div>


<!-- ══════════════════ 8. USUARIOS ══════════════════ -->
<div class="section" id="s8">
  <div class="section-header">
    <div class="section-num">8</div>
    <span class="icon">👥</span>
    <h2>Gestión de usuarios</h2>
  </div>
  <p><span class="role admin">admin</span> Acceda desde el menú lateral → <strong>Usuarios</strong>.</p>

  <div class="screenshot-wrap">
    <img src="{b64('08_usuarios.png')}" alt="Listado de usuarios"/>
    <p class="caption">Figura 8 — Listado de usuarios del sistema</p>
  </div>

  <p>El módulo de usuarios permite ver, crear y gestionar todas las cuentas del sistema. Para cada usuario se muestra: nombre, correo, rol, estado (activo/inactivo) y fecha de registro.</p>

  <div class="subsection">
    <h3>Crear un nuevo usuario</h3>
    <ol class="steps">
      <li><p>Haga clic en <strong>"+ Nuevo usuario"</strong>.</p></li>
      <li><p>Complete nombre completo, correo electrónico y contraseña.</p></li>
      <li><p>Seleccione el <strong>Rol</strong>: <em>admin</em> o <em>usuario</em>.</p></li>
      <li><p>Haga clic en <strong>"Guardar"</strong>.</p></li>
    </ol>
  </div>

  <div class="callout info">
    <span class="callout-icon">💡</span>
    <p>Para <strong>desactivar</strong> un usuario sin eliminarlo, use el botón de editar y cambie su estado a inactivo. Un usuario inactivo no puede iniciar sesión.</p>
  </div>
</div>


<!-- ══════════════════ 9. PRÉSTAMOS (ADMIN) ══════════════════ -->
<div class="section" id="s9">
  <div class="section-header">
    <div class="section-num">9</div>
    <span class="icon">📋</span>
    <h2>Gestión de préstamos (Admin)</h2>
  </div>
  <p><span class="role admin">admin</span> Acceda desde el menú lateral → <strong>Préstamos</strong>.</p>

  <div class="screenshot-wrap">
    <img src="{b64('09_prestamos.png')}" alt="Listado de préstamos"/>
    <p class="caption">Figura 9 — Gestión de préstamos</p>
  </div>

  <p>El módulo muestra todos los préstamos del sistema con su estado:</p>
  <table>
    <tr><th>Estado</th><th>Descripción</th></tr>
    <tr><td>🟢 Activo</td><td>El libro está prestado y dentro del plazo</td></tr>
    <tr><td>🔴 Vencido</td><td>El plazo de devolución expiró sin registrar devolución</td></tr>
    <tr><td>⚫ Devuelto</td><td>El libro fue devuelto</td></tr>
  </table>

  <div class="subsection">
    <h3>Registrar un nuevo préstamo</h3>
    <ol class="steps">
      <li><p>Haga clic en <strong>"+ Nuevo préstamo"</strong>.</p></li>
      <li><p>Seleccione el <strong>Usuario</strong> que solicita el préstamo.</p></li>
      <li><p>Seleccione el <strong>Libro</strong> (solo aparecen libros con stock disponible mayor a 0).</p></li>
      <li><p>Defina la <strong>Fecha de devolución</strong>.</p></li>
      <li><p>Haga clic en <strong>"Guardar"</strong>. El stock disponible del libro se reduce automáticamente.</p></li>
    </ol>
  </div>

  <div class="callout warning">
    <span class="callout-icon">⚠️</span>
    <p>Si un usuario tiene un préstamo <strong>vencido</strong>, el sistema no permitirá asignarle nuevos préstamos hasta que devuelva el libro pendiente.</p>
  </div>
</div>


<!-- ══════════════════ 10. MIS PRÉSTAMOS ══════════════════ -->
<div class="section" id="s10">
  <div class="section-header">
    <div class="section-num">10</div>
    <span class="icon">📚</span>
    <h2>Mis préstamos (Usuario)</h2>
  </div>
  <p><span class="role usuario">usuario</span> Los usuarios regulares acceden al historial de sus propios préstamos desde el menú lateral → <strong>Mis préstamos</strong>.</p>

  <div class="screenshot-wrap">
    <img src="{b64('10_mis_prestamos.png')}" alt="Vista de mis préstamos"/>
    <p class="caption">Figura 10 — Vista de mis préstamos (usuario regular)</p>
  </div>

  <p>Esta vista muestra únicamente los préstamos del usuario autenticado, con los campos: libro, fecha de préstamo, fecha de devolución esperada, fecha de devolución real y estado actual.</p>

  <div class="callout info">
    <span class="callout-icon">💡</span>
    <p>Un usuario regular <strong>no puede</strong> ver los préstamos de otros usuarios, ni registrar préstamos directamente — eso es responsabilidad del administrador de la biblioteca.</p>
  </div>
</div>


<!-- ══════════════════ 11. REPORTES ══════════════════ -->
<div class="section" id="s11">
  <div class="section-header">
    <div class="section-num">11</div>
    <span class="icon">📈</span>
    <h2>Reportes y estadísticas</h2>
  </div>
  <p><span class="role admin">admin</span> Acceda desde el menú lateral → <strong>Reportes</strong>.</p>

  <div class="screenshot-wrap">
    <img src="{b64('11_reportes.png')}" alt="Pantalla de reportes"/>
    <p class="caption">Figura 11 — Reportes estadísticos</p>
  </div>

  <p>El módulo de reportes presenta estadísticas avanzadas sobre el uso de la biblioteca:</p>
  <table>
    <tr><th>Reporte</th><th>Descripción</th></tr>
    <tr><td>Libros más prestados</td><td>Ranking de títulos con mayor cantidad de préstamos históricos</td></tr>
    <tr><td>Préstamos por mes</td><td>Evolución temporal del volumen de préstamos</td></tr>
    <tr><td>Usuarios más activos</td><td>Usuarios con mayor número de préstamos registrados</td></tr>
    <tr><td>Stock bajo</td><td>Libros que requieren adquisición de más ejemplares</td></tr>
  </table>
</div>


<!-- ══════════════════ 12. CATÁLOGO ══════════════════ -->
<div class="section" id="s12">
  <div class="section-header">
    <div class="section-num">12</div>
    <span class="icon">🔍</span>
    <h2>Catálogo público</h2>
  </div>
  <p>Accesible para todos los usuarios autenticados. Permite consultar el catálogo completo de libros disponibles.</p>

  <div class="screenshot-wrap">
    <img src="{b64('12_catalogo.png')}" alt="Catálogo de libros"/>
    <p class="caption">Figura 12 — Catálogo de libros</p>
  </div>

  <p>En el catálogo puede:</p>
  <ul style="margin: 12px 0 16px 20px; color: var(--text-2);">
    <li style="margin-bottom:6px;">Buscar libros por <strong>título</strong>, <strong>autor</strong> o <strong>categoría</strong></li>
    <li style="margin-bottom:6px;">Ver el <strong>stock disponible</strong> de cada título</li>
    <li style="margin-bottom:6px;">Ver la ficha completa de un libro (descripción, ISBN, editorial, etc.)</li>
  </ul>

  <div class="callout info">
    <span class="callout-icon">💡</span>
    <p>Para solicitar un préstamo, el usuario debe comunicarse con el personal de la biblioteca (administrador), quien registra el préstamo en el sistema.</p>
  </div>
</div>


<!-- ══════════════════ 13. ROLES ══════════════════ -->
<div class="section" id="s13">
  <div class="section-header">
    <div class="section-num">13</div>
    <span class="icon">🛡️</span>
    <h2>Roles y permisos</h2>
  </div>
  <p>El sistema implementa control de acceso basado en roles. A continuación el resumen completo:</p>
  <table>
    <tr><th>Funcionalidad</th><th><span class="role admin">admin</span></th><th><span class="role usuario">usuario</span></th></tr>
    <tr><td>Dashboard con indicadores</td><td>✅</td><td>❌</td></tr>
    <tr><td>Gestión de libros (CRUD)</td><td>✅</td><td>❌</td></tr>
    <tr><td>Gestión de autores (CRUD)</td><td>✅</td><td>❌</td></tr>
    <tr><td>Gestión de categorías (CRUD)</td><td>✅</td><td>❌</td></tr>
    <tr><td>Gestión de usuarios</td><td>✅</td><td>❌</td></tr>
    <tr><td>Gestión de préstamos (todos)</td><td>✅</td><td>❌</td></tr>
    <tr><td>Ver mis préstamos</td><td>✅</td><td>✅</td></tr>
    <tr><td>Consultar el catálogo</td><td>✅</td><td>✅</td></tr>
    <tr><td>Reportes estadísticos</td><td>✅</td><td>❌</td></tr>
  </table>
</div>


<!-- ══════════════════ 14. FAQ ══════════════════ -->
<div class="section" id="s14">
  <div class="section-header">
    <div class="section-num">14</div>
    <span class="icon">❓</span>
    <h2>Preguntas frecuentes</h2>
  </div>

  <div class="subsection">
    <h3>¿Por qué no puedo iniciar sesión?</h3>
    <p>Verifique que su correo y contraseña sean correctos. Si el sistema muestra "cuenta inactiva", contacte al administrador para que reactive su cuenta.</p>
  </div>

  <div class="subsection">
    <h3>¿Por qué no puedo solicitar un nuevo préstamo?</h3>
    <p>El sistema bloquea nuevos préstamos si tiene un préstamo <strong>vencido</strong> sin devolver. Devuelva el libro pendiente primero.</p>
  </div>

  <div class="subsection">
    <h3>¿Por qué un libro aparece con stock 0?</h3>
    <p>Todos los ejemplares disponibles están actualmente prestados. Cuando alguno sea devuelto, el stock se actualizará automáticamente.</p>
  </div>

  <div class="subsection">
    <h3>¿Puedo tener más de un préstamo activo?</h3>
    <p>Sí, siempre y cuando ninguno de sus préstamos esté vencido. El límite exacto de préstamos simultáneos lo define el administrador de la biblioteca.</p>
  </div>

  <div class="subsection">
    <h3>¿Cómo cambio mi contraseña?</h3>
    <p>Acceda a su perfil desde el menú lateral → <strong>Mi perfil</strong>. Desde allí puede actualizar su información personal y contraseña.</p>
  </div>

  <div class="subsection">
    <h3>¿Qué hago si el sistema muestra un error al guardar?</h3>
    <p>Verifique que todos los campos obligatorios estén completos y que los valores sean válidos (por ejemplo, el título debe tener al menos 2 caracteres). Si el error persiste, contacte al administrador del sistema.</p>
  </div>
</div>

</div><!-- /.wrap -->

<div class="footer">
  Sistema de Control de Biblioteca — Manual de Usuario v1.0 &nbsp;·&nbsp; Junio 2026 &nbsp;·&nbsp; Programación III
</div>

</body>
</html>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"Manual generado: {OUT} ({OUT.stat().st_size // 1024} KB)")
