"""ReportRepository outbound port."""

from typing import Any, Protocol, runtime_checkable

from app.schemas.dashboard import ReportsDashboard


@runtime_checkable
class ReportRepository(Protocol):
    """Contract for read-only dashboard/report persistence."""

    def get_dashboard(self, session: Any) -> ReportsDashboard:
        """Return the combined dashboard report payload."""
        ...


__all__ = ["ReportRepository"]
