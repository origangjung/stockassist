[CmdletBinding()]
param(
    [ValidateRange(1, 3650)]
    [int]$RetentionDays = 14
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$backupRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "backups"))
$expectedRoot = $repoRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
    [System.IO.Path]::DirectorySeparatorChar

if (-not $backupRoot.StartsWith($expectedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Backup path must stay inside the repository workspace."
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI was not found on PATH."
}

New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$postgresName = "postgres-$timestamp.dump"
$redisName = "redis-$timestamp.rdb"
$manifestName = "backup-$timestamp.json"
$postgresPath = Join-Path $backupRoot $postgresName
$redisPath = Join-Path $backupRoot $redisName
$manifestPath = Join-Path $backupRoot $manifestName
$containerDump = "/tmp/stockpilot-$timestamp.dump"

Push-Location $repoRoot
try {
    $postgresUser = (docker compose exec -T postgres printenv POSTGRES_USER | Select-Object -First 1).Trim()
    $postgresDatabase = (docker compose exec -T postgres printenv POSTGRES_DB | Select-Object -First 1).Trim()
    if (-not $postgresUser -or -not $postgresDatabase) {
        throw "PostgreSQL container identity is unavailable."
    }

    docker compose exec -T postgres pg_dump -U $postgresUser -d $postgresDatabase -Fc --no-owner --no-privileges -f $containerDump
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed." }

    docker compose exec -T postgres pg_restore --list $containerDump | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup validation failed." }

    docker compose cp "postgres:$containerDump" $postgresPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not copy the PostgreSQL backup." }

    docker compose exec -T redis redis-cli SAVE | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Redis backup failed." }

    docker compose cp "redis:/data/dump.rdb" $redisPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not copy the Redis backup." }

    $revision = docker compose exec -T postgres psql -U $postgresUser -d $postgresDatabase -Atc "SELECT version_num FROM alembic_version LIMIT 1"
    if ($LASTEXITCODE -ne 0) { throw "Could not read the database revision." }
    $revision = ($revision | Select-Object -First 1).Trim()
    if (-not $revision) { throw "Database revision is unavailable." }

    $manifest = [ordered]@{
        created_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        application_release = (git rev-parse --short HEAD 2>$null)
        alembic_revision = $revision
        retention_days = $RetentionDays
        files = @(
            [ordered]@{
                name = $postgresName
                bytes = (Get-Item -LiteralPath $postgresPath).Length
                sha256 = (Get-FileHash -LiteralPath $postgresPath -Algorithm SHA256).Hash
            },
            [ordered]@{
                name = $redisName
                bytes = (Get-Item -LiteralPath $redisPath).Length
                sha256 = (Get-FileHash -LiteralPath $redisPath -Algorithm SHA256).Hash
            }
        )
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8

    $cutoff = (Get-Date).AddDays(-$RetentionDays)
    $expired = Get-ChildItem -LiteralPath $backupRoot -File | Where-Object {
        $_.LastWriteTime -lt $cutoff -and
        $_.Name -match '^(postgres-\d{8}-\d{6}\.dump|redis-\d{8}-\d{6}\.rdb|backup-\d{8}-\d{6}\.json)$'
    }
    foreach ($file in $expired) {
        $resolved = [System.IO.Path]::GetFullPath($file.FullName)
        if (-not $resolved.StartsWith($backupRoot + [System.IO.Path]::DirectorySeparatorChar,
                [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove a file outside the backup directory."
        }
        Remove-Item -LiteralPath $resolved -Force
    }

    Write-Output "backup=ok timestamp=$timestamp files=2 expired_removed=$($expired.Count)"
}
catch {
    foreach ($partialPath in @($postgresPath, $redisPath, $manifestPath)) {
        if (Test-Path -LiteralPath $partialPath) {
            Remove-Item -LiteralPath $partialPath -Force
        }
    }
    throw
}
finally {
    docker compose exec -T postgres rm -f $containerDump 2>$null | Out-Null
    Pop-Location
}
