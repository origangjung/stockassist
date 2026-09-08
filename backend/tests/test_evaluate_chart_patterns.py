from scripts.ai.training.evaluate_chart_patterns import OutcomeStats, _wilson_interval


def test_pattern_outcome_stats_tracks_direction_and_baseline():
    stats = OutcomeStats()
    stats.add("upward", 0.02)
    stats.add("upward", -0.01)
    stats.add("downward", -0.03)
    stats.add("downward", 0.01)

    report = stats.report()

    assert report["samples"] == 4
    assert report["accuracy"] == 0.5
    assert report["baseline_accuracy"] == 0.5
    assert report["average_direction_adjusted_return"] == 0.0075


def test_wilson_interval_contains_observed_accuracy():
    lower, upper = _wilson_interval(60, 100)

    assert lower < 0.6 < upper
