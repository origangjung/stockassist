import pytest

from app.local_ai.diagnostic import load_diagnostic_policy
from scripts.ai.training.evaluate_rule_diagnostic import evaluate, save_policy


def _row(index: int, label: int) -> dict[str, str]:
    favorable = label == 1
    return {
        "timestamp": f"2026-01-{index // 10 + 1:02d}",
        "symbol": f"S{index:03d}",
        "label": str(label),
        "investor_flow_available": "1",
        "investor_flow_probability": "0.1" if favorable else "0.9",
        "investor_flow_confidence": "0.8",
        "risk_available": "1",
        "risk_probability": "0.1" if favorable else "0.9",
        "risk_confidence": "0.8",
    }


def test_rule_diagnostic_evaluator_reports_directional_quality():
    rows = [_row(index, index % 2) for index in range(1_200)]

    report = evaluate(rows, ("investor_flow", "risk"), folds=4)

    assert report["approved"] is True
    assert report["metrics"]["accuracy"] == 1.0
    assert report["metrics"]["coverage"] == 1.0
    assert report["metrics"]["minimum_fold_balanced_accuracy"] == 1.0


def test_rule_diagnostic_policy_rejects_tampering(tmp_path):
    path = tmp_path / "diagnostic-policy.json"
    policy = evaluate(
        [_row(index, index % 2) for index in range(1_200)],
        ("investor_flow", "risk"),
        folds=4,
    )
    save_policy(path, policy)
    payload = path.read_text(encoding="utf-8").replace('"approved": true', '"approved": false')
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match="checksum"):
        load_diagnostic_policy(path)
