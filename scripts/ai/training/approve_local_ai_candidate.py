"""검증을 통과한 로컬 AI 후보를 명시적 버전 승인 후 원자적으로 활성화한다."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = (ROOT / "artifacts").resolve()
sys.path.insert(0, str(ROOT / "backend"))

from app.local_ai.contracts import ModelName  # noqa: E402
from app.local_ai.model import LocalLogisticModel  # noqa: E402


def parse_args() -> argparse.Namespace:
    """`parse_args`은(는) 원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--approve-version", required=True)
    parser.add_argument("--operating-dir", type=Path, default=ARTIFACT_ROOT / "local-ai")
    return parser.parse_args()


def safe_artifact_directory(path: Path) -> Path:
    """`safe_artifact_directory`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    resolved = path.expanduser().resolve()
    if resolved == ARTIFACT_ROOT or not resolved.is_relative_to(ARTIFACT_ROOT):
        raise ValueError("artifact directory must stay below artifacts")
    return resolved


def approve(
    candidate_dir: Path,
    operating_dir: Path,
    agent: ModelName,
    approved_version: str,
) -> str:
    """`approve`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    summary_path = candidate_dir / "validation-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    item = (summary.get("agents") or {}).get(agent) or {}
    model_info = item.get("candidate_model") or {}
    if item.get("status") != "validated" or item.get("promotion_ready") is not True:
        raise ValueError("candidate did not pass the promotion gate")
    if item.get("custom_feature_schema"):
        raise ValueError("custom feature candidates require a runtime adapter before promotion")
    if model_info.get("model_version") != approved_version:
        raise ValueError("approved version does not match the validated candidate")
    source = (candidate_dir / str(model_info.get("path"))).resolve()
    if not source.is_relative_to(candidate_dir) or source.is_symlink():
        raise ValueError("candidate model path is unsafe")
    model = LocalLogisticModel.load(source, expected_agent=agent)
    if model.artifact.model_version != approved_version:
        raise ValueError("candidate artifact version mismatch")
    operating_dir.mkdir(parents=True, exist_ok=True)
    target = operating_dir / f"{agent}.json"
    history = ARTIFACT_ROOT / "local-ai-history"
    history.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        current = LocalLogisticModel.load(target, expected_agent=agent)
        shutil.copy2(target, history / f"{agent}-{current.artifact.model_version}.json")
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, target)
    return approved_version


def main() -> int:
    """`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."""

    args = parse_args()
    candidate_dir = safe_artifact_directory(args.candidate_dir)
    operating_dir = safe_artifact_directory(args.operating_dir)
    version = approve(candidate_dir, operating_dir, args.agent, args.approve_version)
    print(json.dumps({"activated": args.agent, "model_version": version}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
