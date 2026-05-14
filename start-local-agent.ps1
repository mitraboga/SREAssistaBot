param(
    [ValidateSet("env", "ollama", "bedrock", "google", "anthropic")]
    [string]$Provider = "env"
)

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

if ($Provider -ne "env") {
    $env:MODEL_PROVIDER = $Provider
}

switch ($env:MODEL_PROVIDER) {
    "ollama" {
        if (-not $env:OLLAMA_MODEL) {
            $env:OLLAMA_MODEL = "qwen2.5:1.5b"
        }
        if (-not $env:OLLAMA_API_BASE) {
            $env:OLLAMA_API_BASE = "http://localhost:11434"
        }
        $env:SRE_OLLAMA_SIMPLE_MODE = "true"
    }
    "bedrock" {
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
    }
    "google" {
        $env:SRE_OLLAMA_SIMPLE_MODE = "false"
    }
    "anthropic" {
        $env:SRE_OLLAMA_SIMPLE_MODE = "false"
    }
}

Write-Host "Starting local SRE Agent API on http://localhost:8001"
Write-Host "Using MODEL_PROVIDER=$env:MODEL_PROVIDER"
if ($env:MODEL_PROVIDER -eq "ollama") {
    Write-Host "Using OLLAMA_MODEL=$env:OLLAMA_MODEL OLLAMA_API_BASE=$env:OLLAMA_API_BASE"
}
if ($env:MODEL_PROVIDER -eq "bedrock") {
    Write-Host "Using BEDROCK_MODEL_ID=$env:BEDROCK_MODEL_ID BEDROCK_REGION=$env:BEDROCK_REGION"
    Write-Host "Note: Bedrock model calls are billable AWS API usage."
}

# Run Python directly. Avoid piping stderr through PowerShell because native
# stderr records can terminate the wrapper on Windows even for harmless warnings.
$ErrorActionPreference = "Continue"
& $Python "sre_agent\serve.py"
