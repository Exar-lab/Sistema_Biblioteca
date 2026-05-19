"""FastAPI entrypoint for the library control system."""

from fastapi import FastAPI


app = FastAPI(
    title="Sistema de Control de Biblioteca",
    description="API for managing library users, catalog, loans, returns, and reports.",
    version="0.1.0",
)


@app.get("/", tags=["Health"])
def read_root() -> dict[str, str]:
    """Return a basic health response for the application."""

    return {"message": "Sistema de Control de Biblioteca API"}
