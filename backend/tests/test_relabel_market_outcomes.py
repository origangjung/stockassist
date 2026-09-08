import csv

from scripts.ai.data.relabel_specialists_with_market_outcomes import (
    _outcome_index,
    relabel,
)


def _write(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_financial_relabel_uses_strictly_later_market_session(tmp_path):
    outcomes = {
        ("2026-01-02", "AAPL"): {
            "timestamp": "2026-01-02T13:00:00+09:00",
            "symbol": "AAPL",
            "future_return": "0.03",
            "benchmark_future_return": "0.01",
            "future_excess_return": "0.02",
        },
        ("2026-01-05", "AAPL"): {
            "timestamp": "2026-01-05T13:00:00+09:00",
            "symbol": "AAPL",
            "future_return": "-0.02",
            "benchmark_future_return": "0.01",
            "future_excess_return": "-0.03",
        },
    }
    source = tmp_path / "financial-source.csv"
    target = tmp_path / "financial.csv"
    _write(
        source,
        ["timestamp", "symbol", "feature", "label"],
        [{"timestamp": "2026-01-02", "symbol": "AAPL", "feature": "1", "label": "0"}],
    )

    report = relabel(
        "financial",
        source,
        target,
        outcomes,
        _outcome_index(outcomes),
    )

    with target.open("r", encoding="utf-8", newline="") as result:
        rows = list(csv.DictReader(result))
    assert report["matched_rows"] == 1
    assert rows[0]["outcome_start_timestamp"].startswith("2026-01-05")
    assert rows[0]["label"] == "0"


def test_all_directional_specialists_use_the_same_market_outcome_direction(tmp_path):
    outcome = {
        "timestamp": "2026-01-02T13:00:00+09:00",
        "symbol": "AAPL",
        "future_return": "-0.02",
        "benchmark_future_return": "0.01",
        "future_excess_return": "-0.03",
    }
    outcomes = {("2026-01-02", "AAPL"): outcome}
    source = tmp_path / "source.csv"
    _write(
        source,
        ["timestamp", "symbol", "feature", "label"],
        [{"timestamp": "2026-01-02", "symbol": "AAPL", "feature": "1", "label": "0"}],
    )

    labels = {}
    for agent in ("technical", "news", "investor_flow", "risk"):
        target = tmp_path / f"{agent}.csv"
        relabel(agent, source, target, outcomes, _outcome_index(outcomes))
        with target.open("r", encoding="utf-8", newline="") as result:
            labels[agent] = next(csv.DictReader(result))["label"]

    assert labels == {
        "technical": "0",
        "news": "0",
        "investor_flow": "0",
        "risk": "0",
    }
