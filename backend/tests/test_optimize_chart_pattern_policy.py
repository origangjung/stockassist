from datetime import date

from scripts.ai.training.optimize_chart_pattern_policy import PatternEvent, _matches


def _event(direction: str = "upward") -> PatternEvent:
    return PatternEvent(
        date(2026, 1, 1),
        "AAPL",
        "hammer",
        direction,
        0.8,
        1.3,
        0.02 if direction == "upward" else -0.02,
        {5: 0.01},
        {5: 0.005},
    )


def test_pattern_filters_require_confirming_context():
    upward = _event()
    downward = _event("downward")

    assert _matches(upward, "volume_and_trend") is True
    assert _matches(downward, "volume_and_trend") is True
    assert _matches(upward, "high_rule_strength") is True


def test_pattern_filter_rejects_misaligned_trend():
    event = _event()
    misaligned = PatternEvent(
        event.timestamp,
        event.symbol,
        event.name,
        event.direction,
        event.confidence,
        event.volume_ratio,
        -0.01,
        event.absolute_returns,
        event.relative_returns,
    )

    assert _matches(misaligned, "trend_aligned") is False
