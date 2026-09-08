import json

import pytest

from scripts.ai.training.approve_local_ai_candidate import approve


def test_candidate_approval_requires_gate_and_exact_version(tmp_path):
    candidate = tmp_path / "candidate"
    operating = tmp_path / "operating"
    candidate.mkdir()
    summary = {
        "agents": {
            "financial": {
                "status": "validated",
                "promotion_ready": True,
                "custom_feature_schema": False,
                "candidate_model": {
                    "path": "models/financial.json",
                    "model_version": "local-financial-123456789abc",
                },
            }
        }
    }
    (candidate / "validation-summary.json").write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(ValueError, match="approved version"):
        approve(candidate, operating, "financial", "local-financial-wrongversion")

    summary["agents"]["financial"]["promotion_ready"] = False
    (candidate / "validation-summary.json").write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(ValueError, match="promotion gate"):
        approve(candidate, operating, "financial", "local-financial-123456789abc")
