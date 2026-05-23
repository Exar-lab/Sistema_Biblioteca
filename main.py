"""FastAPI entrypoint for the library control system."""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.routers.authors import router as authors_router
from app.api.v1.routers.books import router as books_router
from app.api.v1.routers.categories import router as categories_router
from app.api.v1.routers.roles import router as roles_router
from app.core.database import SessionLocal, run_db_smoke_check


app = FastAPI(
    title="Sistema de Control de Biblioteca",
    description="API for managing library users, catalog, loans, returns, and reports.",
    version="0.1.0",
)

app.include_router(authors_router, prefix="/api/v1")
app.include_router(books_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def read_root() -> dict[str, str]:
    """Return a basic health response for the application."""

    return {"message": "Sistema de Control de Biblioteca API"}


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
