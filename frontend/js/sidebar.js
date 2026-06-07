function renderSidebar(activePage) {
  const user = getUser();
  const admin = isAdmin();
  const initials = user ? user.full_name.split(' ').map(w => w[0]).slice(0,2).join('').toUpperCase() : '??';

  const adminLinks = admin ? `
    <p class="nav-section-label">Administración</p>
    <a href="admin-dashboard.html" class="nav-link ${activePage==='dashboard'?'active':''}">
      <i class="ti ti-layout-dashboard" aria-hidden="true"></i> Dashboard
    </a>
    <a href="libros.html" class="nav-link ${activePage==='libros'?'active':''}">
      <i class="ti ti-books" aria-hidden="true"></i> Libros
    </a>
    <a href="autores.html" class="nav-link ${activePage==='autores'?'active':''}">
      <i class="ti ti-user-circle" aria-hidden="true"></i> Autores
    </a>
    <a href="categorias.html" class="nav-link ${activePage==='categorias'?'active':''}">
      <i class="ti ti-tags" aria-hidden="true"></i> Categorías
    </a>
    <a href="prestamos.html" class="nav-link ${activePage==='prestamos'?'active':''}">
      <i class="ti ti-clock-hour-3" aria-hidden="true"></i> Préstamos
    </a>
    <a href="usuarios.html" class="nav-link ${activePage==='usuarios'?'active':''}">
      <i class="ti ti-users" aria-hidden="true"></i> Usuarios
    </a>
    <a href="reportes.html" class="nav-link ${activePage==='reportes'?'active':''}">
      <i class="ti ti-chart-bar" aria-hidden="true"></i> Reportes
    </a>
  ` : `
    <p class="nav-section-label">Mi cuenta</p>
    <a href="usuario.html" class="nav-link ${activePage==='usuario'?'active':''}">
      <i class="ti ti-home" aria-hidden="true"></i> Inicio
    </a>
    <a href="mis-prestamos.html" class="nav-link ${activePage==='mis-prestamos'?'active':''}">
      <i class="ti ti-clock-hour-3" aria-hidden="true"></i> Mis préstamos
    </a>
    <a href="catalogo.html" class="nav-link ${activePage==='catalogo'?'active':''}">
      <i class="ti ti-books" aria-hidden="true"></i> Catálogo
    </a>
  `;

  document.getElementById('sidebar-root').innerHTML = `
    <aside class="sidebar">
      <div class="sidebar-brand">
        <h1>Biblioteca</h1>
        <span>Sistema de control</span>
      </div>
      <div class="sidebar-user">
        <div class="avatar">${initials}</div>
        <div class="sidebar-user-info">
          <p>${user?.full_name || 'Usuario'}</p>
          <span>${user?.role?.name || ''}</span>
        </div>
      </div>
      <nav class="sidebar-nav">${adminLinks}</nav>
      <div class="sidebar-footer">
        <button class="btn-logout" onclick="doLogout()">
          <i class="ti ti-logout" aria-hidden="true"></i> Cerrar sesión
        </button>
      </div>
    </aside>
  `;
}

function doLogout() {
  clearSession();
  window.location.href = '../index.html';
}

function confirm(title, msg, onConfirm) {
  const d = document.createElement('div');
  d.className = 'confirm-dialog';
  d.innerHTML = `
    <div class="confirm-box">
      <h3>${title}</h3>
      <p>${msg}</p>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="this.closest('.confirm-dialog').remove()">Cancelar</button>
        <button class="btn btn-danger" id="confirmOk">Confirmar</button>
      </div>
    </div>`;
  document.body.appendChild(d);
  d.querySelector('#confirmOk').onclick = () => { d.remove(); onConfirm(); };
}
