[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$TaskName = "StockPilot-LocalAI-Collection"
)

$ErrorActionPreference = "Stop"
if ($TaskName -notmatch '^[A-Za-z0-9_-]{1,64}$') {
    throw "TaskName contains unsupported characters."
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $task) {
    Write-Output "task=$TaskName status=not_registered"
    return
}
if ($PSCmdlet.ShouldProcess($TaskName, "unregister local AI collection")) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
Write-Output "task=$TaskName status=unregistered"
