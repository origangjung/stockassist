from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.adapters.broker import BrokerAdapter
from app.api.routes import get_data_lifecycle_maintenance_service
from app.config import Settings, get_settings
from app.database import Base, create_session_factory
from app.main import app
from app.models.content import DisclosureModel, NewsArticleModel
from app.models.market import DataQualityLogModel
from app.providers.mock import MockProvider
from app.repositories.data_lifecycle import SqlAlchemyDataLifecycleRepository
from app.scheduler import build_scheduler
from app.services.data_lifecycle import DataLifecycleMaintenanceService


def _settings(**overrides: object) -> Settings:
    values = {
        "_env_file": None,
        "admin_api_key": "test-admin-secret",
        "persistence_enabled": False,
        "stock_provider": "mock",
        "financial_provider": "mock",
        "disclosure_provider": "mock",
        "news_provider": "mock",
        "investor_flow_provider": "mock",
        "ai_report_provider": "mock",
        **overrides,
    }
    return Settings(**values)


def _seed_lifecycle_rows(sessions, *, created_at: datetime, suffix: str) -> None:
    with sessions.begin() as session:
        session.add(
            DataQualityLogModel(
                symbol="005930",
                rule=f"rule-{suffix}",
                severity="warning",
                message="bounded test message",
                observed_at=created_at,
                created_at=created_at,
            )
        )
        session.add(
            NewsArticleModel(
                symbol="005930",
                title=f"News {suffix}",
                url=f"https://example.test/news/{suffix}",
                publisher="Test",
                published_at=created_at,
                summary=None,
                source="test",
                created_at=created_at,
            )
        )
        session.add(
            DisclosureModel(
                symbol="005930",
                corp_code="00126380",
                receipt_no=f"receipt-{suffix}",
                company_name="Test Company",
                report_name=f"Report {suffix}",
                filed_at=created_at,
                filer_name="Test Filer",
                remarks=None,
                document_url=f"https://example.test/disclosure/{suffix}",
                source="test",
                created_at=created_at,
            )
        )


def test_lifecycle_repository_counts_and_deletes_only_expired_allowlisted_rows(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'lifecycle.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    old = datetime(2024, 1, 1, tzinfo=UTC)
    recent = datetime(2026, 7, 1, tzinfo=UTC)
    _seed_lifecycle_rows(sessions, created_at=old, suffix="old")
    _seed_lifecycle_rows(sessions, created_at=recent, suffix="recent")
    repository = SqlAlchemyDataLifecycleRepository(sessions)
    cutoffs = {
        "data_quality_logs": datetime(2026, 1, 1, tzinfo=UTC),
        "news": datetime(2026, 1, 1, tzinfo=UTC),
        "disclosures": datetime(2026, 1, 1, tzinfo=UTC),
    }

    assert repository.count_before(cutoffs) == {
        "data_quality_logs": 1,
        "news": 1,
        "disclosures": 1,
    }
    assert repository.delete_before(cutoffs) == {
        "data_quality_logs": 1,
        "news": 1,
        "disclosures": 1,
    }
    assert repository.count_before(
        {dataset: datetime(2030, 1, 1, tzinfo=UTC) for dataset in cutoffs}
    ) == {"data_quality_logs": 1, "news": 1, "disclosures": 1}


def test_lifecycle_repository_rejects_non_allowlisted_dataset(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'allowlist.db'}")
    repository = SqlAlchemyDataLifecycleRepository(sessions)

    with pytest.raises(ValueError, match="Unsupported lifecycle datasets"):
        repository.delete_before({"backtest_runs": datetime(2026, 1, 1, tzinfo=UTC)})


def test_lifecycle_service_previews_then_deletes_with_independent_cutoffs(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'service.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    _seed_lifecycle_rows(
        sessions,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        suffix="candidate",
    )
    service = DataLifecycleMaintenanceService(
        SqlAlchemyDataLifecycleRepository(sessions),
        enabled=True,
        retention_days={"data_quality_logs": 30, "news": 180, "disclosures": 365},
        cleanup_hour_kst=4,
    )
    now = datetime(2026, 7, 19, tzinfo=UTC)

    preview = service.preview(now)
    result = service.cleanup(now)

    assert preview["preview_status"] == "ready"
    assert preview["eligible_counts"] == {
        "data_quality_logs": 1,
        "news": 1,
        "disclosures": 0,
    }
    assert result["status"] == "healthy"
    assert result["last_deleted_counts"] == {
        "data_quality_logs": 1,
        "news": 1,
        "disclosures": 0,
    }


class _FailingLifecycleRepository:
    def count_before(self, _: dict[str, datetime]) -> dict[str, int]:
        raise RuntimeError("private database detail")

    def delete_before(self, _: dict[str, datetime]) -> dict[str, int]:
        raise RuntimeError("private database detail")


def test_lifecycle_service_contains_preview_and_cleanup_failures():
    service = DataLifecycleMaintenanceService(
        _FailingLifecycleRepository(),
        enabled=True,
        retention_days={"data_quality_logs": 180},
        cleanup_hour_kst=4,
    )
    now = datetime(2026, 7, 19, tzinfo=UTC)

    preview = service.preview(now)
    result = service.cleanup(now)

    assert preview["preview_status"] == "failed"
    assert preview["preview_error_type"] == "RuntimeError"
    assert result["status"] == "failed"
    assert result["last_error_type"] == "RuntimeError"
    assert "private database detail" not in str(preview)
    assert "private database detail" not in str(result)


def test_lifecycle_cleanup_requires_persistence():
    with pytest.raises(ValueError, match="DATA_LIFECYCLE_CLEANUP_ENABLED"):
        _settings(data_lifecycle_cleanup_enabled=True)


def test_lifecycle_cleanup_scheduler_runs_daily(tmp_path):
    settings = _settings(
        database_url=f"sqlite:///{tmp_path / 'scheduler.db'}",
        persistence_enabled=True,
        data_lifecycle_cleanup_enabled=True,
        data_lifecycle_cleanup_hour_kst=6,
    )
    service = DataLifecycleMaintenanceService(
        None,
        enabled=False,
        retention_days=settings.data_retention_days,
        cleanup_hour_kst=6,
    )

    scheduler = build_scheduler(
        settings,
        BrokerAdapter([MockProvider()]),
        data_lifecycle_service=service,
    )

    job = scheduler.get_job("operational-data-cleanup")
    assert job is not None
    assert str(job.trigger) == "cron[hour='6', minute='30']"
    assert job.next_run_time is not None


class _StubLifecycleService:
    def preview(self) -> dict[str, object]:
        return {"preview_status": "ready", "eligible_counts": {"news": 2}}

    def cleanup(self) -> dict[str, object]:
        return {"status": "healthy", "last_deleted_counts": {"news": 2}}


def test_lifecycle_admin_endpoints_require_authentication():
    app.dependency_overrides[get_settings] = lambda: _settings()
    service = _StubLifecycleService()
    app.dependency_overrides[get_data_lifecycle_maintenance_service] = lambda: service
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        assert client.get("/api/v1/admin/data-lifecycle/preview").status_code == 401
        assert client.post("/api/v1/admin/data-lifecycle/cleanup").status_code == 401

        preview = client.get("/api/v1/admin/data-lifecycle/preview", headers=headers)
        cleanup = client.post("/api/v1/admin/data-lifecycle/cleanup", headers=headers)

        assert preview.status_code == 200
        assert preview.json()["data"]["eligible_counts"]["news"] == 2
        assert cleanup.status_code == 200
        assert cleanup.json()["data"]["last_deleted_counts"]["news"] == 2
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_data_lifecycle_maintenance_service, None)
