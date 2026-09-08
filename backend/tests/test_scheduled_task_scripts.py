"""Windows 예약 작업 등록 스크립트와 실행기 경로 계약을 검증한다."""

from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[2]
OPERATIONS = ROOT / "scripts" / "operations"


@pytest.mark.parametrize(
    ("registration_name", "runner_name"),
    [
        ("register_kis_realtime_validation_tasks.ps1", "run_kis_realtime_validation.ps1"),
        ("register_local_ai_collection_task.ps1", "run_local_ai_collection.ps1"),
        (
            "register_local_ai_candidate_validation_task.ps1",
            "run_local_ai_candidate_validation.ps1",
        ),
    ],
)
def test_scheduled_task_registration_uses_existing_runner(
    registration_name: str,
    runner_name: str,
) -> None:
    """등록 스크립트가 같은 운영 폴더의 실제 실행기를 사용해야 한다."""

    registration = OPERATIONS / registration_name
    runner = OPERATIONS / runner_name

    assert registration.is_file()
    assert runner.is_file()

    source = registration.read_text(encoding="utf-8-sig")
    declared_runner = re.search(
        r'Join-Path\s+\$PSScriptRoot\s+"([^"\r\n]+)"',
        source,
        flags=re.IGNORECASE,
    )

    assert declared_runner is not None
    assert declared_runner.group(1).replace("\\", "/") == runner_name
    assert 'New-ScheduledTaskAction -Execute $powerShell' in source
    assert "-WindowStyle Hidden" in source


@pytest.mark.parametrize(
    "runner_name",
    [
        "run_kis_realtime_validation.ps1",
        "run_local_ai_collection.ps1",
        "run_local_ai_candidate_validation.ps1",
    ],
)
def test_scheduled_runner_returns_explicit_exit_codes(runner_name: str) -> None:
    """예약 실행기는 모호한 PowerShell 예외 대신 숫자 종료 코드를 반환해야 한다."""

    source = (OPERATIONS / runner_name).read_text(encoding="utf-8-sig")

    assert "exit 0" in source
    assert re.search(r"exit\s+\$[A-Za-z][A-Za-z0-9]*ExitCode", source)


def test_candidate_schedule_runs_frozen_risk_forward_validation() -> None:
    """주간 후보 작업은 운영 모델을 교체하지 않고 고정 위험 후보도 평가해야 한다."""

    source = (OPERATIONS / "run_local_ai_candidate_validation.ps1").read_text(
        encoding="utf-8-sig"
    )

    assert "evaluate_frozen_local_ai_candidate.py" in source
    assert "enrich_local_ai_macro.py" in source
    assert 'Service = "collector"' in source
    assert 'Profile = "collection"' in source
    assert '"--entrypoint", "python", $service' in source
    assert "forward-risk-enriched/risk.csv" in source
    assert '"--cutoff-date", "2026-08-20"' in source
    assert '"--minimum-timestamps", "20"' in source
    assert "automatic_promotion=false" in source


def test_candidate_schedule_gates_earnings_regression_on_readiness() -> None:
    """실적 회귀는 안전한 준비 보고서가 통과된 주간 ML 작업에서만 실행해야 한다."""

    source = (OPERATIONS / "run_local_ai_candidate_validation.ps1").read_text(
        encoding="utf-8-sig"
    )

    assert "earnings-candidates\\readiness.json" in source
    assert '[IO.FileAttributes]::ReparsePoint' in source
    assert '$readinessFile.Length -le 1MB' in source
    assert '$earningsReadiness.status -eq "ready_for_validation"' in source
    assert "nested_walk_forward_technical_regression.py" in source
    assert "technical_earnings_expected_excess_return_ridge" in source
    assert "technical_earnings_base_expected_excess_return_ridge" in source
    assert '"--evaluation-subgroup-feature", "earnings_event_10d"' in source
    assert "assess_technical_earnings_promotion.py" in source
    assert '"--blas-threads", "1"' in source
    assert "technical-earnings/base-validation.json" in source
    assert "technical-earnings/nested-validation.json" in source
    assert "technical-earnings/promotion-assessment.json" in source


def test_collection_runner_streams_redacted_progress_to_its_log() -> None:
    """긴 수집이 중단돼도 완료 단계는 남고 민감한 출력은 기록되지 않아야 한다."""

    source = (OPERATIONS / "run_local_ai_collection.ps1").read_text(
        encoding="utf-8-sig"
    )

    assert "function Write-SanitizedLogLine" in source
    assert "& docker @arguments 2>&1 | ForEach-Object" in source
    assert "Write-SanitizedLogLine -Line $_ -Path $logPath" in source
    assert "redacted_sensitive_output=true" in source
    assert "$output = & docker" not in source
