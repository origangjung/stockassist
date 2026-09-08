[CmdletBinding()]
param([switch]$DryRun)

$ErrorActionPreference = "Stop"
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$logRoot = Join-Path $repoRoot "datasets\local-ai-incremental\task-logs"
$logPath = Join-Path $logRoot ("candidate-validation-{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))
$targets = @(
    @{
        Name = "incremental-specialists"
        Script = "scripts/ai/training/validate_local_ai_candidates.py"
        Arguments = @(
            "--data-dir", "/app/datasets/local-ai-incremental/labeled",
            "--output-dir", "/app/artifacts/local-ai-candidates/incremental"
        )
    },
    @{
        Name = "incremental-market"
        Script = "scripts/ai/training/validate_local_ai_candidates.py"
        Arguments = @(
            "--data-dir", "/app/datasets/local-ai-incremental/market",
            "--output-dir", "/app/artifacts/local-ai-candidates/incremental-market"
        )
    },
    @{
        Name = "kis-flow"
        Script = "scripts/ai/training/validate_local_ai_candidates.py"
        Arguments = @(
            "--data-dir", "/app/datasets/local-ai-incremental/kis-flow",
            "--output-dir", "/app/artifacts/local-ai-candidates/kis-flow"
        )
    },
    @{
        Name = "risk-macro-enrichment"
        Service = "collector"
        Profile = "collection"
        Script = "scripts/ai/data/enrich_local_ai_macro.py"
        Arguments = @(
            "--data-dir", "/app/datasets/local-ai-incremental/market",
            "--output-dir", "/app/datasets/local-ai-incremental/forward-risk-enriched"
        )
    },
    @{
        Name = "risk-forward"
        Script = "scripts/ai/training/evaluate_frozen_local_ai_candidate.py"
        Arguments = @(
            "--data", "/app/datasets/local-ai-incremental/forward-risk-enriched/risk.csv",
            "--candidate", "/app/artifacts/local-ai-candidates/risk-stability-20260828/candidate/models/risk.json",
            "--champion", "/app/artifacts/local-ai/risk.json",
            "--cutoff-date", "2026-08-20",
            "--minimum-rows", "1000",
            "--minimum-timestamps", "20",
            "--output", "/app/artifacts/local-ai-candidates/risk-stability-20260828/forward-validation.json"
        )
    }
)

New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$earningsReadinessPath = Join-Path $repoRoot "datasets\local-ai-incremental\earnings-candidates\readiness.json"
if (Test-Path -LiteralPath $earningsReadinessPath -PathType Leaf) {
    $readinessFile = Get-Item -LiteralPath $earningsReadinessPath -Force
    $isReparsePoint = ($readinessFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
    if (-not $isReparsePoint -and $readinessFile.Length -le 1MB) {
        try {
            $earningsReadiness = Get-Content -LiteralPath $earningsReadinessPath -Raw | ConvertFrom-Json
            if ($earningsReadiness.status -eq "ready_for_validation") {
                $earningsBaseArguments = @(
                    "--data", "/app/datasets/local-ai-incremental/earnings-candidates/technical.csv",
                    "--base-feature", "return_1d",
                    "--base-feature", "return_5d",
                    "--base-feature", "sma_5_gap",
                    "--base-feature", "sma_20_gap",
                    "--base-feature", "volatility_20",
                    "--base-feature", "volume_ratio",
                    "--base-feature", "rsi_14",
                    "--evaluation-subgroup-feature", "earnings_event_10d",
                    "--purge-timestamps", "10",
                    "--blas-threads", "1"
                )
                $targets += @(
                    @{
                        Name = "technical-earnings-base"
                        Script = "scripts/ai/training/nested_walk_forward_technical_regression.py"
                        Arguments = @(
                            $earningsBaseArguments
                            "--model-name", "technical_earnings_base_expected_excess_return_ridge",
                            "--output", "/app/artifacts/local-ai-candidates/technical-earnings/base-validation.json"
                        )
                    },
                    @{
                        Name = "technical-earnings-regression"
                        Script = "scripts/ai/training/nested_walk_forward_technical_regression.py"
                        Arguments = @(
                            $earningsBaseArguments
                            "--model-name", "technical_earnings_expected_excess_return_ridge",
                            "--candidate-extra-feature-set", "eps_surprise_signed_log,eps_surprise_positive,eps_yoy_growth_signed_log,eps_yoy_available,eps_beat_streak_scaled,earnings_age_log_scaled,earnings_event_3d,earnings_event_10d",
                            "--output", "/app/artifacts/local-ai-candidates/technical-earnings/nested-validation.json"
                        )
                    },
                    @{
                        Name = "technical-earnings-assessment"
                        Script = "scripts/ai/training/assess_technical_earnings_promotion.py"
                        Arguments = @(
                            "--base", "/app/artifacts/local-ai-candidates/technical-earnings/base-validation.json",
                            "--candidate", "/app/artifacts/local-ai-candidates/technical-earnings/nested-validation.json",
                            "--output", "/app/artifacts/local-ai-candidates/technical-earnings/promotion-assessment.json"
                        )
                    }
                )
            }
        }
        catch {
            Add-Content -LiteralPath $logPath -Value "earnings_readiness=invalid"
        }
    }
}

Push-Location $repoRoot
$runnerExitCode = 0
$failureStage = ""
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "docker cli unavailable"
    }
    Add-Content -LiteralPath $logPath -Value "started_at_utc=$((Get-Date).ToUniversalTime().ToString('o')) dry_run=$($DryRun.IsPresent)"
    foreach ($target in $targets) {
        $service = if ($target.ContainsKey("Service")) { $target.Service } else { "trainer" }
        $profile = if ($target.ContainsKey("Profile")) { $target.Profile } else { "training" }
        $arguments = @("compose", "--profile", $profile, "run", "--rm")
        if ($service -eq "collector") {
            # 외부 데이터 키와 네트워크는 수집 컨테이너에만 두고 trainer는 오프라인으로 유지한다.
            $arguments += @("--entrypoint", "python", $service, $target.Script)
        }
        else {
            $arguments += @($service, "python", $target.Script)
        }
        $arguments += $target.Arguments
        if ($DryRun) { $arguments += "--dry-run" }
        $previousErrorAction = $ErrorActionPreference
        try {
            $ErrorActionPreference = "Continue"
            $output = & docker @arguments 2>&1
            $exitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $previousErrorAction
        }
        foreach ($line in $output) {
            $text = [string]$line
            if ($text -match '(?i)(secret|token|api[_-]?key|authorization)\s*[:=]') {
                Add-Content -LiteralPath $logPath -Value "redacted_sensitive_output=true"
                continue
            }
            Add-Content -LiteralPath $logPath -Value $text
        }
        Add-Content -LiteralPath $logPath -Value "target=$($target.Name) exit_code=$exitCode"
        if ($exitCode -ne 0) {
            $runnerExitCode = $exitCode
            $failureStage = "validator"
            break
        }
    }
}
catch {
    $runnerExitCode = 3
    $failureStage = "runner"
    Add-Content -LiteralPath $logPath -Value "failure_stage=runner exit_code=3"
}
finally {
    Add-Content -LiteralPath $logPath -Value "completed_at_utc=$((Get-Date).ToUniversalTime().ToString('o')) exit_code=$runnerExitCode"
    Pop-Location
}

if ($runnerExitCode -ne 0) {
    Write-Output "candidate_validation=failed stage=$failureStage exit_code=$runnerExitCode log=$([IO.Path]::GetFileName($logPath)) automatic_promotion=false"
    exit $runnerExitCode
}

Write-Output "candidate_validation=ok log=$([IO.Path]::GetFileName($logPath)) automatic_promotion=false"
exit 0
