"""Central HTTP translation for application/domain errors."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.errors import (
    ConflictError,
    InactiveUserError,
    InvalidCredentialsError,
    NotFoundError,
    OutOfStockError,
)


def _error_response(status_code: int, exc: Exception) -> JSONResponse:
    """Return the FastAPI error shape used by HTTPException."""

    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    """Register API-layer handlers for framework-free application errors."""

    @app.exception_handler(NotFoundError)
    def handle_not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(status.HTTP_404_NOT_FOUND, exc)

    @app.exception_handler(ConflictError)
    def handle_conflict(_request: Request, exc: ConflictError) -> JSONResponse:
        return _error_response(status.HTTP_409_CONFLICT, exc)

    @app.exception_handler(OutOfStockError)
    def handle_out_of_stock(_request: Request, exc: OutOfStockError) -> JSONResponse:
        return _error_response(status.HTTP_409_CONFLICT, exc)

    @app.exception_handler(InvalidCredentialsError)
    def handle_invalid_credentials(_request: Request, exc: InvalidCredentialsError) -> JSONResponse:
        return _error_response(status.HTTP_401_UNAUTHORIZED, exc)

    @app.exception_handler(InactiveUserError)
    def handle_inactive_user(_request: Request, exc: InactiveUserError) -> JSONResponse:
        return _error_response(status.HTTP_403_FORBIDDEN, exc)


__all__ = ["register_exception_handlers"]
