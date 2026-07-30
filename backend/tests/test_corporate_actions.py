from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_corporate_action_service
from app.api.routes import get_corporate_action_ingestion_service
from app.config import Settings, get_settings
from app.adapters.broker import BrokerAdapter
from app.backtest import BacktestEngine
from app.corporate_actions import (
    CorporateActionAdjustmentEngine,
    CorporateActionBacktestAdjustmentEngine,
    CorporateActionFetchResult,
    CorporateActionIngestionUnavailableError,
    CorporateActionRecord,
    CorporateActionRevisionConflictError,
    CorporateActionSourceMetadata,
    UntrustedCorporateActionSourceError,
)
from app.database import Base, create_session_factory
from app.main import app
from app.models.market import StockModel
from app.providers.contracts import Candle
from app.providers.mock import MockProvider
from app.repositories.corporate_action import SqlAlchemyCorporateActionRepository
from app.services.corporate_actions import (
    CorporateActionIngestionService,
    CorporateActionService,
)
from app.services.backtest import BacktestService


def _action(
    *,
    revision: int = 1,
    known_at: datetime = datetime(2026, 1, 5, tzinfo=UTC),
    status: str = "confirmed",
    price_factor: str = "0.5",
    symbol: str = "005930",
    source: str = "test",
    event_id: str = "split-2026-01",
) -> CorporateActionRecord:
    return CorporateActionRecord(
        symbol=symbol,
        action_type="split",
        event_id=event_id,
        revision=revision,
        effective_at=datetime(2026, 1, 10, tzinfo=UTC),
        announced_at=datetime(2026, 1, 4, tzinfo=UTC),
        known_at=known_at,
        price_factor=Decimal(price_factor),
        volume_factor=Decimal("2"),
        status=status,
        source=source,
        rule_version="corp-action-2026.1",
    )


def _candles() -> list[Candle]:
    return [
        Candle(
            datetime(2026, 1, 2, tzinfo=UTC),
            Decimal("100"),
            Decimal("120"),
            Decimal("90"),
            Decimal("110"),
            1000,
            "unadjusted",
        ),
        Candle(
            datetime(2026, 1, 12, tzinfo=UTC),
            Decimal("55"),
            Decimal("60"),
            Decimal("50"),
            Decimal("58"),
            2200,
            "unadjusted",
        ),
    ]


def test_adjustment_engine_creates_view_without_mutating_raw_candles():
    source = _candles()
    original = list(source)

    result = CorporateActionAdjustmentEngine().adjust(
        source,
        [_action()],
        as_of=datetime(2026, 1, 12, tzinfo=UTC),
    )

    assert source == original
    assert result.raw_candles_mutated is False
    assert result.adjustment_version == "2026.1"
    assert result.candles[0].open == Decimal("50.0")
    assert result.candles[0].close == Decimal("55.0")
    assert result.candles[0].volume == 2000
    assert result.candles[1] == replace(source[1], price_basis="point_in_time_adjusted")
    assert [(item.event_id, item.revision) for item in result.applied_actions] == [
        ("split-2026-01", 1)
    ]


def test_adjustment_engine_uses_latest_revision_known_at_the_requested_time():
    confirmed = _action()
    cancelled = _action(
        revision=2,
        known_at=datetime(2026, 1, 15, tzinfo=UTC),
        status="cancelled",
    )
    future_correction = _action(
        revision=3,
        known_at=datetime(2026, 1, 20, tzinfo=UTC),
        status="confirmed",
        price_factor="0.4",
    )
    engine = CorporateActionAdjustmentEngine()

    before_cancel = engine.adjust(
        _candles(),
        [confirmed, cancelled, future_correction],
        as_of=datetime(2026, 1, 12, tzinfo=UTC),
    )
    after_cancel = engine.adjust(
        _candles(),
        [confirmed, cancelled, future_correction],
        as_of=datetime(2026, 1, 16, tzinfo=UTC),
    )

    assert before_cancel.candles[0].open == Decimal("50.0")
    assert after_cancel.candles == [
        replace(candle, price_basis="point_in_time_adjusted") for candle in _candles()
    ]
    assert after_cancel.applied_actions == []


def test_adjustment_engine_rejects_naive_timestamps_and_invalid_factors():
    with pytest.raises(ValueError, match="timezone-aware"):
        CorporateActionAdjustmentEngine().adjust(
            _candles(),
            [_action()],
            as_of=datetime(2026, 1, 12),
        )
    with pytest.raises(ValueError, match="factors must be positive"):
        CorporateActionAdjustmentEngine().adjust(
            _candles(),
            [replace(_action(), price_factor=Decimal("0"))],
            as_of=datetime(2026, 1, 12, tzinfo=UTC),
        )


def test_adjustment_engine_rejects_provider_adjusted_candles():
    with pytest.raises(ValueError, match="explicitly unadjusted"):
        CorporateActionAdjustmentEngine().adjust(
            [replace(candle, price_basis="provider_adjusted") for candle in _candles()],
            [_action()],
            as_of=datetime(2026, 1, 12, tzinfo=UTC),
        )


def test_backtest_adjustment_forward_normalizes_only_post_event_candles():
    source = _candles()
    result = CorporateActionBacktestAdjustmentEngine().adjust(
        source,
        [_action()],
        as_of=datetime(2026, 1, 12, tzinfo=UTC),
    )

    assert result.adjustment_direction == "forward"
    assert result.look_ahead_safe is True
    assert result.raw_candles_mutated is False
    assert result.candles[0] == replace(source[0], price_basis="point_in_time_adjusted")
    assert result.candles[1].close == Decimal("116")
    assert result.candles[1].volume == 1100
    assert source[1].close == Decimal("58")


def test_backtest_adjustment_rejects_late_knowledge_and_revision_histories():
    engine = CorporateActionBacktestAdjustmentEngine()
    as_of = datetime(2026, 1, 20, tzinfo=UTC)
    with pytest.raises(ValueError, match="known after"):
        engine.adjust(
            _candles(),
            [_action(known_at=datetime(2026, 1, 11, tzinfo=UTC))],
            as_of=as_of,
        )
    with pytest.raises(ValueError, match="corrected or cancelled"):
        engine.adjust(
            _candles(),
            [
                _action(),
                _action(
                    revision=2,
                    known_at=datetime(2026, 1, 8, tzinfo=UTC),
                    price_factor="0.4",
                ),
            ],
            as_of=as_of,
        )


def test_backtest_adjustment_rejects_non_unadjusted_input():
    with pytest.raises(ValueError, match="explicitly unadjusted"):
        CorporateActionBacktestAdjustmentEngine().adjust(
            [replace(candle, price_basis="provider_adjusted") for candle in _candles()],
            [_action()],
            as_of=datetime(2026, 1, 12, tzinfo=UTC),
        )


def test_backtest_service_opt_in_reports_applied_action_metadata():
    provider = MockProvider()
    source = provider.get_candles("005930", 30)
    action = CorporateActionRecord(
        symbol="005930",
        action_type="split",
        event_id="test-safe-forward-split",
        revision=1,
        effective_at=source[15].timestamp,
        announced_at=source[9].timestamp,
        known_at=source[10].timestamp,
        price_factor=Decimal("0.5"),
        volume_factor=Decimal("2"),
        status="confirmed",
        source="verified-test",
        rule_version="test-2026.1",
    )

    class ActionRepository:
        def list_known(self, symbol: str, *, as_of: datetime):
            assert symbol == "005930"
            assert as_of == source[-1].timestamp
            return [action]

    service = BacktestService(
        BrokerAdapter([provider]),
        BacktestEngine(),
        corporate_actions=CorporateActionService(ActionRepository()),
    )
    result = service.run(
        symbol="005930",
        strategy_name="buy_and_hold",
        limit=30,
        fast_period=5,
        slow_period=20,
        initial_capital=1_000_000,
        commission_rate=0,
        tax_rate=0,
        slippage_rate=0,
        corporate_action_mode="forward_point_in_time",
    )

    metadata = result["corporate_action_adjustment"]
    assert metadata["mode"] == "forward_point_in_time"
    assert metadata["look_ahead_safe"] is True
    assert metadata["raw_candles_mutated"] is False
    assert metadata["applied_actions"][0]["event_id"] == action.event_id


def test_candle_rejects_unknown_price_basis_classification():
    with pytest.raises(ValueError, match="Unsupported candle price basis"):
        replace(_candles()[0], price_basis="ambiguous")


def test_repository_preserves_immutable_revisions_and_point_in_time_queries(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'actions.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    with sessions.begin() as session:
        session.add(StockModel(symbol="005930", name="Samsung", market="KOSPI"))
    repository = SqlAlchemyCorporateActionRepository(sessions)
    action = _action()

    repository.save(action)
    repository.save(action)

    assert repository.list_known("005930", as_of=datetime(2026, 1, 4, tzinfo=UTC)) == []
    known = repository.list_known("005930", as_of=datetime(2026, 1, 6, tzinfo=UTC))
    assert len(known) == 1
    assert known[0].recorded_at is not None
    items, total = repository.list_recent(limit=10, offset=0, symbol="005930")
    assert total == len(items) == 1

    with pytest.raises(CorporateActionRevisionConflictError):
        repository.save(replace(action, price_factor=Decimal("0.4")))


def test_repository_batch_is_atomic_when_a_later_revision_conflicts(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'atomic-actions.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    with sessions.begin() as session:
        session.add(StockModel(symbol="005930", name="Samsung", market="KOSPI"))
    repository = SqlAlchemyCorporateActionRepository(sessions)
    existing = _action()
    repository.save(existing)

    with pytest.raises(CorporateActionRevisionConflictError):
        repository.save_batch(
            [
                _action(revision=2, event_id="new-event"),
                replace(existing, price_factor=Decimal("0.4")),
            ]
        )

    items, total = repository.list_recent(limit=10, offset=0)
    assert total == 1
    assert [(item.event_id, item.revision) for item in items] == [("split-2026-01", 1)]


def test_repository_batch_duplicate_ignores_database_recorded_at(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'recorded-at-actions.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    repository = SqlAlchemyCorporateActionRepository(sessions)
    action = _action()

    created, unchanged = repository.save_batch(
        [action, replace(action, recorded_at=datetime(2026, 2, 1, tzinfo=UTC))]
    )

    assert (created, unchanged) == (1, 1)


class _CorporateActionProvider:
    def __init__(
        self,
        actions: tuple[CorporateActionRecord, ...],
        *,
        trust_status: str = "verified",
    ) -> None:
        self.metadata = CorporateActionSourceMetadata(
            name="verified-source",
            markets=("KR", "US"),
            trust_status=trust_status,
            revision_strategy="source_revision",
        )
        self.actions = actions
        self.calls = 0

    def fetch_actions(
        self,
        symbol: str,
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> CorporateActionFetchResult:
        self.calls += 1
        return CorporateActionFetchResult(
            source=self.metadata.name,
            symbol=symbol,
            fetched_at=datetime(2026, 1, 20, tzinfo=UTC),
            actions=self.actions,
        )


def test_verified_source_ingestion_is_bounded_and_idempotent(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'ingest-actions.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    with sessions.begin() as session:
        session.add(StockModel(symbol="005930", name="Samsung", market="KOSPI"))
    repository = SqlAlchemyCorporateActionRepository(sessions)
    action = _action(source="verified-source")
    provider = _CorporateActionProvider((action, action))
    service = CorporateActionIngestionService(repository, [provider])
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    first = service.ingest("verified-source", "005930", start=start, end=end, limit=10)
    second = service.ingest("verified-source", "005930", start=start, end=end, limit=10)

    assert first["created"] == 1
    assert first["unchanged"] == 1
    assert second["created"] == 0
    assert second["unchanged"] == 2
    assert first["consumer_adjustment_mode"] == "opt_in_disabled"
    assert service.status()["verified_source_count"] == 1


def test_ingestion_rejects_unverified_and_invalid_provider_data(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'invalid-actions.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    repository = SqlAlchemyCorporateActionRepository(sessions)
    experimental = _CorporateActionProvider((), trust_status="experimental")
    service = CorporateActionIngestionService(repository, [experimental])

    with pytest.raises(UntrustedCorporateActionSourceError):
        service.ingest(
            "verified-source",
            "005930",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 31, tzinfo=UTC),
            limit=10,
        )
    assert experimental.calls == 0

    future = _action(
        source="verified-source",
        known_at=datetime(2026, 2, 1, tzinfo=UTC),
    )
    verified = _CorporateActionProvider((future,))
    invalid_service = CorporateActionIngestionService(repository, [verified])
    with pytest.raises(ValueError, match="known_at"):
        invalid_service.ingest(
            "verified-source",
            "005930",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 31, tzinfo=UTC),
            limit=10,
        )


def test_ingestion_reports_disabled_persistence():
    service = CorporateActionIngestionService(None, [])
    assert service.status()["ingestion_available"] is False
    assert [item["name"] for item in service.status()["source_candidates"]] == [
        "dart",
        "dtcc-asset-servicing",
        "nasdaq-daily-list",
        "nyse-market-event-feed",
        "sec-edgar",
    ]
    with pytest.raises(CorporateActionIngestionUnavailableError):
        service.ingest(
            "missing",
            "005930",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 31, tzinfo=UTC),
            limit=10,
        )


def test_service_reports_disabled_storage_and_requires_aware_as_of():
    service = CorporateActionService(None)
    result = service.recent(limit=25, offset=0)

    assert result["persistence_status"] == "disabled"
    assert result["application_mode"] == "preview_only"
    assert result["raw_candles_mutated"] is False
    with pytest.raises(ValueError, match="timezone-aware"):
        service.recent(limit=25, offset=0, as_of=datetime(2026, 1, 1))


class _StubCorporateActionService:
    def recent(self, **_: object) -> dict[str, object]:
        return {
            "persistence_status": "enabled",
            "items": [],
            "total": 0,
            "application_mode": "preview_only",
            "raw_candles_mutated": False,
        }


class _StubCorporateActionIngestionService:
    def status(self) -> dict[str, object]:
        return {
            "persistence_status": "enabled",
            "ingestion_available": False,
            "sources": [],
            "verified_source_count": 0,
            "automatic_ingestion": False,
            "consumer_adjustment_mode": "opt_in_disabled",
            "max_batch_records": 500,
        }

    def ingest(self, source: str, symbol: str, **_: object) -> dict[str, object]:
        return {"source": source, "symbol": symbol, "created": 0, "unchanged": 0}


def test_corporate_action_endpoint_requires_admin_access():
    settings = Settings(_env_file=None, admin_api_key="test-admin-secret")
    service = _StubCorporateActionService()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_corporate_action_service] = lambda: service
    client = TestClient(app)
    try:
        unauthorized = client.get("/api/v1/admin/corporate-actions")
        accepted = client.get(
            "/api/v1/admin/corporate-actions?symbol=005930",
            headers={"X-Admin-Key": "test-admin-secret"},
        )

        assert unauthorized.status_code == 401
        assert accepted.status_code == 200
        assert accepted.json()["data"]["raw_candles_mutated"] is False
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_corporate_action_service, None)


def test_corporate_action_ingestion_endpoints_are_admin_only_and_bounded():
    settings = Settings(_env_file=None, admin_api_key="test-admin-secret")
    service = _StubCorporateActionIngestionService()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_corporate_action_ingestion_service] = lambda: service
    client = TestClient(app)
    headers = {"X-Admin-Key": "test-admin-secret"}
    try:
        assert client.get("/api/v1/admin/corporate-actions/ingestion").status_code == 401
        status = client.get("/api/v1/admin/corporate-actions/ingestion", headers=headers)
        accepted = client.post(
            "/api/v1/admin/corporate-actions/ingestion/test/005930"
            "?start=2026-01-01T00:00:00Z&end=2026-01-31T00:00:00Z&limit=100",
            headers=headers,
        )
        rejected = client.post(
            "/api/v1/admin/corporate-actions/ingestion/test/005930"
            "?start=2026-01-01T00:00:00Z&end=2026-01-31T00:00:00Z&limit=501",
            headers=headers,
        )

        assert status.status_code == 200
        assert status.json()["data"]["consumer_adjustment_mode"] == "opt_in_disabled"
        assert accepted.status_code == 200
        assert rejected.status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_corporate_action_ingestion_service, None)
