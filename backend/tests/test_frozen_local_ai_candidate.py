"""Verify frozen challenger evaluation on strictly newer labeled rows."""

from datetime import date
from pathlib import Path

import numpy as np

from app.local_ai.model import LocalLogisticModel, LocalModelArtifact
from scripts.ai.training.evaluate_frozen_local_ai_candidate import (
    build_report,
    load_forward_rows,
)


def model(version: str, coefficient: float) -> LocalLogisticModel:
    """Build a minimal in-memory risk model for forward comparison tests."""

    return LocalLogisticModel(
        LocalModelArtifact(
            schema_version=2,
            agent="risk",
            model_version=version,
            feature_names=["risk_feature"],
            means=[0.0],
            scales=[1.0],
            coefficients=[coefficient],
            intercept=0.0,
            metrics={"decision_threshold": 0.5},
            training_samples=200,
            trained_at="2026-08-20T00:00:00+00:00",
            content_sha256="",
        )
    )


def test_forward_rows_are_strictly_after_cutoff(tmp_path: Path) -> None:
    """Rows on the selection date stay excluded from forward evidence."""

    path = tmp_path / "risk.csv"
    path.write_text(
        "timestamp,symbol,risk_feature,label\n"
        "2026-08-20T13:00:00+09:00,AAPL,-1,0\n"
        "2026-08-21T13:00:00+09:00,AAPL,1,1\n",
        encoding="utf-8",
    )

    features, labels, timestamps, symbols = load_forward_rows(
        path,
        ("risk_feature",),
        date(2026, 8, 20),
    )

    assert features[:, 0].tolist() == [1.0]
    assert labels.tolist() == [1]
    assert timestamps == ["2026-08-21T13:00:00+09:00"]
    assert symbols == ["AAPL"]


def test_forward_report_waits_for_minimum_independent_data() -> None:
    """A challenger cannot become ready from a small forward sample."""

    report = build_report(
        model("local-risk-aaaaaaaaaaaa", 2.0),
        model("local-risk-bbbbbbbbbbbb", 0.0),
        np.asarray([[-1.0], [1.0]]),
        np.asarray([0, 1]),
        ["2026-08-21", "2026-08-22"],
        ["AAPL", "MSFT"],
        cutoff=date(2026, 8, 20),
        minimum_rows=200,
        minimum_timestamps=5,
    )

    assert report["status"] == "awaiting_data"
    assert report["promotion_ready"] is False
    assert "rows_below_minimum" in report["reasons"]


def test_forward_report_requires_candidate_to_beat_champion() -> None:
    """Enough clean evidence can mark only a genuinely better frozen challenger ready."""

    values = np.linspace(-2.0, 2.0, 200)
    features = values.reshape(-1, 1)
    labels = (values >= 0.0).astype(np.int8)
    timestamps = [f"2026-09-{index // 40 + 1:02d}" for index in range(200)]
    symbols = [f"S{index % 20}" for index in range(200)]

    report = build_report(
        model("local-risk-aaaaaaaaaaaa", 5.0),
        model("local-risk-bbbbbbbbbbbb", 0.0),
        features,
        labels,
        timestamps,
        symbols,
        cutoff=date(2026, 8, 20),
        minimum_rows=200,
        minimum_timestamps=5,
    )

    assert report["status"] == "evaluated"
    assert report["candidate_metrics"]["accuracy"] == 1.0
    assert report["accuracy_delta"] > 0.0
    assert report["promotion_ready"] is True
    assert report["automatic_promotion"] is False
