"""FastAPI entrypoint for the library control system."""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.exception_handlers import (
    conflict_handler,
    not_found_handler,
    out_of_stock_handler,
)
from app.api.v1.router import api_router
from app.application.errors import ConflictError, NotFoundError, OutOfStockError
from app.core.database import SessionLocal, run_db_smoke_check


app = FastAPI(
    title="Sistema de Control de Biblioteca",
    description="API for managing library users, catalog, loans, returns, and reports.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Domain exception handlers
# ---------------------------------------------------------------------------

app.add_exception_handler(NotFoundError, not_found_handler)
app.add_exception_handler(OutOfStockError, out_of_stock_handler)
app.add_exception_handler(ConflictError, conflict_handler)

# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------


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
