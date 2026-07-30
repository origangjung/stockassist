import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlsplit


INTEGRATION_STATUSES = frozenset({"not_available", "requires_contract", "verified", "disabled"})
EFFECTIVE_DATE_FIELD_STATUSES = frozenset({"absent", "unverified", "verified"})
VERIFICATION_ROLES = frozenset({"primary", "crosscheck", "not_suitable"})


def _is_authoritative_https_url(value: str, *, expected_host: str | None = None) -> bool:
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and (expected_host is None or parsed.hostname == expected_host)
        and parsed.username is None
        and parsed.password is None
        and port in (None, 443)
        and not parsed.fragment
    )


class ExchangeVerificationSourceNotFoundError(LookupError):
    pass


class ExchangeVerificationUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExchangeVerificationMetadata:
    name: str
    authority: str
    markets: tuple[str, ...]
    access_mode: str
    integration_status: str
    corporate_action_data: bool
    effective_date_field_status: str
    requires_contract: bool
    verification_role: str
    coverage_notes: str
    reference_url: str

    def __post_init__(self) -> None:
        if (
            not re.fullmatch(r"[a-z0-9_-]{1,40}", self.name)
            or not self.authority.strip()
            or not self.markets
            or any(not re.fullmatch(r"[A-Z]{2,8}", item) for item in self.markets)
            or self.integration_status not in INTEGRATION_STATUSES
            or self.effective_date_field_status not in EFFECTIVE_DATE_FIELD_STATUSES
            or self.verification_role not in VERIFICATION_ROLES
            or not self.coverage_notes.strip()
            or not _is_authoritative_https_url(self.reference_url)
        ):
            raise ValueError("Invalid exchange verification source metadata")
        if self.integration_status == "verified" and (
            not self.corporate_action_data or self.effective_date_field_status != "verified"
        ):
            raise ValueError("Verified exchange source requires a verified effective-date field")


@dataclass(frozen=True)
class ExchangeVerificationResult:
    source: str
    symbol: str
    action_type: str
    requested_effective_at: datetime
    matched_effective_at: datetime
    exact_match: bool
    evidence_id: str
    evidence_url: str
    fetched_at: datetime


class ExchangeVerificationProvider(Protocol):
    metadata: ExchangeVerificationMetadata

    def verify_effective_date(
        self,
        symbol: str,
        action_type: str,
        *,
        effective_at: datetime,
    ) -> ExchangeVerificationResult: ...


KRX_OPEN_API = ExchangeVerificationMetadata(
    name="krx-open-api",
    authority="Korea Exchange",
    markets=("KR",),
    access_mode="approved_open_api",
    integration_status="not_available",
    corporate_action_data=False,
    effective_date_field_status="absent",
    requires_contract=False,
    verification_role="not_suitable",
    coverage_notes="KRX public catalog has no corporate-action effective-date API",
    reference_url=("https://openapi.krx.co.kr/contents/OPP/INFO/service/OPPINFO004.cmd"),
)

KRX_MARKET_EVENT_EOD = ExchangeVerificationMetadata(
    name="krx-market-event-eod",
    authority="Korea Exchange",
    markets=("KR",),
    access_mode="licensed_reference_feed",
    integration_status="requires_contract",
    corporate_action_data=True,
    effective_date_field_status="unverified",
    requires_contract=True,
    verification_role="primary",
    coverage_notes="KOSPI and KOSDAQ EOD market-event reference product",
    reference_url="https://openapi.krx.co.kr/contents/OPP/DATA/OPPDATA002.jsp",
)

NASDAQ_DAILY_LIST = ExchangeVerificationMetadata(
    name="nasdaq-daily-list",
    authority="Nasdaq",
    markets=("US",),
    access_mode="monthly_subscription",
    integration_status="requires_contract",
    corporate_action_data=True,
    effective_date_field_status="verified",
    requires_contract=True,
    verification_role="primary",
    coverage_notes="Nasdaq-listed securities; not a complete NYSE/NYSE American source",
    reference_url="https://nasdaqtrader.com/Trader.aspx?id=DailyListPD",
)

NYSE_MARKET_EVENT_FEED = ExchangeVerificationMetadata(
    name="nyse-market-event-feed",
    authority="New York Stock Exchange",
    markets=("US",),
    access_mode="licensed_api",
    integration_status="requires_contract",
    corporate_action_data=True,
    effective_date_field_status="verified",
    requires_contract=True,
    verification_role="primary",
    coverage_notes="NYSE, NYSE American, NYSE Arca and NYSE Texas listed securities",
    reference_url=("https://www.nyse.com/market-data/corporate-actions/market-event-feed"),
)

DTCC_ASSET_SERVICING = ExchangeVerificationMetadata(
    name="dtcc-asset-servicing",
    authority="Depository Trust & Clearing Corporation",
    markets=("US",),
    access_mode="licensed_asset_servicing",
    integration_status="requires_contract",
    corporate_action_data=True,
    effective_date_field_status="unverified",
    requires_contract=True,
    verification_role="primary",
    coverage_notes="Broad DTC-eligible securities; automation schema not publicly verified",
    reference_url="https://www.dtcc.com/about/businesses-and-subsidiaries/dtc.aspx",
)

SEC_EDGAR_DISCLOSURES = ExchangeVerificationMetadata(
    name="sec-edgar-disclosures",
    authority="U.S. Securities and Exchange Commission",
    markets=("US",),
    access_mode="public_disclosure_api",
    integration_status="not_available",
    corporate_action_data=False,
    effective_date_field_status="absent",
    requires_contract=False,
    verification_role="crosscheck",
    coverage_notes="Filing and XBRL evidence only; not a normalized factor or ex-date feed",
    reference_url=("https://www.sec.gov/search-filings/edgar-application-programming-interfaces"),
)

EXCHANGE_VERIFICATION_CANDIDATES = (
    KRX_OPEN_API,
    KRX_MARKET_EVENT_EOD,
    NASDAQ_DAILY_LIST,
    NYSE_MARKET_EVENT_FEED,
    DTCC_ASSET_SERVICING,
    SEC_EDGAR_DISCLOSURES,
)


class CorporateActionExchangeVerificationService:
    """Fail-closed registry for authoritative effective-date verification."""

    def __init__(
        self,
        providers: list[ExchangeVerificationProvider] | None = None,
        candidates: tuple[ExchangeVerificationMetadata, ...] = EXCHANGE_VERIFICATION_CANDIDATES,
    ) -> None:
        self._providers: dict[str, ExchangeVerificationProvider] = {}
        self._candidates = candidates
        for provider in providers or []:
            metadata = provider.metadata
            if metadata.name in self._providers:
                raise ValueError(f"Duplicate exchange verification source: {metadata.name}")
            self._providers[metadata.name] = provider

    def status(self) -> dict[str, object]:
        verified = [
            provider.metadata
            for provider in self._providers.values()
            if provider.metadata.integration_status == "verified"
        ]
        return {
            "structured_verification_available": bool(verified),
            "automatic_effective_date_lookup": bool(verified),
            "registered_sources": [
                asdict(provider.metadata)
                for provider in sorted(
                    self._providers.values(), key=lambda item: item.metadata.name
                )
            ],
            "evaluated_sources": [
                asdict(item) for item in sorted(self._candidates, key=lambda item: item.name)
            ],
            "fallback_mode": "manual_krx_evidence_url",
            "screen_scraping_allowed": False,
        }

    def verify(
        self,
        source: str,
        symbol: str,
        action_type: str,
        *,
        effective_at: datetime,
    ) -> ExchangeVerificationResult:
        self._require_aware(effective_at)
        provider = self._providers.get(source)
        if provider is None:
            raise ExchangeVerificationSourceNotFoundError(
                f"Unknown exchange verification source: {source}"
            )
        if provider.metadata.integration_status != "verified":
            raise ExchangeVerificationUnavailableError(
                f"Exchange verification source is not verified: {source}"
            )
        result = provider.verify_effective_date(
            symbol.strip().upper(),
            action_type,
            effective_at=effective_at,
        )
        self._validate_result(provider.metadata, result, symbol, action_type, effective_at)
        return result

    @classmethod
    def _validate_result(
        cls,
        metadata: ExchangeVerificationMetadata,
        result: ExchangeVerificationResult,
        symbol: str,
        action_type: str,
        effective_at: datetime,
    ) -> None:
        cls._require_aware(result.requested_effective_at)
        cls._require_aware(result.matched_effective_at)
        cls._require_aware(result.fetched_at)
        if (
            result.source != metadata.name
            or result.symbol != symbol.strip().upper()
            or result.action_type != action_type
            or result.requested_effective_at != effective_at
        ):
            raise ValueError("Exchange verification result has mismatched provenance")
        if result.exact_match != (result.matched_effective_at == effective_at):
            raise ValueError("Exchange verification match flag is inconsistent")
        reference_host = urlsplit(metadata.reference_url).hostname
        if (
            not result.evidence_id.strip()
            or reference_host is None
            or not _is_authoritative_https_url(
                result.evidence_url,
                expected_host=reference_host,
            )
        ):
            raise ValueError("Exchange verification result has invalid evidence")

    @staticmethod
    def _require_aware(value: datetime) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Exchange verification timestamps must be timezone-aware")
