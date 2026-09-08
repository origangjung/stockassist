[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateRange(60, 14400)]
    [int]$DurationSeconds = 600
)

$ErrorActionPreference = "Stop"
$runner = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "run_kis_realtime_validation.ps1"))
$powerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
$principal = New-ScheduledTaskPrincipal `
    -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew
$tasks = @(
    @{ Name = "StockPilot-KIS-Realtime-KR"; Market = "domestic"; At = "09:10" },
    @{ Name = "StockPilot-KIS-Realtime-US"; Market = "us"; At = "23:35" }
)

foreach ($item in $tasks) {
    $arguments = "-NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`" -Market $($item.Market) -DurationSeconds $DurationSeconds"
    $action = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments
    $trigger = New-ScheduledTaskTrigger `
        -Weekly `
        -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
        -At $item.At
    if ($PSCmdlet.ShouldProcess($item.Name, "register KIS realtime validation")) {
        Register-ScheduledTask `
            -TaskName $item.Name `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Validates read-only KIS realtime quotes without placing orders." `
            -Force | Out-Null
    }
    Write-Output "task=$($item.Name) weekdays@$($item.At)"
}
