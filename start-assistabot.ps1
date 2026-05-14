param(
    [ValidateSet("ollama", "bedrock", "google", "anthropic")]
    [string]$Provider = "ollama",

    [switch]$WithWeb,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $Root ".runtime"
$LogDir = Join-Path $RuntimeDir "logs"
$PidDir = Join-Path $RuntimeDir "pids"
$PowerShell = Join-Path $PSHOME "powershell.exe"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $PidDir -Force | Out-Null

if ($Restart) {
    & (Join-Path $Root "stop-assistabot.ps1")
}

function Test-PidRunning {
    param([string]$PidFile)

    if (-not (Test-Path $PidFile)) {
        return $false
    }

    $rawPid = (Get-Content -Path $PidFile -Raw).Trim()
    if (-not $rawPid) {
        return $false
    }

    try {
        $process = Get-Process -Id ([int]$rawPid) -ErrorAction Stop
        return -not $process.HasExited
    } catch {
        return $false
    }
}

function Start-ManagedService {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    $pidFile = Join-Path $PidDir "$Name.pid"
    if (Test-PidRunning -PidFile $pidFile) {
        $existingPid = (Get-Content -Path $pidFile -Raw).Trim()
        Write-Host "$Name already running (PID $existingPid)"
        return
    }

    $stdout = Join-Path $LogDir "$Name.out.log"
    $stderr = Join-Path $LogDir "$Name.err.log"
    $argList = @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $ScriptPath
    ) + $Arguments

    $process = Start-Process `
        -FilePath $PowerShell `
        -ArgumentList $argList `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru `
        -WindowStyle Hidden

    Set-Content -Path $pidFile -Value $process.Id
    Write-Host "Started $Name (PID $($process.Id))"
    Write-Host "  logs: $stdout"
}

function Wait-ForHttp {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "$Name health check OK: $Url"
                return
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }

    Write-Warning "$Name did not pass health check before timeout: $Url"
}

Write-Host "Starting SRE AssistaBot with provider: $Provider"

Start-ManagedService `
    -Name "agent" `
    -ScriptPath (Join-Path $Root "start-local-agent.ps1") `
    -Arguments @("-Provider", $Provider)

Wait-ForHttp -Name "Agent API" -Url "http://localhost:8001/health"

Start-ManagedService `
    -Name "slack" `
    -ScriptPath (Join-Path $Root "start-local-slack.ps1")

Wait-ForHttp -Name "Slack listener" -Url "http://localhost:8002/health"

if ($WithWeb) {
    Start-ManagedService `
        -Name "web" `
        -ScriptPath (Join-Path $Root "start-local-web.ps1")

    Wait-ForHttp -Name "ADK Web UI" -Url "http://localhost:8000/dev-ui/"
}

Write-Host ""
Write-Host "SRE AssistaBot is running in the background."
Write-Host "Use .\status-assistabot.ps1 to check it."
Write-Host "Use .\stop-assistabot.ps1 to stop it."
