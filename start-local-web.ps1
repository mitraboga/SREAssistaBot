$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgentsDir = Join-Path $Root "agents"
$Adk = Join-Path $Root ".venv\Scripts\adk.exe"

if (-not (Test-Path $Adk)) {
    throw "ADK executable not found. Install dependencies with: .\.venv\Scripts\python.exe -m pip install -r agents\sre_agent\requirements.txt"
}

Set-Location $AgentsDir

Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
    }
}

$env:PYTHONPATH = $AgentsDir
$env:SESSION_SERVICE_URI = "sqlite:///./srebot_web_sessions.db"
$env:PYTHONWARNINGS = "ignore"
$env:PYTHONIOENCODING = "utf-8"
$env:OLLAMA_API_BASE = "http://localhost:11434"

Write-Host "Starting ADK Web UI on http://localhost:8000"
Write-Host "Using MODEL_PROVIDER=$env:MODEL_PROVIDER OLLAMA_MODEL=$env:OLLAMA_MODEL"
Write-Host "Using SESSION_SERVICE_URI=$env:SESSION_SERVICE_URI"

$ErrorActionPreference = "Continue"
& $Adk web --session_service_uri $env:SESSION_SERVICE_URI --host 0.0.0.0 --port 8000 .
