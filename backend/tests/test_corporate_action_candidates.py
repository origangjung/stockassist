from dataclasses import replace
from datetime import UTC, date, datetime
from io import BytesIO
from zipfile import ZipFile

import httpx2
import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_corporate_action_candidate_service
from app.config import Settings, get_settings
from app.corporate_actions.dart_candidates import DartCorporateActionCandidateProvider
from app.corporate_actions.reconciliation import CorporateActionRevisionReconciler
from app.main import app
from app.services.corporate_actions import CorporateActionCandidateService


def _dart_transport() -> httpx2.MockTransport:
    archive = BytesIO()
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "CORPCODE.xml",
            "<result><list><corp_code>00126380</corp_code>"
            "<stock_code>005930</stock_code></list></result>",
        )

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.params["crtfc_key"] == "dart-key"
        if request.url.path == "/api/corpCode.xml":
            return httpx2.Response(200, content=archive.getvalue())
        assert request.url.params["corp_code"] == "00126380"
        assert request.url.params["bgn_de"] == "20260101"
        assert request.url.params["end_de"] == "20261231"
        if request.url.path == "/api/list.json":
            assert request.url.params["last_reprt_at"] == "N"
            return httpx2.Response(
                200,
                json={
                    "status": "000",
                    "total_page": 1,
                    "list": [
                        {
                            "rcept_no": "20260401000001",
                            "report_nm": "주요사항보고서(무상증자결정)",
                            "rm": "유정",
                        },
                        {
                            "rcept_no": "20260501000002",
                            "report_nm": "주요사항보고서(감자결정)",
                            "rm": "유",
                        },
                    ],
                },
            )
        if request.url.path == "/api/fricDecsn.json":
            return httpx2.Response(
                200,
                json={
                    "status": "000",
                    "list": [
                        {
                            "rcept_no": "20260401000001",
                            "fric_nstk_ascnt_ps_ostk": "1.0",
                            "fric_bddd": "20260401",
                            "fric_nstk_asstd": "20260430",
                        }
                    ],
                },
            )
        assert request.url.path == "/api/crDecsn.json"
        return httpx2.Response(
            200,
            json={
                "status": "000",
                "list": [
                    {
                        "rcept_no": "20260501000002",
                        "bfcr_tisstk_ostk": "1,000,000",
                        "atcr_tisstk_ostk": "100,000",
                        "bddd": "20260501",
                        "cr_std": "20260601",
                    }
                ],
            },
        )

    return httpx2.MockTransport(handler)


def test_dart_candidate_provider_collects_read_only_bonus_and_reduction_evidence():
    provider = DartCorporateActionCandidateProvider.create(
        base_url="https://opendart.fss.or.kr/api",
        api_key="dart-key",
        transport=_dart_transport(),
    )
    try:
        result = provider.fetch_candidates(
            "005930",
            start=date(2026, 1, 1),
            end=date(2026, 12, 31),
            limit=10,
        )
    finally:
        provider.close()

    assert result.source == "dart"
    assert result.fetched_at.tzinfo is UTC
    assert [item.action_type for item in result.candidates] == [
        "reverse_split",
        "stock_dividend",
    ]
    reduction, bonus = result.candidates
    assert reduction.proposed_price_factor == 10
    assert "proportional_consolidation_evidence_required" in reduction.warnings
    assert bonus.proposed_price_factor == 0.5
    assert bonus.confirmation_ready is False
    assert bonus.superseded_hint is True
    assert bonus.report_name == "주요사항보고서(무상증자결정)"
    assert "later_correction_reported" in bonus.warnings
    assert bonus.evidence_url.endswith("rcpNo=20260401000001")


def test_reconciler_only_suggests_revision_order_and_requires_manual_confirmation():
    provider = DartCorporateActionCandidateProvider.create(
        base_url="https://opendart.fss.or.kr/api",
        api_key="dart-key",
        transport=_dart_transport(),
    )
    try:
        original = provider.fetch_candidates(
            "005930",
            start=date(2026, 1, 1),
            end=date(2026, 12, 31),
            limit=10,
        ).candidates[1]
    finally:
        provider.close()
    correction = replace(
        original,
        event_id="dart:20260415000003:bonus_issue",
        receipt_no="20260415000003",
        filed_on=date(2026, 4, 15),
        report_name="[기재정정] 주요사항보고서(무상증자결정)",
        remarks="유",
        correction_hint=True,
        superseded_hint=False,
    )

    groups = CorporateActionRevisionReconciler().propose((original, correction))

    assert len(groups) == 1
    assert groups[0].receipt_nos == ("20260401000001", "20260415000003")
    assert groups[0].suggested_revisions == (1, 2)
    assert groups[0].confidence == "likely_correction"
    assert groups[0].requires_manual_confirmation is True
    assert groups[0].persistence_allowed is False


def test_candidate_service_is_bounded_and_never_writes_or_confirms():
    provider = DartCorporateActionCandidateProvider.create(
        base_url="https://opendart.fss.or.kr/api",
        api_key="dart-key",
        transport=_dart_transport(),
    )
    service = CorporateActionCandidateService([provider])
    try:
        status = service.status()
        preview = service.preview(
            "dart",
            "005930",
            start=date(2026, 1, 1),
            end=date(2026, 12, 31),
            limit=10,
        )
        with pytest.raises(ValueError, match="366 days"):
            service.preview(
                "dart",
                "005930",
                start=date(2024, 1, 1),
                end=date(2026, 1, 1),
                limit=10,
            )
    finally:
        service.close()

    assert status["available"] is True
    assert status["read_only"] is True
    assert preview["count"] == 2
    assert preview["write_performed"] is False
    assert preview["automatic_confirmation"] is False
    assert preview["point_in_time_eligible"] is False
    assert len(preview["revision_groups"]) == 2

class _StubCandidateService:
    def status(self) -> dict[str, object]:
        return {
            "available": True,
            "sources": [],
            "read_only": True,
            "automatic_confirmation": False,
            "point_in_time_eligible": False,
            "max_range_days": 366,
            "max_candidates": 200,
        }

    def preview(self, source: str, symbol: str, **_: object) -> dict[str, object]:
        return {
            "source": source,
            "symbol": symbol,
            "items": [],
            "count": 0,
            "write_performed": False,
            "automatic_confirmation": False,
            "point_in_time_eligible": False,
            "data_as_of": datetime.now(UTC),
        }


def test_candidate_preview_endpoint_requires_admin_and_bounds_date_range():
    settings = Settings(_env_file=None, admin_api_key="test-admin-secret")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_corporate_action_candidate_service] = (
        lambda: _StubCandidateService()
    )
    client = TestClient(app)
    path = (
        "/api/v1/admin/corporate-actions/candidates/dart/005930"
        "?start=2026-01-01&end=2026-12-31&limit=100"
    )
    try:
        status_path = "/api/v1/admin/corporate-actions/candidates"
        assert client.get(status_path).status_code == 401
        status = client.get(
            status_path, headers={"X-Admin-Key": "test-admin-secret"}
        )
        assert status.status_code == 200
        assert status.json()["data"]["read_only"] is True
        assert client.get(path).status_code == 401
        accepted = client.get(path, headers={"X-Admin-Key": "test-admin-secret"})
        rejected = client.get(
            path.replace("limit=100", "limit=201"),
            headers={"X-Admin-Key": "test-admin-secret"},
        )

        assert accepted.status_code == 200
        assert accepted.json()["data"]["write_performed"] is False
        assert rejected.status_code == 422
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_corporate_action_candidate_service, None)
