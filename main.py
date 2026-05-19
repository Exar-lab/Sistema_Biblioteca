"""FastAPI entrypoint for the library control system."""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.core.database import SessionLocal, run_db_smoke_check


app = FastAPI(
    title="Sistema de Control de Biblioteca",
    description="API for managing library users, catalog, loans, returns, and reports.",
    version="0.1.0",
)


@app.get("/", tags=["Health"])
def read_root() -> dict[str, str]:
    """Return a basic health response for the application."""

    return {"message": "Sistema de Control de Biblioteca API"}


@app.get("/health", tags=["Health"])
def read_health() -> dict[str, str]:
    """Verify app and Oracle DB connectivity."""

    try:
        with SessionLocal() as db:
            run_db_smoke_check(db)
        return {"status": "ok", "database": "up"}
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "down"},
        )
