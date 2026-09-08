[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateRange(50, 5000)]
    [int]$MarketLimit = 2600
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$composePath = Join-Path $repoRoot "docker-compose.yml"
$logRoot = Join-Path $repoRoot "datasets\local-ai-incremental\task-logs"

function Test-DockerEngine {
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = "SilentlyContinue"
        & docker info *> $null
        return $LASTEXITCODE -eq 0
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
}

function Start-DockerEngine {
    if (Test-DockerEngine) { return }
    $dockerCli = (Get-Command docker -ErrorAction Stop).Source
    $cliInstallRoot = Split-Path (Split-Path (Split-Path $dockerCli -Parent) -Parent) -Parent
    $desktopCandidates = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe"),
        (Join-Path $cliInstallRoot "Docker Desktop.exe")
    )
    $desktop = $desktopCandidates | Where-Object {
        Test-Path -LiteralPath $_ -PathType Leaf
    } | Select-Object -First 1
    if (-not $desktop) {
        throw "Docker Desktop is not running and its executable was not found."
    }
    Start-Process -FilePath $desktop -WindowStyle Hidden
    $deadline = (Get-Date).AddMinutes(3)
    do {
        Start-Sleep -Seconds 3
        if (Test-DockerEngine) { return }
    } while ((Get-Date) -lt $deadline)
    throw "Docker Desktop did not become ready within three minutes."
}

function Write-SanitizedLogLine {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Line,
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $text = [string]$Line
    if ($text -match '(?i)(secret|token|api[_-]?key|authorization)\s*[:=]') {
        Add-Content -LiteralPath $Path -Value "redacted_sensitive_output=true"
        return
    }
    Add-Content -LiteralPath $Path -Value $text
}

New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot ("collector-{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))
$arguments = @(
    "compose", "--profile", "collection", "run", "--rm", "collector",
    "--mode", "all", "--market-limit", $MarketLimit, "--news-windows", "4"
)
if ($DryRun) {
    $arguments += "--dry-run"
}

Push-Location $repoRoot
$runnerExitCode = 0
$failureStage = ""
try {
    if (-not (Test-Path -LiteralPath $composePath -PathType Leaf)) {
        throw "compose file unavailable"
    }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "docker cli unavailable"
    }
    Start-DockerEngine
    $startedAt = (Get-Date).ToUniversalTime().ToString("o")
    Add-Content -LiteralPath $logPath -Value "started_at_utc=$startedAt dry_run=$($DryRun.IsPresent)"

    # 긴 수집이 중단돼도 완료된 단계가 남도록 Docker 출력을 즉시 보안 필터링해 기록한다.
    $previousErrorAction = $ErrorActionPreference
    try {
        # Docker Compose는 정상 진행 상태도 stderr에 쓰므로 프로세스 종료 코드로 판정한다.
        $ErrorActionPreference = "Continue"
        & docker @arguments 2>&1 | ForEach-Object {
            Write-SanitizedLogLine -Line $_ -Path $logPath
        }
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
    Add-Content -LiteralPath $logPath -Value "completed_at_utc=$((Get-Date).ToUniversalTime().ToString('o')) exit_code=$exitCode"
    if ($exitCode -ne 0) {
        $runnerExitCode = $exitCode
        $failureStage = "collector"
    }
}
catch {
    $runnerExitCode = 3
    $failureStage = "runner"
    Add-Content -LiteralPath $logPath -Value "completed_at_utc=$((Get-Date).ToUniversalTime().ToString('o')) exit_code=3 failure_stage=runner"
}
finally {
    Pop-Location
}

if ($runnerExitCode -ne 0) {
    Write-Output "collection=failed dry_run=$($DryRun.IsPresent) stage=$failureStage exit_code=$runnerExitCode log=$([System.IO.Path]::GetFileName($logPath))"
    exit $runnerExitCode
}

Write-Output "collection=ok dry_run=$($DryRun.IsPresent) log=$([System.IO.Path]::GetFileName($logPath))"
exit 0
