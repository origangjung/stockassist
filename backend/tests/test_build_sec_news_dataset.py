from scripts.ai.data.build_sec_news_local_ai_dataset import transform
from app.local_ai.sec_event_features import SEC_EVENT_FEATURES


def test_sec_events_are_transformed_to_news_candidate_rows():
    row = {
        "timestamp": "2026-08-01T16:30:00",
        "symbol": "aapl",
        **{name: "0.0" for name in SEC_EVENT_FEATURES},
        "future_return": "0.02",
        "benchmark_future_return": "0.01",
        "future_excess_return": "0.01",
        "label": "1",
        "unused_financial_feature": "9",
    }

    result = transform([row])

    assert result[0]["symbol"] == "AAPL"
    assert "unused_financial_feature" not in result[0]
    assert set(SEC_EVENT_FEATURES).issubset(result[0])
