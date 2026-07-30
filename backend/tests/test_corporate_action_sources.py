from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.corporate_actions.dart_mapping import DartCorporateActionMapper
from app.corporate_actions import CorporateActionSourceMetadata
from app.corporate_actions.sources import (
    DART_SOURCE,
    DTCC_SOURCE,
    NASDAQ_DAILY_LIST_SOURCE,
    NYSE_MARKET_EVENT_FEED_SOURCE,
    SEC_SOURCE,
)


def test_source_candidates_remain_experimental_until_reconciled():
    assert DART_SOURCE.markets == ("KR",)
    assert DART_SOURCE.trust_status == "experimental"
    assert SEC_SOURCE.markets == ("US",)
    assert SEC_SOURCE.trust_status == "experimental"
    assert SEC_SOURCE.revision_strategy == "filing-candidate-only"

    with pytest.raises(ValueError, match="source metadata"):
        CorporateActionSourceMetadata(
            name="Unsafe Source",
            markets=(),
            trust_status="verified",
            revision_strategy="",
        )


def test_us_factor_sources_remain_experimental_until_contract_validation():
    assert NASDAQ_DAILY_LIST_SOURCE.trust_status == "experimental"
    assert NASDAQ_DAILY_LIST_SOURCE.markets == ("US",)
    assert DTCC_SOURCE.trust_status == "experimental"
    assert DTCC_SOURCE.markets == ("US",)
    assert NYSE_MARKET_EVENT_FEED_SOURCE.trust_status == "experimental"
    assert NYSE_MARKET_EVENT_FEED_SOURCE.markets == ("US",)


def test_dart_bonus_issue_maps_reviewed_ratio_without_inferring_effective_date():
    effective_at = datetime(2026, 5, 7, tzinfo=UTC)
    action = DartCorporateActionMapper().map_bonus_issue(
        {
            "fric_nstk_ascnt_ps_ostk": "1.0",
            "fric_bddd": "2026-04-01",
            "fric_nstk_asstd": "20260430",
        },
        symbol="005930",
        event_id="dart:20260401000001:bonus",
        revision=1,
        known_at=datetime(2026, 4, 1, 9, tzinfo=UTC),
        effective_at=effective_at,
    )

    assert action.action_type == "stock_dividend"
    assert action.price_factor == Decimal("0.5")
    assert action.volume_factor == Decimal("2.0")
    assert action.effective_at is effective_at
    assert action.status == "announced"
    assert action.source == "dart"
    assert action.announced_at is not None
    assert getattr(action.announced_at.tzinfo, "key", None) == "Asia/Seoul"


def test_dart_capital_reduction_requires_proportional_consolidation_review():
    mapper = DartCorporateActionMapper()
    arguments = {
        "symbol": "005930",
        "event_id": "dart:20260401000002:capital-reduction",
        "revision": 1,
        "known_at": datetime(2026, 4, 1, tzinfo=UTC),
        "effective_at": datetime(2026, 5, 7, tzinfo=UTC),
    }
    row = {
        "bfcr_tisstk_ostk": "1,000,000",
        "atcr_tisstk_ostk": "100,000",
        "bddd": "20260401",
    }

    with pytest.raises(ValueError, match="reviewed proportional"):
        mapper.map_proportional_capital_reduction(
            row,
            proportional_share_consolidation=False,
            **arguments,
        )

    action = mapper.map_proportional_capital_reduction(
        row,
        proportional_share_consolidation=True,
        **arguments,
    )
    assert action.action_type == "reverse_split"
    assert action.price_factor == Decimal("10")
    assert action.volume_factor == Decimal("0.1")


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ({"fric_nstk_ascnt_ps_ostk": "-"}, "not numeric"),
        ({"fric_nstk_ascnt_ps_ostk": "0"}, "must be positive"),
        (
            {"fric_nstk_ascnt_ps_ostk": "1", "fric_bddd": "2026/04/01"},
            "YYYYMMDD",
        ),
    ],
)
def test_dart_mapper_rejects_ambiguous_fields(row, message):
    with pytest.raises(ValueError, match=message):
        DartCorporateActionMapper().map_bonus_issue(
            row,
            symbol="005930",
            event_id="event",
            revision=1,
            known_at=datetime(2026, 4, 1, tzinfo=UTC),
            effective_at=datetime(2026, 5, 7, tzinfo=UTC),
        )


def test_dart_mapper_rejects_naive_reconciled_effective_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        DartCorporateActionMapper().map_bonus_issue(
            {"fric_nstk_ascnt_ps_ostk": "1"},
            symbol="005930",
            event_id="event",
            revision=1,
            known_at=datetime(2026, 4, 1, tzinfo=UTC),
            effective_at=datetime(2026, 5, 7),
        )
