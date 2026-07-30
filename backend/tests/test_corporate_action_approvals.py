from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.routes import get_corporate_action_approval_service
from app.config import Settings, get_settings
from app.corporate_actions.approval_contracts import (
    CorporateActionApprovalEvidence,
    CorporateActionApprovalResult,
    CorporateActionApprovalUnavailableError,
)
from app.corporate_actions.contracts import CorporateActionRecord
from app.database import Base, create_session_factory
from app.main import app
from app.models.corporate_action import CorporateActionApprovalModel
from app.models.market import StockModel
from app.repositories.corporate_action_approval import (
    SqlAlchemyCorporateActionApprovalRepository,
)
from app.services.corporate_actions import CorporateActionApprovalService


REVIEWED_AT = datetime(2026, 7, 20, 3, 0, tzinfo=UTC)
EFFECTIVE_AT = datetime(2026, 6, 2, 0, 0, tzinfo=UTC)
GROUP_HINT = "candidate:0123456789abcdefabcd"
RECEIPT_NO = "20260501000002"


def _action(*, factor: str = "0.5") -> CorporateActionRecord:
    return CorporateActionRecord(
        symbol="005930",
        action_type="stock_dividend",
        event_id="reviewed:0123456789abcdefabcd",
        revision=1,
        effective_at=EFFECTIVE_AT,
        announced_at=datetime(2026, 5, 1, tzinfo=UTC),
        known_at=REVIEWED_AT,
        price_factor=Decimal(factor),
        volume_factor=Decimal("2"),
        status="confirmed",
        source="dart-reviewed",
        rule_version="manual-review-2026.1",
    )


def _evidence(*, receipt_no: str = RECEIPT_NO) -> CorporateActionApprovalEvidence:
    return CorporateActionApprovalEvidence(
        group_hint=GROUP_HINT,
        receipt_no=receipt_no,
        filing_evidence_url=(f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}"),
        exchange_evidence_url="https://kind.krx.co.kr/example?event=123",
        reviewed_by="admin-api",
        reviewed_at=REVIEWED_AT,
    )


def test_approval_repository_is_atomic_idempotent_and_assigns_revisions(tmp_path):
    sessions = create_session_factory(f"sqlite:///{tmp_path / 'approvals.db'}")
    Base.metadata.create_all(sessions.kw["bind"])
    with sessions.begin() as session:
        session.add(StockModel(symbol="005930", name="Samsung", market="KOSPI"))
    repository = SqlAlchemyCorporateActionApprovalRepository(sessions)

    first = repository.approve(_action(), _evidence())
    replay = repository.approve(_action(), _evidence())
    revised = repository.approve(
        _action(factor="0.4"),
        _evidence(receipt_no="20260515000003"),
    )

    assert first.created is True
    assert replay.created is False
    assert replay.action == first.action
    assert revised.created is True
    assert revised.action.revision == 2
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(CorporateActionApprovalModel)) == 2


class _CandidateService:
    def __init__(self, *, include_group: bool = True, factors: bool = True) -> None:
        self.include_group = include_group
        self.factors = factors
        self.calls = 0

    def preview(self, source: str, symbol: str, **_: object) -> dict[str, object]:
        self.calls += 1
        candidate = {
            "source": source,
            "symbol": symbol,
            "receipt_no": RECEIPT_NO,
            "action_type": "stock_dividend",
            "filed_on": date(2026, 5, 1),
            "proposed_price_factor": Decimal("0.5") if self.factors else None,
            "proposed_volume_factor": Decimal("2") if self.factors else None,
            "evidence_url": (f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={RECEIPT_NO}"),
        }
        group = {"group_hint": GROUP_HINT, "receipt_nos": (RECEIPT_NO,)}
        return {
            "items": [candidate],
            "revision_groups": [group] if self.include_group else [],
            "data_as_of": REVIEWED_AT,
        }


class _ApprovalRepository:
    def __init__(self) -> None:
        self.action: CorporateActionRecord | None = None
        self.evidence: CorporateActionApprovalEvidence | None = None

    def approve(self, action, evidence) -> CorporateActionApprovalResult:
        self.action = action
        self.evidence = evidence
        return CorporateActionApprovalResult(action, "a" * 64, True)


def _approve(service: CorporateActionApprovalService, **overrides):
    values = {
        "source": "dart",
        "symbol": "005930",
        "start": date(2026, 1, 1),
        "end": date(2026, 12, 31),
        "group_hint": GROUP_HINT,
        "receipt_no": RECEIPT_NO,
        "effective_at": EFFECTIVE_AT,
        "exchange_evidence_url": "https://kind.krx.co.kr/example?event=123",
        "confirmation": "CONFIRM_CORPORATE_ACTION",
    }
    values.update(overrides)
    return service.approve(**values)


def test_approval_service_refetches_candidate_and_uses_review_time_as_known_at():
    candidates = _CandidateService()
    repository = _ApprovalRepository()
    service = CorporateActionApprovalService(
        repository,
        candidates,
        enabled=True,
        clock=lambda: REVIEWED_AT,
    )

    result = _approve(service)

    assert candidates.calls == 1
    assert result["known_at_policy"] == "approval_time"
    assert repository.action is not None
    assert repository.action.known_at == REVIEWED_AT
    assert repository.action.price_factor == Decimal("0.5")
    assert repository.evidence is not None
    assert repository.evidence.reviewed_at == REVIEWED_AT
    status = service.status()
    assert status["exchange_verification"]["automatic_effective_date_lookup"] is False
    assert status["exchange_verification"]["screen_scraping_allowed"] is False


def test_approval_service_fails_closed_for_disabled_or_changed_candidate():
    disabled = CorporateActionApprovalService(None, _CandidateService(), enabled=False)
    with pytest.raises(CorporateActionApprovalUnavailableError):
        _approve(disabled)

    changed = CorporateActionApprovalService(
        _ApprovalRepository(), _CandidateService(include_group=False), enabled=True
    )
    with pytest.raises(ValueError, match="changed during approval"):
        _approve(changed)


@pytest.mark.parametrize(
    "url",
    [
        "http://kind.krx.co.kr/example",
        "https://kind.krx.co.kr.evil.example/event",
        "https://user:pass@kind.krx.co.kr/event",
        "https://kind.krx.co.kr:444/event",
        "https://kind.krx.co.kr/event#unverifiable-fragment",
        "https://kind.krx.co.kr:invalid/event",
    ],
)
def test_approval_service_rejects_untrusted_exchange_evidence(url):
    service = CorporateActionApprovalService(
        _ApprovalRepository(), _CandidateService(), enabled=True
    )
    with pytest.raises(ValueError, match="approved HTTPS host"):
        _approve(service, exchange_evidence_url=url)


def test_approval_settings_require_persistence_admin_and_dart_keys():
    with pytest.raises(ValueError, match="PERSISTENCE_ENABLED"):
        Settings(_env_file=None, corporate_action_approval_enabled=True)
    with pytest.raises(ValueError, match="ADMIN_API_KEY"):
        Settings(
            _env_file=None,
            corporate_action_approval_enabled=True,
            persistence_enabled=True,
            admin_api_key="",
        )
    settings = Settings(
        _env_file=None,
        corporate_action_approval_enabled=True,
        persistence_enabled=True,
        admin_api_key="admin-secret",
        dart_api_key="dart-secret",
    )
    assert settings.corporate_action_approval_enabled is True


class _ApprovalApiService:
    def status(self) -> dict[str, object]:
        return {"enabled": False, "available": False}

    def approve(self, *args, **kwargs) -> dict[str, object]:
        return {"created": True, "symbol": args[1]}


def test_approval_api_is_admin_only_and_validates_confirmation():
    settings = Settings(_env_file=None, admin_api_key="test-admin-secret")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_corporate_action_approval_service] = lambda: _ApprovalApiService()
    client = TestClient(app)
    path = "/api/v1/admin/corporate-actions/approvals/dart/005930"
    payload = {
        "start": "2026-01-01",
        "end": "2026-12-31",
        "group_hint": GROUP_HINT,
        "receipt_no": RECEIPT_NO,
        "effective_at": EFFECTIVE_AT.isoformat(),
        "exchange_evidence_url": "https://kind.krx.co.kr/example",
        "confirmation": "CONFIRM_CORPORATE_ACTION",
    }
    try:
        assert client.get("/api/v1/admin/corporate-actions/approvals").status_code == 401
        assert client.post(path, json=payload).status_code == 401
        headers = {"X-Admin-Key": "test-admin-secret"}
        assert (
            client.get("/api/v1/admin/corporate-actions/approvals", headers=headers).status_code
            == 200
        )
        assert client.post(path, json=payload, headers=headers).status_code == 200
        payload["confirmation"] = "yes"
        assert client.post(path, json=payload, headers=headers).status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_corporate_action_approval_service, None)
