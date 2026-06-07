"""FastAPI entrypoint for the library control system."""

from fastapi import FastAPI, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.authors import router as authors_router
from app.api.v1.routers.books import router as books_router
from app.api.v1.routers.categories import router as categories_router
from app.api.exception_handlers import register_exception_handlers
from app.api.v1.routers.loans import router as loans_router
from app.api.v1.routers.reports import router as reports_router
from app.api.v1.routers.returns import router as returns_router
from app.api.v1.routers.roles import router as roles_router
from app.api.v1.routers.users import router as users_router
from app.core.database import SessionLocal, run_db_smoke_check


app = FastAPI(
    title="Sistema de Control de Biblioteca",
    description="API for managing library users, catalog, loans, returns, and reports.",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(authors_router, prefix="/api/v1")
app.include_router(books_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
register_exception_handlers(app)

app.include_router(loans_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(returns_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")


@app.get("/", include_in_schema=False)
def read_root() -> FileResponse:
    """Serve the static frontend entrypoint."""

    return FileResponse("app/static/index.html")


@app.get("/health", tags=["Health"], response_model=None)
def read_health() -> dict[str, str] | JSONResponse:
    """Verify app and Oracle DB connectivity."""

    try:
        with SessionLocal() as db:
            run_db_smoke_check(db)
        return {"status": "ok", "database": "up"}
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "down"},
        )
