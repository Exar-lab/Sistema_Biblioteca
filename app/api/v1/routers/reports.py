"""Report API routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.application.services.report_service import ReportService
from app.core.database import get_db
from app.infrastructure.repositories.report_repository import report_repository
from app.schemas.dashboard import ReportsDashboard

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_report_service() -> ReportService:
    """Build the report service with the SQLAlchemy repository adapter."""

    return ReportService(report_repository)


DbSession = Annotated[Any, Depends(get_db)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


@router.get("/dashboard", response_model=ReportsDashboard)
def get_dashboard(db: DbSession, service: ReportServiceDep) -> ReportsDashboard:
    """Return admin dashboard report metrics."""

    return service.get_dashboard(db)


__all__ = ["router", "get_report_service"]
