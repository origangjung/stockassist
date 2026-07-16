from decimal import Decimal

from app.ai_reports.signals import derive_reference_signal


def test_reference_signal_requires_calculated_score_and_prediction():
    result = derive_reference_signal(None, None, [])

    assert result.signal == "data_insufficient"
    assert result.strength == 0


def test_reference_signal_distinguishes_positive_neutral_and_defensive_consensus():
    positive = derive_reference_signal(
        {"overall_score": 68, "coverage_ratio": 0.3},
        {"rise_probability": Decimal("0.70")},
        [],
    )
    neutral = derive_reference_signal(
        {"overall_score": 72, "coverage_ratio": 0.3},
        {"rise_probability": Decimal("0.25")},
        [],
    )
    defensive = derive_reference_signal(
        {"overall_score": 32, "coverage_ratio": 0.3},
        {"rise_probability": Decimal("0.30")},
        [],
    )

    assert positive.signal == "positive_watch"
    assert neutral.signal == "neutral_watch"
    assert defensive.signal == "defensive_watch"


def test_market_warning_overrides_directional_signal():
    result = derive_reference_signal(
        {"overall_score": 90},
        {"rise_probability": Decimal("0.90")},
        [{"warning_type": "investment_warning"}],
    )

    assert result.signal == "risk_aware"
    assert result.strength == 100
