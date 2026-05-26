"""Tests for the reporting dashboard slice and API guardrails."""

import os
from datetime import date
from typing import Any

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "oracle+oracledb://user:pass@127.0.0.1:1/?service_name=FREEPDB1"

import main  # noqa: E402
from app.api.v1.routers.reports import get_report_service  # noqa: E402
from app.application.errors import ConflictError, NotFoundError, OutOfStockError  # noqa: E402
from app.application.services.report_service import ReportService  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.infrastructure.repositories.report_repository import LOW_STOCK_THRESHOLD, SqlAlchemyReportRepository  # noqa: E402
from app.schemas.dashboard import (  # noqa: E402
    DashboardSummary,
    LowStockBookItem,
    MonthlyLoanItem,
    ReportsDashboard,
    TopBookItem,
    TopUserItem,
)


def sample_dashboard() -> ReportsDashboard:
    """Return a complete dashboard payload for service and route tests."""

    return ReportsDashboard(
        summary=DashboardSummary(
            total_books=10,
            total_users=4,
            active_loans=3,
            pending_returns=3,
            overdue_loans=1,
            low_stock_books=1,
        ),
        top_books=[TopBookItem(book_id=1, title="Ficciones", total_loans=7)],
        loans_by_month=[MonthlyLoanItem(month=date(2026, 5, 1), total_loans=7)],
        top_users=[TopUserItem(user_id=1, username="reader", full_name="Reader User", total_loans=7)],
        low_stock_books=[LowStockBookItem(book_id=2, title="Rayuela", stock_available=1, stock_total=3)],
    )


class FakeReportRepository:
    def __init__(self) -> None:
        self.called_with: Any = None
        self.dashboard = sample_dashboard()

    def get_dashboard(self, session: Any) -> ReportsDashboard:
        self.called_with = session
        return self.dashboard


class RaisingReportService:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def get_dashboard(self, _session: Any) -> ReportsDashboard:
        raise self._exc


def test_report_service_delegates_to_repository() -> None:
    repository = FakeReportRepository()
    session = object()

    dashboard = ReportService(repository).get_dashboard(session)

    assert dashboard == repository.dashboard
    assert repository.called_with is session


def test_reports_router_returns_dashboard_payload() -> None:
    service = ReportService(FakeReportRepository())

    main.app.dependency_overrides[get_report_service] = lambda: service
    main.app.dependency_overrides[get_db] = lambda: object()
    try:
        response = TestClient(main.app).get("/api/v1/reports/dashboard")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_books"] == 10
    assert payload["top_books"][0] == {"book_id": 1, "title": "Ficciones", "total_loans": 7}
    assert payload["loans_by_month"][0] == {"month": "2026-05-01", "total_loans": 7}
    assert payload["low_stock_books"][0]["stock_available"] == 1


def test_central_exception_handlers_map_domain_errors() -> None:
    cases = [
        (NotFoundError("missing"), 404),
        (ConflictError("conflict"), 409),
        (OutOfStockError("no stock"), 409),
    ]

    for exc, expected_status in cases:
        main.app.dependency_overrides[get_report_service] = lambda exc=exc: RaisingReportService(exc)
        main.app.dependency_overrides[get_db] = lambda: object()
        try:
            response = TestClient(main.app).get("/api/v1/reports/dashboard")
        finally:
            main.app.dependency_overrides.clear()

        assert response.status_code == expected_status
        assert response.json() == {"detail": str(exc)}


def test_report_repository_uses_documented_low_stock_threshold() -> None:
    assert LOW_STOCK_THRESHOLD == 2
    assert hasattr(SqlAlchemyReportRepository(), "get_dashboard")
