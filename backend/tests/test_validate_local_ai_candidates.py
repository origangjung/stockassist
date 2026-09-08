from pathlib import Path

import pytest

from scripts.ai.training.validate_local_ai_candidates import (
    dataset_horizon_days,
    safe_directory,
    candidate_training_command,
    selected_training_options,
    uses_custom_feature_schema,
    validation_command,
)


def test_candidate_validation_paths_stay_under_ignored_roots(tmp_path):
    root = tmp_path / "datasets"
    data = root / "candidate"
    data.mkdir(parents=True)

    assert safe_directory(data, root.resolve(), must_exist=True) == data.resolve()
    with pytest.raises(ValueError, match="directory must stay"):
        safe_directory(tmp_path / "outside", root.resolve(), must_exist=False)


def test_candidate_validation_command_uses_argument_list(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.ai.training.validate_local_ai_candidates.ROOT", Path("C:/workspace")
    )

    command = validation_command(
        tmp_path / "datasets" / "candidate",
        tmp_path / "artifacts" / "candidate",
        "financial",
    )

    assert command[command.index("--agent") + 1] == "financial"
    assert command[command.index("--class-weight-mode") + 1] == "both"
    assert command[command.index("--output") + 1].endswith("financial-nested.json")
    assert all("secret" not in value.casefold() for value in command)


def test_candidate_validation_can_lock_unweighted_models(tmp_path):
    command = validation_command(
        tmp_path / "datasets" / "candidate",
        tmp_path / "artifacts" / "candidate",
        "risk",
        class_weight_mode="unweighted",
    )

    assert command[command.index("--class-weight-mode") + 1] == "unweighted"


def test_dataset_horizon_is_explicit_and_role_checked(tmp_path):
    data = tmp_path / "financial.csv"
    data.write_text(
        "timestamp,symbol,feature,horizon_days,label\n"
        "2026-01-01,AAPL,1,20,1\n",
        encoding="utf-8",
    )

    assert dataset_horizon_days(data, "financial") == 20
    command = validation_command(
        tmp_path,
        tmp_path / "output",
        "financial",
        prediction_horizon_days=20,
    )
    assert command[command.index("--prediction-horizon-days") + 1] == "20"
    assert command[command.index("--purge-timestamps") + 1] == "20"


def test_custom_schema_is_detected_and_passed_to_nested_validation(tmp_path):
    data = tmp_path / "investor_flow.csv"
    data.write_text(
        "timestamp,symbol,kis_feature,label\n2026-01-01,005930,1,0\n",
        encoding="utf-8",
    )

    assert uses_custom_feature_schema(data, "investor_flow") is True
    command = validation_command(
        tmp_path, tmp_path / "output", "investor_flow", custom_schema=True
    )
    assert "--use-all-safe-features" in command


def test_promotion_ready_settings_build_a_candidate_without_auto_activation(tmp_path):
    result = {
        "selected_settings": {"c=0.05,balanced": 4, "c=1,unweighted": 1},
        "metrics": {"decision_threshold": 0.57},
    }

    assert selected_training_options(result) == (0.05, True)
    command = candidate_training_command(
        tmp_path, tmp_path / "candidate", "financial", result
    )
    assert "--class-weight-balanced" in command
    assert command[command.index("--decision-threshold") + 1] == "0.57"
    assert str(tmp_path / "candidate" / "models") in command


def test_selective_candidate_options_are_shared_by_validation_and_training(tmp_path):
    result = {"selected_settings": {"c=0.1,unweighted": 5}}
    validation = validation_command(
        tmp_path,
        tmp_path / "validation",
        "technical",
        min_absolute_outcome=0.005,
        outcome_column="future_excess_return",
    )
    training = candidate_training_command(
        tmp_path,
        tmp_path / "candidate",
        "technical",
        result,
        min_absolute_outcome=0.005,
        outcome_column="future_excess_return",
    )

    assert validation[validation.index("--min-absolute-outcome") + 1] == "0.005"
    assert training[training.index("--min-absolute-return") + 1] == "0.005"
    assert training[training.index("--outcome-column") + 1] == "future_excess_return"
