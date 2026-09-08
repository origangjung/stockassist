"""횡단면 특성이 시간 누출 없이 안정적으로 계산되는지 검증한다."""

from app.local_ai.cross_section_features import (
    TARGET_RANK_COLUMN,
    enrich_cross_section_rows,
    relabel_cross_section_outcomes,
)


def _rows(*, future_shock: bool = False) -> list[dict[str, str]]:
    rows = []
    for day in range(8):
        for symbol_index in range(6):
            value = day + symbol_index
            if future_shock and day == 7:
                value *= 100
            rows.append(
                {
                    "timestamp": f"2026-08-{day + 1:02d}",
                    "symbol": f"S{symbol_index}",
                    "feature": str(value),
                    "label": str(symbol_index % 2),
                }
            )
    return rows


def test_cross_section_features_are_bounded_sorted_and_complete():
    enriched, names = enrich_cross_section_rows(_rows(), ("feature",))

    assert names == (
        "feature_cross_section_rank",
        "feature_cross_section_zscore",
    )
    assert len(enriched) == 48
    assert all(0 < float(row[names[0]]) <= 1 for row in enriched)
    assert [(row["timestamp"], row["symbol"]) for row in enriched] == sorted(
        (row["timestamp"], row["symbol"]) for row in enriched
    )


def test_future_cross_section_changes_do_not_rewrite_past_features():
    original, _names = enrich_cross_section_rows(_rows(), ("feature",))
    shocked, _names = enrich_cross_section_rows(_rows(future_shock=True), ("feature",))

    assert [row for row in original if row["timestamp"] < "2026-08-08"] == [
        row for row in shocked if row["timestamp"] < "2026-08-08"
    ]


def test_cross_section_target_keeps_only_top_and_bottom_tails():
    rows = [
        {
            "timestamp": "2026-08-01",
            "symbol": f"S{index}",
            "future_excess_return": str(index / 100),
            "feature": str(index),
            "label": "0",
        }
        for index in range(8)
    ]

    relabeled = relabel_cross_section_outcomes(rows, tail_fraction=0.25)

    assert [row["symbol"] for row in relabeled] == ["S0", "S1", "S6", "S7"]
    assert [row["label"] for row in relabeled] == [0, 0, 1, 1]
    assert float(relabeled[0][TARGET_RANK_COLUMN]) == 0.0
    assert float(relabeled[-1][TARGET_RANK_COLUMN]) == 1.0
    assert all(
        row["label_basis"] == "cross_section_future_excess_return_tail"
        for row in relabeled
    )


def test_cross_section_target_rejects_invalid_configuration():
    import pytest

    with pytest.raises(ValueError, match="tail fraction"):
        relabel_cross_section_outcomes([], tail_fraction=0.5)
