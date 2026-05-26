"""Application service for read-only reports."""

from typing import Any

from app.application.ports.report_repository import ReportRepository
from app.schemas.dashboard import ReportsDashboard


class ReportService:
    """Coordinate reporting use cases without FastAPI or SQLAlchemy imports."""

    def __init__(self, report_repository: ReportRepository) -> None:
        self._report_repository = report_repository

    def get_dashboard(self, session: Any) -> ReportsDashboard:
        """Return dashboard metrics and ranking lists."""

        return self._report_repository.get_dashboard(session)


__all__ = ["ReportService"]
