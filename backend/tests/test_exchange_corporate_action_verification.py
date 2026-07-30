from dataclasses import replace
from datetime import UTC, datetime

import pytest

from app.corporate_actions.exchange_verification import (
    DTCC_ASSET_SERVICING,
    KRX_MARKET_EVENT_EOD,
    KRX_OPEN_API,
    NASDAQ_DAILY_LIST,
    NYSE_MARKET_EVENT_FEED,
    SEC_EDGAR_DISCLOSURES,
    CorporateActionExchangeVerificationService,
    ExchangeVerificationMetadata,
    ExchangeVerificationResult,
    ExchangeVerificationSourceNotFoundError,
    ExchangeVerificationUnavailableError,
)


EFFECTIVE_AT = datetime(2026, 6, 2, tzinfo=UTC)


class _VerificationProvider:
    def __init__(
        self,
        metadata: ExchangeVerificationMetadata,
        *,
        mismatch: bool = False,
        evidence_url: str = "https://example.com/evidence/123",
    ):
        self.metadata = metadata
        self.mismatch = mismatch
        self.evidence_url = evidence_url

    def verify_effective_date(
        self,
        symbol: str,
        action_type: str,
        *,
        effective_at: datetime,
    ) -> ExchangeVerificationResult:
        return ExchangeVerificationResult(
            source=self.metadata.name,
            symbol="WRONG" if self.mismatch else symbol,
            action_type=action_type,
            requested_effective_at=effective_at,
            matched_effective_at=effective_at,
            exact_match=True,
            evidence_id="KRX-EOD-20260602-005930",
            evidence_url=self.evidence_url,
            fetched_at=datetime(2026, 7, 20, tzinfo=UTC),
        )


def _verified_metadata() -> ExchangeVerificationMetadata:
    return ExchangeVerificationMetadata(
        name="licensed-test-feed",
        authority="Test Exchange",
        markets=("KR",),
        access_mode="licensed_reference_feed",
        integration_status="verified",
        corporate_action_data=True,
        effective_date_field_status="verified",
        requires_contract=True,
        verification_role="primary",
        coverage_notes="Test coverage",
        reference_url="https://example.com/provider-spec",
    )


def test_krx_catalog_does_not_claim_unavailable_open_api_support():
    status = CorporateActionExchangeVerificationService().status()

    assert status["structured_verification_available"] is False
    assert status["automatic_effective_date_lookup"] is False
    assert status["fallback_mode"] == "manual_krx_evidence_url"
    assert status["screen_scraping_allowed"] is False
    evaluated = {item["name"]: item for item in status["evaluated_sources"]}
    assert evaluated[KRX_OPEN_API.name]["corporate_action_data"] is False
    assert evaluated[KRX_OPEN_API.name]["effective_date_field_status"] == "absent"
    assert evaluated[KRX_MARKET_EVENT_EOD.name]["integration_status"] == ("requires_contract")
    assert evaluated[KRX_MARKET_EVENT_EOD.name]["effective_date_field_status"] == ("unverified")


def test_us_source_policy_keeps_sec_as_crosscheck_and_paid_feeds_unverified():
    status = CorporateActionExchangeVerificationService().status()
    evaluated = {item["name"]: item for item in status["evaluated_sources"]}

    nasdaq = evaluated[NASDAQ_DAILY_LIST.name]
    assert nasdaq["integration_status"] == "requires_contract"
    assert nasdaq["effective_date_field_status"] == "verified"
    assert nasdaq["verification_role"] == "primary"
    assert "not a complete NYSE" in nasdaq["coverage_notes"]

    nyse = evaluated[NYSE_MARKET_EVENT_FEED.name]
    assert nyse["integration_status"] == "requires_contract"
    assert nyse["effective_date_field_status"] == "verified"
    assert "NYSE American" in nyse["coverage_notes"]

    dtcc = evaluated[DTCC_ASSET_SERVICING.name]
    assert dtcc["integration_status"] == "requires_contract"
    assert dtcc["effective_date_field_status"] == "unverified"

    sec = evaluated[SEC_EDGAR_DISCLOSURES.name]
    assert sec["verification_role"] == "crosscheck"
    assert sec["corporate_action_data"] is False
    assert sec["effective_date_field_status"] == "absent"


def test_verified_metadata_requires_an_authoritative_effective_date_field():
    with pytest.raises(ValueError, match="verified effective-date"):
        replace(
            _verified_metadata(),
            effective_date_field_status="unverified",
        )


def test_exchange_verification_registry_fails_closed_for_unknown_or_untrusted_source():
    service = CorporateActionExchangeVerificationService(
        [_VerificationProvider(KRX_MARKET_EVENT_EOD)]
    )

    with pytest.raises(ExchangeVerificationSourceNotFoundError):
        service.verify(
            "missing",
            "005930",
            "stock_dividend",
            effective_at=EFFECTIVE_AT,
        )
    with pytest.raises(ExchangeVerificationUnavailableError):
        service.verify(
            KRX_MARKET_EVENT_EOD.name,
            "005930",
            "stock_dividend",
            effective_at=EFFECTIVE_AT,
        )


def test_verified_exchange_provider_result_is_provenance_checked():
    metadata = _verified_metadata()
    service = CorporateActionExchangeVerificationService([_VerificationProvider(metadata)])

    result = service.verify(
        metadata.name,
        "005930",
        "stock_dividend",
        effective_at=EFFECTIVE_AT,
    )

    assert result.exact_match is True
    assert service.status()["structured_verification_available"] is True

    mismatch = CorporateActionExchangeVerificationService(
        [_VerificationProvider(metadata, mismatch=True)]
    )
    with pytest.raises(ValueError, match="mismatched provenance"):
        mismatch.verify(
            metadata.name,
            "005930",
            "stock_dividend",
            effective_at=EFFECTIVE_AT,
        )


def test_exchange_verification_rejects_naive_requested_timestamp():
    metadata = _verified_metadata()
    service = CorporateActionExchangeVerificationService([_VerificationProvider(metadata)])
    with pytest.raises(ValueError, match="timezone-aware"):
        service.verify(
            metadata.name,
            "005930",
            "stock_dividend",
            effective_at=datetime(2026, 6, 2),
        )


@pytest.mark.parametrize(
    "evidence_url",
    [
        "https://evil.example/evidence/123",
        "https://user:pass@example.com/evidence/123",
        "https://example.com:444/evidence/123",
        "https://example.com/evidence/123#fragment",
        "https://example.com:invalid/evidence/123",
    ],
)
def test_exchange_verification_rejects_non_authoritative_evidence_url(evidence_url):
    metadata = _verified_metadata()
    service = CorporateActionExchangeVerificationService(
        [_VerificationProvider(metadata, evidence_url=evidence_url)]
    )

    with pytest.raises(ValueError, match="invalid evidence"):
        service.verify(
            metadata.name,
            "005930",
            "stock_dividend",
            effective_at=EFFECTIVE_AT,
        )
