$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SlackDir = Join-Path $Root "slack_bot"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run: python -m venv .venv"
}

Set-Location $SlackDir

Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
    }
}

$env:PYTHONPATH = $SlackDir
$env:PORT = "8002"
$env:SRE_AGENT_API_URL = "http://localhost:8001"
$env:SLACK_SOCKET_MODE = "true"
$env:PYTHONWARNINGS = "ignore"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Starting Slack Socket Mode listener on http://localhost:8002"
Write-Host "Forwarding Slack messages to $env:SRE_AGENT_API_URL"

# Run Python directly. Avoid piping stderr through PowerShell because native
# stderr records can terminate the wrapper on Windows even for harmless warnings.
$ErrorActionPreference = "Continue"
& $Python -m uvicorn main:fast_api --host 0.0.0.0 --port 8002
