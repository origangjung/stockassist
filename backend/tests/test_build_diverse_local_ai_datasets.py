from datetime import date

from scripts.ai.data.build_diverse_local_ai_datasets import _index, _latest, _recent_events


def test_latest_context_never_uses_future_or_same_day_when_strict():
    rows = [
        {"timestamp": "2026-01-01", "symbol": "AAPL", "value": "1"},
        {"timestamp": "2026-01-03", "symbol": "AAPL", "value": "3"},
    ]
    index = _index(rows)

    normal = _latest(index, "AAPL", date(2026, 1, 3), maximum_age_days=5)
    strict = _latest(
        index,
        "AAPL",
        date(2026, 1, 3),
        maximum_age_days=5,
        strictly_before=True,
    )

    assert normal["value"] == "3"
    assert strict["value"] == "1"


def test_recent_events_exclude_target_day_events():
    rows = [
        {
            "timestamp": "2026-01-02T17:00:00",
            "symbol": "AAPL",
            "event_results": "1",
            "event_guidance_or_disclosure": "0",
            "event_material_agreement": "0",
            "event_acquisition": "0",
            "event_leadership": "0",
            "event_other": "0",
        },
        {
            "timestamp": "2026-01-03T09:00:00",
            "symbol": "AAPL",
            "event_results": "0",
            "event_guidance_or_disclosure": "1",
            "event_material_agreement": "0",
            "event_acquisition": "0",
            "event_leadership": "0",
            "event_other": "0",
        },
    ]

    values = _recent_events(_index(rows), "AAPL", date(2026, 1, 3))

    assert values["recent_sec_event_count_7d"] == 1
    assert values["recent_sec_results"] == 1
    assert values["recent_sec_guidance_or_disclosure"] == 0
