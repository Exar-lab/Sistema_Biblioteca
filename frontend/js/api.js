const API_BASE = 'http://localhost:8000/api/v1';

function getToken() { return localStorage.getItem('token'); }
function getUser()  { return JSON.parse(localStorage.getItem('user') || 'null'); }
function isAdmin()  { const u = getUser(); return u?.role?.name?.toLowerCase() === 'admin'; }

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
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API_BASE + path, { ...options, headers });
  if (res.status === 401) { clearSession(); window.location.href = '/index.html'; return; }
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw { status: res.status, detail: data.detail || 'Error desconocido' };
  return data;
}

function requireAuth() {
  if (!getToken()) { window.location.href = '../index.html'; }
}

function requireAdmin() {
  requireAuth();
  if (!isAdmin()) { window.location.href = '../pages/usuario.html'; }
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
