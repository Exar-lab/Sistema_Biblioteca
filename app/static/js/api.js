const API_BASE = 'http://localhost:8000/api/v1';

function getToken() { return localStorage.getItem('token'); }
function getUser()  { return JSON.parse(localStorage.getItem('user') || 'null'); }
function isAdmin()  { const u = getUser(); return u?.role?.name?.toLowerCase() === 'admin'; }

function isInPagesDir() {
  return window.location.pathname.replace(/\\/g, '/').includes('/pages/');
}

function resolveLoginUrl() {
  return isInPagesDir() ? '../index.html' : 'index.html';
}

function resolvePageUrl(page) {
  return isInPagesDir() ? page : `pages/${page}`;
}

function redirectToLogin() {
  window.location.href = resolveLoginUrl();
}

function redirectToPage(page) {
  window.location.href = resolvePageUrl(page);
}

function escapeHtml(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function jsString(value) {
  return escapeHtml(JSON.stringify(value === null || value === undefined ? '' : String(value)));
}

function setSession(data) {
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
}

function clearSession() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (!headers.has('Accept')) headers.set('Accept', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body != null && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(API_BASE + path, { ...options, headers });
  if (res.status === 204) return null;

  const contentType = res.headers.get('content-type') || '';
  const rawBody = await res.text();
  let data = null;

  if (rawBody) {
    if (contentType.includes('application/json')) {
      try { data = JSON.parse(rawBody); } catch { data = rawBody; }
    } else {
      data = rawBody;
    }
  }

  if (res.status === 401) {
    clearSession();
    if (!path.startsWith('/auth/login') && !path.startsWith('/auth/register')) {
      redirectToLogin();
    }
  }

  if (!res.ok) {
    const detail = typeof data === 'string'
      ? data
      : data?.detail || data?.message || `HTTP ${res.status}`;
    throw { status: res.status, detail };
  }
  return data;
}

function requireAuth() {
  if (!getToken()) { redirectToLogin(); return false; }
  return true;
}

function requireAdmin() {
  if (!requireAuth()) return false;
  if (!isAdmin()) { redirectToPage('usuario.html'); return false; }
  return true;
}

function showToast(msg, type = 'success') {
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.classList.add('show'), 10);
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 3500);
}

function formatDate(str) {
  if (!str) return '—';
  return new Date(str).toLocaleDateString('es-CR', { day: '2-digit', month: 'short', year: 'numeric' });
}

function today() {
  return new Date().toISOString().split('T')[0];
}
