"""준비된 로컬 AI 데이터만 중첩 시간 검증하고 운영 모델은 변경하지 않는다."""

import argparse
import csv
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
DATASET_ROOT = (ROOT / "datasets").resolve()
ARTIFACT_ROOT = (ROOT / "artifacts").resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.quality import MINIMUM_VALIDATION_SAMPLES  # noqa: E402
from app.local_ai.horizons import HORIZON_POLICIES, validate_horizon  # noqa: E402
from scripts.ai.training.audit_local_ai_datasets import MODEL_FEATURES, audit  # noqa: E402
from scripts.ai.training.walk_forward_local_agents import dataset_feature_names  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--agent", action="append", choices=sorted(MODEL_FEATURES))
    parser.add_argument("--use-all-safe-features", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--c-grid", default="0.01,0.1,1.0")
    parser.add_argument(
        "--class-weight-mode",
        choices=("both", "balanced", "unweighted"),
        default="both",
    )
    parser.add_argument("--max-training-timestamps", type=int)
    parser.add_argument("--fixed-decision-threshold", type=float)
    parser.add_argument("--min-absolute-outcome", type=float, default=0.0)
    parser.add_argument("--outcome-column", default="future_excess_return")
    return parser.parse_args()


def safe_directory(path: Path, root: Path, *, must_exist: bool) -> Path:
    """데이터와 결과 경로가 각각 Git 제외 루트 안에만 머물도록 제한한다."""

    resolved = path.expanduser().resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError(f"directory must stay below {root.name}")
    if must_exist and (not resolved.is_dir() or resolved.is_symlink()):
        raise ValueError("data directory is missing or unsafe")
    return resolved


def uses_custom_feature_schema(path: Path, agent: str) -> bool:
    """기본 운영 피처가 없는 지역 전용 데이터셋인지 판별한다."""

    available = set(dataset_feature_names(path))
    return not set(MODEL_FEATURES[agent]).issubset(available)


def dataset_horizon_days(path: Path, agent: str) -> int:
    """CSV에 기록된 단일 예측 기간을 읽고 기존 데이터만 5일로 해석한다."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if "horizon_days" not in (reader.fieldnames or []):
            return 5
        values = {int(row["horizon_days"]) for row in reader if row.get("horizon_days")}
    if len(values) != 1:
        raise ValueError("candidate dataset must contain exactly one prediction horizon")
    horizon = values.pop()
    if agent in HORIZON_POLICIES:
        return validate_horizon(agent, horizon)
    if not 1 <= horizon <= 252:
        raise ValueError("prediction horizon must be between 1 and 252 trading days")
    return horizon


def audit_dataset(
    path: Path, agent: str, *, use_all_safe_features: bool = False
) -> dict[str, object]:
    """기본 운영 피처로 후보 데이터의 구조와 시간 검증 준비도를 확인한다."""

    return audit(
        path,
        dataset_feature_names(path)
        if use_all_safe_features or uses_custom_feature_schema(path, agent)
        else MODEL_FEATURES[agent],
        minimum_validation_samples=MINIMUM_VALIDATION_SAMPLES[agent],
    )


def validation_command(
    data_dir: Path,
    output_dir: Path,
    agent: str,
    *,
    custom_schema: bool = False,
    c_grid: str = "0.01,0.1,1.0",
    class_weight_mode: str = "both",
    max_training_timestamps: int | None = None,
    fixed_decision_threshold: float | None = None,
    min_absolute_outcome: float = 0.0,
    outcome_column: str = "future_excess_return",
    prediction_horizon_days: int = 5,
) -> list[str]:
    """셸 문자열 결합 없이 중첩 시간 검증 명령 인자를 만든다."""

    command = [
        sys.executable,
        str(ROOT / "scripts" / "ai" / "training" / "nested_walk_forward_local_agent.py"),
        "--data-dir",
        str(data_dir),
        "--agent",
        agent,
        "--outer-splits",
        "5",
        "--inner-splits",
        "3",
        "--purge-timestamps",
        str(prediction_horizon_days),
        "--c-grid",
        c_grid,
        "--class-weight-mode",
        class_weight_mode,
        "--output",
        str(output_dir / f"{agent}-nested.json"),
        "--prediction-horizon-days",
        str(prediction_horizon_days),
    ]
    if custom_schema:
        command.append("--use-all-safe-features")
    if max_training_timestamps is not None:
        command.extend(["--max-training-timestamps", str(max_training_timestamps)])
    if fixed_decision_threshold is not None:
        command.extend(["--fixed-decision-threshold", str(fixed_decision_threshold)])
    if min_absolute_outcome:
        command.extend(["--min-absolute-outcome", str(min_absolute_outcome)])
        command.extend(["--outcome-column", outcome_column])
    return command


def selected_training_options(result: dict) -> tuple[float, bool]:
    """중첩 검증에서 가장 자주 선택된 규제 설정을 최종 후보 학습에 사용한다."""

    settings = result.get("selected_settings")
    if not isinstance(settings, dict) or not settings:
        raise ValueError("nested validation omitted selected settings")
    selected = max(settings, key=lambda key: (int(settings[key]), key))
    matched = re.fullmatch(r"c=([0-9.eE+-]+),(balanced|unweighted)", selected)
    if matched is None:
        raise ValueError("nested validation returned an invalid setting")
    return float(matched.group(1)), matched.group(2) == "balanced"


def candidate_training_command(
    data_dir: Path,
    output_dir: Path,
    agent: str,
    result: dict,
    *,
    max_training_timestamps: int | None = None,
    min_absolute_outcome: float = 0.0,
    outcome_column: str = "future_excess_return",
) -> list[str]:
    """`candidate_training_command`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    inverse_regularization, balanced = selected_training_options(result)
    metrics = result.get("metrics") or {}
    decision_threshold = float(metrics.get("decision_threshold", 0.5))
    prediction_horizon_days = int(result.get("prediction_horizon_days", 5))
    command = [
        sys.executable,
        str(ROOT / "scripts" / "ai" / "training" / "train_local_agents.py"),
        "--data-dir",
        str(data_dir),
        "--output-dir",
        str(output_dir / "models"),
        "--agent",
        agent,
        "--trainer",
        "sklearn",
        "--inverse-regularization",
        str(inverse_regularization),
        "--refit-full-data",
        "--decision-threshold",
        str(decision_threshold),
        "--prediction-horizon-days",
        str(prediction_horizon_days),
    ]
    if max_training_timestamps is not None:
        command.extend(["--max-training-timestamps", str(max_training_timestamps)])
    if min_absolute_outcome:
        command.extend(["--min-absolute-return", str(min_absolute_outcome)])
        command.extend(["--outcome-column", outcome_column])
    if balanced:
        command.append("--class-weight-balanced")
    return command


def save_json(path: Path, payload: object) -> None:
    """부분 보고서가 남지 않도록 같은 디렉터리에서 원자적으로 교체한다."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    data_dir = safe_directory(args.data_dir, DATASET_ROOT, must_exist=True)
    output_dir = safe_directory(args.output_dir, ARTIFACT_ROOT, must_exist=False)
    selected = args.agent or [
        name for name in MODEL_FEATURES if (data_dir / f"{name}.csv").is_file()
    ]
    if not selected:
        raise ValueError("no local AI datasets were found")

    summary: dict[str, object] = {
        "automatic_promotion": False,
        "data_dir": data_dir.name,
        "agents": {},
    }
    agents = summary["agents"]
    assert isinstance(agents, dict)
    for agent in selected:
        path = data_dir / f"{agent}.csv"
        if not path.is_file() or path.is_symlink():
            agents[agent] = {"status": "skipped", "reason": "dataset_missing"}
            continue
        report = audit_dataset(
            path,
            agent,
            use_all_safe_features=args.use_all_safe_features,
        )
        if report["training_readiness"] != "ready_for_candidate_training":
            agents[agent] = {
                "status": "skipped",
                "reason": "collect_more_data",
                "readiness": report,
            }
            continue
        custom_schema = args.use_all_safe_features or uses_custom_feature_schema(path, agent)
        prediction_horizon_days = dataset_horizon_days(path, agent)
        command = validation_command(
            data_dir,
            output_dir,
            agent,
            custom_schema=custom_schema,
            c_grid=args.c_grid,
            class_weight_mode=args.class_weight_mode,
            max_training_timestamps=args.max_training_timestamps,
            fixed_decision_threshold=args.fixed_decision_threshold,
            min_absolute_outcome=args.min_absolute_outcome,
            outcome_column=args.outcome_column,
            prediction_horizon_days=prediction_horizon_days,
        )
        if args.dry_run:
            agents[agent] = {
                "status": "planned",
                "rows": report["rows"],
                "custom_feature_schema": custom_schema,
                "prediction_horizon_days": prediction_horizon_days,
            }
            continue
        output_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(command, cwd=ROOT, check=True)
        result_path = output_dir / f"{agent}-nested.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        promotion_ready = bool(result.get("promotion_ready", False))
        candidate_model = None
        if promotion_ready and not custom_schema:
            subprocess.run(
                candidate_training_command(
                    data_dir,
                    output_dir,
                    agent,
                    result,
                    max_training_timestamps=args.max_training_timestamps,
                    min_absolute_outcome=args.min_absolute_outcome,
                    outcome_column=args.outcome_column,
                ),
                cwd=ROOT,
                check=True,
            )
            model_path = output_dir / "models" / f"{agent}.json"
            model_payload = json.loads(model_path.read_text(encoding="utf-8"))
            candidate_model = {
                "path": str(model_path.relative_to(output_dir)),
                "model_version": model_payload["model_version"],
                "content_sha256": model_payload["content_sha256"],
            }
        agents[agent] = {
            "status": "validated",
            "rows": report["rows"],
            "promotion_ready": promotion_ready,
            "promotion_reasons": result.get("promotion_reasons", []),
            "custom_feature_schema": custom_schema,
            "prediction_horizon_days": prediction_horizon_days,
            "candidate_model": candidate_model,
        }

    save_json(output_dir / "validation-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
