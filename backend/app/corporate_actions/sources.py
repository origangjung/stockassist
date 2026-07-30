from app.corporate_actions.contracts import CorporateActionSourceMetadata


DART_SOURCE = CorporateActionSourceMetadata(
    name="dart",
    markets=("KR",),
    trust_status="experimental",
    revision_strategy="receipt-reconciliation-required",
)

SEC_SOURCE = CorporateActionSourceMetadata(
    name="sec-edgar",
    markets=("US",),
    trust_status="experimental",
    revision_strategy="filing-candidate-only",
)

NASDAQ_DAILY_LIST_SOURCE = CorporateActionSourceMetadata(
    name="nasdaq-daily-list",
    markets=("US",),
    trust_status="experimental",
    revision_strategy="subscription-event-revision-required",
)

NYSE_MARKET_EVENT_FEED_SOURCE = CorporateActionSourceMetadata(
    name="nyse-market-event-feed",
    markets=("US",),
    trust_status="experimental",
    revision_strategy="licensed-api-event-revision-required",
)

DTCC_SOURCE = CorporateActionSourceMetadata(
    name="dtcc-asset-servicing",
    markets=("US",),
    trust_status="experimental",
    revision_strategy="licensed-event-revision-required",
)

SOURCE_CANDIDATES = (
    DART_SOURCE,
    SEC_SOURCE,
    NASDAQ_DAILY_LIST_SOURCE,
    NYSE_MARKET_EVENT_FEED_SOURCE,
    DTCC_SOURCE,
)

__all__ = [
    "DART_SOURCE",
    "DTCC_SOURCE",
    "NASDAQ_DAILY_LIST_SOURCE",
    "NYSE_MARKET_EVENT_FEED_SOURCE",
    "SEC_SOURCE",
    "SOURCE_CANDIDATES",
]
