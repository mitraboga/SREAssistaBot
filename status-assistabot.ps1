$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidDir = Join-Path $Root ".runtime\pids"
$LogDir = Join-Path $Root ".runtime\logs"

Write-Host "SRE AssistaBot status"
Write-Host "Project: $Root"
Write-Host ""

if (-not (Test-Path $PidDir)) {
    Write-Host "No PID files found. Bot is probably not running."
} else {
    Get-ChildItem -Path $PidDir -Filter "*.pid" | ForEach-Object {
        $serviceName = $_.BaseName
        $rawPid = (Get-Content -Path $_.FullName -Raw).Trim()
        try {
            $process = Get-Process -Id ([int]$rawPid) -ErrorAction Stop
            Write-Host "${serviceName}: running (PID $rawPid)"
        } catch {
            Write-Host "${serviceName}: stopped/stale PID ($rawPid)"
        }
    }
}

Write-Host ""

foreach ($check in @(
    @{ Name = "Agent API"; Url = "http://localhost:8001/health" },
    @{ Name = "Slack listener"; Url = "http://localhost:8002/health" },
    @{ Name = "ADK Web UI"; Url = "http://localhost:8000/dev-ui/" }
)) {
    try {
        $response = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 3
        Write-Host "$($check.Name): HTTP $($response.StatusCode)"
    } catch {
        Write-Host "$($check.Name): unavailable"
    }
}

Write-Host ""
Write-Host "Logs: $LogDir"
Write-Host "Tail agent logs: Get-Content .runtime\logs\agent.out.log -Wait"
Write-Host "Tail Slack logs: Get-Content .runtime\logs\slack.out.log -Wait"
