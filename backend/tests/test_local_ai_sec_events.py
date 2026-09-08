from app.local_ai.sec_event_features import SEC_EVENT_FEATURES, extract_8k_events


def test_sec_events_extract_point_in_time_item_features():
    submissions = {
        "filings": {
            "recent": {
                "form": ["8-K", "10-Q", "8-K"],
                "accessionNumber": ["first", "quarter", "second"],
                "filingDate": ["2026-01-02", "2026-01-03", "2026-02-02"],
                "acceptanceDateTime": [
                    "20260102170000",
                    "20260103120000",
                    "20260202130000",
                ],
                "items": ["2.02, 7.01, 9.01", "", "1.01, 5.02"],
            }
        }
    }

    events = extract_8k_events(submissions)

    assert len(events) == 2
    assert set(SEC_EVENT_FEATURES).issubset(events[0])
    assert events[0]["event_results"] == 1
    assert events[0]["event_guidance_or_disclosure"] == 1
    assert events[0]["event_after_hours"] == 1
    assert events[1]["event_material_agreement"] == 1
    assert events[1]["event_leadership"] == 1
    assert events[1]["event_days_since_previous_log"] < events[0]["event_days_since_previous_log"]
