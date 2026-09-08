[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')]
    [string]$At = "19:30"
)

$ErrorActionPreference = "Stop"
$runner = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "run_local_ai_candidate_validation.ps1"))
$powerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
$action = New-ScheduledTaskAction -Execute $powerShell -Argument (
    "-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`""
)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At $At
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
    -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal `
    -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

if ($PSCmdlet.ShouldProcess("StockPilot-LocalAI-Candidate-Validation", "register weekly validation")) {
    Register-ScheduledTask `
        -TaskName "StockPilot-LocalAI-Candidate-Validation" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Validates local AI candidates without automatic model promotion." `
        -Force | Out-Null
}
Write-Output "task=StockPilot-LocalAI-Candidate-Validation weekly=Saturday@$At"
