[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')]
    [string]$At = "18:30",
    [string]$TaskName = "StockPilot-LocalAI-Collection"
)

$ErrorActionPreference = "Stop"
$runner = [System.IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot "run_local_ai_collection.ps1")
)
if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "The local AI collection runner is missing."
}
if ($TaskName -notmatch '^[A-Za-z0-9_-]{1,64}$') {
    throw "TaskName contains unsupported characters."
}

$powerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
$actionArguments = "-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`""
$action = New-ScheduledTaskAction -Execute $powerShell -Argument $actionArguments
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

if ($PSCmdlet.ShouldProcess($TaskName, "register daily local AI collection at $At")) {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Collects StockPilot market, financial, news, FINRA, and KIS data without model promotion." `
        -Force | Out-Null
}

Write-Output "task=$TaskName schedule=daily@$At user_scope=current"
