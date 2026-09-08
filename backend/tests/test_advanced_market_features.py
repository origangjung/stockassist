"""고급 기술 후보 피처가 미래값을 보지 않고 유한한 값을 만드는지 검증한다."""

from datetime import date, timedelta

from app.local_ai.advanced_market_features import (
    ADVANCED_TECHNICAL_FEATURES,
    enrich_advanced_technical_rows,
)


def _rows(*, future_shock: bool = False) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    start = date(2024, 1, 1)
    for index in range(330):
        for symbol_index, symbol in enumerate(("AAA", "BBB", "CCC")):
            close = 100 + symbol_index * 12 + index * (0.08 + symbol_index * 0.01)
            close += ((index + symbol_index) % 9 - 4) * 0.17
            if future_shock and index > 300:
                close *= 1.0 + symbol_index * 0.3
            rows.append(
                {
                    "timestamp": f"{start + timedelta(days=index)}T00:00:00+00:00",
                    "symbol": symbol,
                    "close_price": str(close),
                    "return_5d": str((index % 13 - 6) / 100),
                    "volatility_20": str(0.01 + (index % 7) / 1000),
                    "label": str(index % 2),
                }
            )
    return rows


def test_advanced_features_are_complete_sorted_and_keep_labels():
    enriched = enrich_advanced_technical_rows(_rows())

    assert enriched
    assert list(ADVANCED_TECHNICAL_FEATURES) == [
        name for name in enriched[0] if name in ADVANCED_TECHNICAL_FEATURES
    ]
    assert [(row["timestamp"], row["symbol"]) for row in enriched] == sorted(
        (row["timestamp"], row["symbol"]) for row in enriched
    )
    assert {row["label"] for row in enriched} == {"0", "1"}
    assert all(0 < float(row["return_5d_cross_section_rank"]) <= 1 for row in enriched)


def test_future_price_changes_do_not_rewrite_past_features():
    original = enrich_advanced_technical_rows(_rows())
    shocked = enrich_advanced_technical_rows(_rows(future_shock=True))
    cutoff = "2024-10-27T00:00:00+00:00"
    original_past = [row for row in original if row["timestamp"] <= cutoff]
    shocked_past = [row for row in shocked if row["timestamp"] <= cutoff]

    assert original_past == shocked_past
