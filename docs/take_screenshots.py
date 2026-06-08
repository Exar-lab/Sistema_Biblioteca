"""Screenshot script — intercepts API calls with mock data so pages render without a live DB."""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Route

BASE = "http://127.0.0.1:8765"
OUT  = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

ADMIN_USER  = {"id": 1, "email": "admin@biblioteca.cr", "full_name": "Admin Sistema",
               "is_active": True, "role": {"id": 1, "name": "admin"}}
REGULAR_USER = {"id": 2, "email": "juan.perez@mail.com", "full_name": "Juan Pérez",
                "is_active": True, "role": {"id": 2, "name": "usuario"}}

MOCK = {
    "/api/v1/auth/me":       ADMIN_USER,
    "/api/v1/categories/":   [
        {"id": 1, "name": "Ciencia Ficción",   "description": "Literatura de anticipación", "is_active": True, "created_at": "2024-01-10T10:00:00", "updated_at": "2024-01-10T10:00:00"},
        {"id": 2, "name": "Historia",           "description": "Hechos históricos",          "is_active": True, "created_at": "2024-01-11T10:00:00", "updated_at": "2024-01-11T10:00:00"},
        {"id": 3, "name": "Tecnología",         "description": "Informática y sistemas",     "is_active": True, "created_at": "2024-01-12T10:00:00", "updated_at": "2024-01-12T10:00:00"},
        {"id": 4, "name": "Literatura",         "description": "Obras literarias",           "is_active": True, "created_at": "2024-01-13T10:00:00", "updated_at": "2024-01-13T10:00:00"},
        {"id": 5, "name": "Filosofía",          "description": "Pensamiento y lógica",       "is_active": False,"created_at": "2024-01-14T10:00:00", "updated_at": "2024-01-14T10:00:00"},
    ],
    "/api/v1/authors/":      [
        {"id": 1, "first_name": "Isaac",     "last_name": "Asimov",       "biography": "Prolífico autor de ciencia ficción y divulgación científica.", "birth_date": "1920-01-02", "death_date": "1992-04-06", "is_active": True,  "created_at": "2024-01-10T10:00:00", "updated_at": "2024-01-10T10:00:00"},
        {"id": 2, "first_name": "Yuval",     "last_name": "Harari",       "biography": "Historiador israelí, autor de Sapiens.",                       "birth_date": "1976-02-24", "death_date": None,          "is_active": True,  "created_at": "2024-01-11T10:00:00", "updated_at": "2024-01-11T10:00:00"},
        {"id": 3, "first_name": "Gabriel",   "last_name": "García Márquez","biography": "Escritor colombiano, Premio Nobel de Literatura 1982.",       "birth_date": "1927-03-06", "death_date": "2014-04-17", "is_active": True,  "created_at": "2024-01-12T10:00:00", "updated_at": "2024-01-12T10:00:00"},
        {"id": 4, "first_name": "Ursula K.", "last_name": "Le Guin",      "biography": "Escritora estadounidense de ciencia ficción y fantasía.",       "birth_date": "1929-10-21", "death_date": "2018-01-22", "is_active": False, "created_at": "2024-01-13T10:00:00", "updated_at": "2024-01-13T10:00:00"},
    ],
    "/api/v1/books/":        [
        {"id": 1, "title": "Fundación",          "isbn": "978-0-553-29335-7", "description": "Primera entrega de la saga Fundación de Asimov.", "publication_date": "1951-06-01", "publisher": "Gnome Press",    "edition": "1.ª",  "pages": 244, "stock_total": 5, "stock_available": 3, "is_active": True,  "category": {"id": 1, "name": "Ciencia Ficción", "description": None, "is_active": True, "created_at": "2024-01-10T10:00:00", "updated_at": "2024-01-10T10:00:00"}, "authors": [{"id": 1, "first_name": "Isaac", "last_name": "Asimov", "biography": None, "birth_date": None, "death_date": None, "is_active": True, "created_at": "2024-01-10T10:00:00", "updated_at": "2024-01-10T10:00:00"}], "created_at": "2024-01-10T10:00:00", "updated_at": "2024-01-10T10:00:00"},
        {"id": 2, "title": "Sapiens",            "isbn": "978-0-06-231609-7", "description": "Breve historia de la humanidad.",                   "publication_date": "2011-01-01", "publisher": "Harper Collins",  "edition": "2.ª",  "pages": 443, "stock_total": 4, "stock_available": 0, "is_active": True,  "category": {"id": 2, "name": "Historia",        "description": None, "is_active": True, "created_at": "2024-01-11T10:00:00", "updated_at": "2024-01-11T10:00:00"}, "authors": [{"id": 2, "first_name": "Yuval", "last_name": "Harari", "biography": None, "birth_date": None, "death_date": None, "is_active": True, "created_at": "2024-01-11T10:00:00", "updated_at": "2024-01-11T10:00:00"}], "created_at": "2024-01-11T10:00:00", "updated_at": "2024-01-11T10:00:00"},
        {"id": 3, "title": "Cien años de soledad","isbn": "978-0-06-088328-7","description": "Saga de la familia Buendía en Macondo.",             "publication_date": "1967-05-30", "publisher": "Sudamericana",   "edition": "Ed. conm.", "pages": 432, "stock_total": 3, "stock_available": 2, "is_active": True,  "category": {"id": 4, "name": "Literatura",      "description": None, "is_active": True, "created_at": "2024-01-13T10:00:00", "updated_at": "2024-01-13T10:00:00"}, "authors": [{"id": 3, "first_name": "Gabriel", "last_name": "García Márquez", "biography": None, "birth_date": None, "death_date": None, "is_active": True, "created_at": "2024-01-12T10:00:00", "updated_at": "2024-01-12T10:00:00"}], "created_at": "2024-01-12T10:00:00", "updated_at": "2024-01-12T10:00:00"},
        {"id": 4, "title": "El nombre de la rosa","isbn": "978-0-15-144647-6","description": "Novela histórica de Umberto Eco.",                   "publication_date": "1980-01-01", "publisher": "Bompiani",        "edition": "1.ª",  "pages": 502, "stock_total": 2, "stock_available": 2, "is_active": False, "category": {"id": 4, "name": "Literatura",      "description": None, "is_active": True, "created_at": "2024-01-13T10:00:00", "updated_at": "2024-01-13T10:00:00"}, "authors": [],                                                                                                                                                                                                                                                                                                                                                                                                                             "created_at": "2024-01-14T10:00:00", "updated_at": "2024-01-14T10:00:00"},
    ],
    "/api/v1/users/":        [
        {"id": 1, "email": "admin@biblioteca.cr",   "full_name": "Admin Sistema",   "is_active": True,  "role": {"id": 1, "name": "admin"},   "created_at": "2024-01-01T08:00:00", "updated_at": "2024-01-01T08:00:00"},
        {"id": 2, "email": "juan.perez@mail.com",   "full_name": "Juan Pérez",      "is_active": True,  "role": {"id": 2, "name": "usuario"}, "created_at": "2024-01-05T09:00:00", "updated_at": "2024-01-05T09:00:00"},
        {"id": 3, "email": "maria.lopez@mail.com",  "full_name": "María López",     "is_active": True,  "role": {"id": 2, "name": "usuario"}, "created_at": "2024-01-06T10:00:00", "updated_at": "2024-01-06T10:00:00"},
        {"id": 4, "email": "carlos.mora@mail.com",  "full_name": "Carlos Mora",     "is_active": False, "role": {"id": 2, "name": "usuario"}, "created_at": "2024-01-07T11:00:00", "updated_at": "2024-02-15T11:00:00"},
    ],
    "/api/v1/loans/":        [
        {"id": 1, "user_id": 2, "book_id": 1, "loan_date": "2024-06-01", "due_date": "2024-06-15", "return_date": None,         "status": "active",   "book": {"id": 1, "title": "Fundación",           "isbn": "978-0-553-29335-7"}, "user": {"id": 2, "full_name": "Juan Pérez",   "email": "juan.perez@mail.com"},  "created_at": "2024-06-01T09:00:00", "updated_at": "2024-06-01T09:00:00"},
        {"id": 2, "user_id": 3, "book_id": 2, "loan_date": "2024-05-20", "due_date": "2024-06-03", "return_date": None,         "status": "overdue",  "book": {"id": 2, "title": "Sapiens",             "isbn": "978-0-06-231609-7"}, "user": {"id": 3, "full_name": "María López",  "email": "maria.lopez@mail.com"}, "created_at": "2024-05-20T09:00:00", "updated_at": "2024-05-20T09:00:00"},
        {"id": 3, "user_id": 2, "book_id": 3, "loan_date": "2024-05-10", "due_date": "2024-05-24", "return_date": "2024-05-22", "status": "returned", "book": {"id": 3, "title": "Cien años de soledad","isbn": "978-0-06-088328-7"}, "user": {"id": 2, "full_name": "Juan Pérez",   "email": "juan.perez@mail.com"},  "created_at": "2024-05-10T09:00:00", "updated_at": "2024-05-22T14:00:00"},
    ],
    "/api/v1/loans/my":      [
        {"id": 1, "user_id": 2, "book_id": 1, "loan_date": "2024-06-01", "due_date": "2024-06-15", "return_date": None,         "status": "active",   "book": {"id": 1, "title": "Fundación",           "isbn": "978-0-553-29335-7"}, "user": {"id": 2, "full_name": "Juan Pérez", "email": "juan.perez@mail.com"}, "created_at": "2024-06-01T09:00:00", "updated_at": "2024-06-01T09:00:00"},
        {"id": 3, "user_id": 2, "book_id": 3, "loan_date": "2024-05-10", "due_date": "2024-05-24", "return_date": "2024-05-22", "status": "returned", "book": {"id": 3, "title": "Cien años de soledad","isbn": "978-0-06-088328-7"}, "user": {"id": 2, "full_name": "Juan Pérez", "email": "juan.perez@mail.com"}, "created_at": "2024-05-10T09:00:00", "updated_at": "2024-05-22T14:00:00"},
    ],
    "/api/v1/reports/dashboard": {
        "total_books": 4, "active_loans": 2, "overdue_loans": 1, "pending_returns": 2,
        "total_users": 4, "low_stock_books": 1,
        "most_borrowed": [
            {"book_id": 1, "title": "Fundación",           "loan_count": 12},
            {"book_id": 2, "title": "Sapiens",             "loan_count": 9},
            {"book_id": 3, "title": "Cien años de soledad","loan_count": 7},
        ],
        "loans_by_month": [
            {"month": "2024-01", "count": 5},
            {"month": "2024-02", "count": 8},
            {"month": "2024-03", "count": 11},
            {"month": "2024-04", "count": 9},
            {"month": "2024-05", "count": 14},
            {"month": "2024-06", "count": 6},
        ],
    },
    "/api/v1/roles/": [
        {"id": 1, "name": "admin"},
        {"id": 2, "name": "usuario"},
    ],
}

def intercept(route: Route):
    url = route.request.url
    path = url.replace(BASE, "")
    # strip query string
    path_no_qs = path.split("?")[0]
    for key, data in MOCK.items():
        if path_no_qs == key or path_no_qs.rstrip("/") == key.rstrip("/"):
            route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
            return
    # let everything else through (static assets, HTML)
    route.continue_()

def inject_auth(page):
    """Inject a fake JWT + user so requireAuth/requireAdmin pass."""
    page.evaluate("""() => {
        localStorage.setItem('token', 'fake.jwt.token');
        localStorage.setItem('user', JSON.stringify({
            id: 1, email: 'admin@biblioteca.cr', full_name: 'Admin Sistema',
            is_active: true, role: { id: 1, name: 'admin' }
        }));
    }""")

def shot(page, name, wait_ms=800):
    page.wait_for_timeout(wait_ms)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  ✓ {name}.png")
    return path

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        ctx.route("**/api/v1/**", intercept)
        page = ctx.new_page()

        # ── 1. Login page ────────────────────────────────────────────────
        print("Login page…")
        page.goto(f"{BASE}/static/index.html")
        shot(page, "01_login")

        # ── 2. Inject auth for all subsequent pages ───────────────────────
        inject_auth(page)

        # ── 3. Admin dashboard ───────────────────────────────────────────
        print("Dashboard…")
        page.goto(f"{BASE}/static/pages/admin-dashboard.html")
        inject_auth(page)
        shot(page, "02_dashboard", 1200)

        # ── 4. Libros ────────────────────────────────────────────────────
        print("Libros…")
        page.goto(f"{BASE}/static/pages/libros.html")
        inject_auth(page)
        shot(page, "03_libros", 1000)

        # ── 4b. Modal nuevo libro ─────────────────────────────────────────
        page.click("button.btn-primary.btn-sm")
        page.wait_for_timeout(400)
        shot(page, "04_libro_nuevo_modal")

        # ── 5. Autores ───────────────────────────────────────────────────
        print("Autores…")
        page.goto(f"{BASE}/static/pages/autores.html")
        inject_auth(page)
        shot(page, "05_autores", 1000)

        # ── 5b. Modal nuevo autor ─────────────────────────────────────────
        page.click("button.btn-primary.btn-sm")
        page.wait_for_timeout(400)
        shot(page, "06_autor_nuevo_modal")

        # ── 6. Categorías ────────────────────────────────────────────────
        print("Categorías…")
        page.goto(f"{BASE}/static/pages/categorias.html")
        inject_auth(page)
        shot(page, "07_categorias", 1000)

        # ── 7. Usuarios ──────────────────────────────────────────────────
        print("Usuarios…")
        page.goto(f"{BASE}/static/pages/usuarios.html")
        inject_auth(page)
        shot(page, "08_usuarios", 1000)

        # ── 8. Préstamos ─────────────────────────────────────────────────
        print("Préstamos…")
        page.goto(f"{BASE}/static/pages/prestamos.html")
        inject_auth(page)
        shot(page, "09_prestamos", 1000)

        # ── 9. Mis préstamos (vista usuario) ──────────────────────────────
        print("Mis préstamos…")
        page.goto(f"{BASE}/static/pages/mis-prestamos.html")
        page.evaluate("""() => {
            localStorage.setItem('token', 'fake.jwt.token');
            localStorage.setItem('user', JSON.stringify({
                id: 2, email: 'juan.perez@mail.com', full_name: 'Juan Pérez',
                is_active: true, role: { id: 2, name: 'usuario' }
            }));
        }""")
        shot(page, "10_mis_prestamos", 1000)

        # ── 10. Reportes ─────────────────────────────────────────────────
        print("Reportes…")
        page.evaluate("""() => {
            localStorage.setItem('user', JSON.stringify({
                id: 1, email: 'admin@biblioteca.cr', full_name: 'Admin Sistema',
                is_active: true, role: { id: 1, name: 'admin' }
            }));
        }""")
        page.goto(f"{BASE}/static/pages/reportes.html")
        inject_auth(page)
        shot(page, "11_reportes", 1200)

        # ── 11. Catálogo público ──────────────────────────────────────────
        print("Catálogo…")
        page.goto(f"{BASE}/static/pages/catalogo.html")
        inject_auth(page)
        shot(page, "12_catalogo", 1000)

        browser.close()
    print("\nDone. Screenshots saved to:", OUT)

if __name__ == "__main__":
    run()
