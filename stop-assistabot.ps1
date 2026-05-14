$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $Root ".runtime"
$PidDir = Join-Path $RuntimeDir "pids"
$LogDir = Join-Path $RuntimeDir "logs"

if (-not (Test-Path $PidDir)) {
    Write-Host "No SRE AssistaBot PID directory found. Nothing to stop."
    return
}

Get-ChildItem -Path $PidDir -Filter "*.pid" | ForEach-Object {
    $serviceName = $_.BaseName
    $rawPid = (Get-Content -Path $_.FullName -Raw).Trim()

    if (-not $rawPid) {
        Remove-Item -LiteralPath $_.FullName -Force
        return
    }

    try {
        $process = Get-Process -Id ([int]$rawPid) -ErrorAction Stop
        Stop-Process -Id $process.Id -Force
        Write-Host "Stopped $serviceName (PID $rawPid)"
    } catch {
        Write-Host "$serviceName was not running (PID $rawPid)"
    }

    Remove-Item -LiteralPath $_.FullName -Force
}

if (Test-Path $LogDir) {
    Write-Host "Logs kept at $LogDir"
}
