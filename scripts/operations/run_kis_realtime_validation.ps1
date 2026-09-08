[CmdletBinding()]
param(
    [ValidateSet("domestic", "us")]
    [string]$Market,
    [ValidateRange(60, 14400)]
    [int]$DurationSeconds = 600
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$symbols = if ($Market -eq "domestic") { @("005930", "000660") } else { @("AAPL", "MSFT") }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$report = Join-Path $repoRoot "artifacts\realtime-validation\$Market-$stamp.json"
$arguments = @("scripts\operations\soak_kis_realtime.py", "--symbols") + $symbols + @(
    "--duration-seconds", $DurationSeconds, "--require-quotes", "--output", $report
)

# 작업 스케줄러에는 비밀값이나 공급자 원문 오류 대신 실패 단계와 종료 코드만 남긴다.
function Write-SanitizedFailureReport {
    param(
        [string]$Status,
        [int]$ExitCode
    )

    $directory = Split-Path -Parent $report
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $temporary = "$report.$PID.tmp"
    [ordered]@{
        status = $Status
        market = $Market
        completed_at = (Get-Date).ToUniversalTime().ToString("o")
        exit_code = $ExitCode
        contains_credentials = $false
    } | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $report -Force
}

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Write-SanitizedFailureReport -Status "runner_unavailable" -ExitCode 3
    Write-Output "kis_realtime_validation=failed market=$Market exit_code=3"
    exit 3
}

$validationExitCode = 3
Push-Location $repoRoot
try {
    & $python @arguments
    $validationExitCode = $LASTEXITCODE
}
catch {
    if (-not (Test-Path -LiteralPath $report -PathType Leaf)) {
        Write-SanitizedFailureReport -Status "runner_failed" -ExitCode 3
    }
    Write-Output "kis_realtime_validation=failed market=$Market exit_code=3"
    exit 3
}
finally {
    Pop-Location
}

if ($validationExitCode -ne 0) {
    if (-not (Test-Path -LiteralPath $report -PathType Leaf)) {
        Write-SanitizedFailureReport -Status "validation_failed" -ExitCode $validationExitCode
    }
    Write-Output "kis_realtime_validation=failed market=$Market exit_code=$validationExitCode"
    exit $validationExitCode
}

Write-Output "kis_realtime_validation=ok market=$Market report=$([IO.Path]::GetFileName($report))"
exit 0
