$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgentsDir = Join-Path $Root "agents"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run: python -m venv .venv"
}

Set-Location $AgentsDir

Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
    }
}

$env:PYTHONPATH = $AgentsDir
$env:SESSION_SERVICE_URI = "sqlite:///./srebot_sessions.db"
$env:PORT = "8001"
$env:PYTHONWARNINGS = "ignore"
$env:PYTHONIOENCODING = "utf-8"

# Force Bedrock for this process even if GOOGLE_API_KEY or ANTHROPIC_API_KEY
# are present in agents/.env.
$env:MODEL_PROVIDER = "bedrock"
$env:SRE_OLLAMA_SIMPLE_MODE = "false"

if (-not $env:BEDROCK_MODEL_ID) {
    $env:BEDROCK_MODEL_ID = "amazon.nova-micro-v1:0"
}

if (-not $env:BEDROCK_REGION) {
    if ($env:AWS_REGION) {
        $env:BEDROCK_REGION = $env:AWS_REGION
    } else {
        $env:BEDROCK_REGION = "us-east-1"
    }
}

$env:AWS_REGION_NAME = $env:BEDROCK_REGION
$env:AWS_DEFAULT_REGION = $env:BEDROCK_REGION

Write-Host "Starting local SRE Agent API on http://localhost:8001"
Write-Host "Using MODEL_PROVIDER=$env:MODEL_PROVIDER BEDROCK_MODEL_ID=$env:BEDROCK_MODEL_ID"
Write-Host "Using AWS_PROFILE=$env:AWS_PROFILE BEDROCK_REGION=$env:BEDROCK_REGION"
Write-Host "Note: Bedrock model calls are billable AWS API usage."

$ErrorActionPreference = "Continue"
& $Python "sre_agent\serve.py"
