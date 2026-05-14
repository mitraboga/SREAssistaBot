$ErrorActionPreference = "Stop"

$TaskName = "SREAssistaBot"

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "Scheduled Task '$TaskName' is not installed."
    return
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Removed Scheduled Task '$TaskName'."
