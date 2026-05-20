"""FastAPI exception handlers for domain errors.

Maps application-layer exceptions to HTTP responses so that routers never
need to import status codes or JSONResponse directly.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.application.errors import ConflictError, NotFoundError, OutOfStockError


async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Translate NotFoundError to HTTP 404."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def out_of_stock_handler(request: Request, exc: OutOfStockError) -> JSONResponse:
    """Translate OutOfStockError to HTTP 409 with OUT_OF_STOCK code."""
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc), "code": "OUT_OF_STOCK"},
    )


async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    """Translate ConflictError to HTTP 409."""
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


__all__ = ["not_found_handler", "out_of_stock_handler", "conflict_handler"]
