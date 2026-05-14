param(
    [ValidateSet("ollama", "bedrock", "google", "anthropic")]
    [string]$Provider = "ollama",

    [switch]$WithWeb
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName = "SREAssistaBot"
$PowerShell = Join-Path $PSHOME "powershell.exe"
$StartScript = Join-Path $Root "start-assistabot.ps1"

$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    "`"$StartScript`"",
    "-Provider",
    $Provider,
    "-Restart"
)

if ($WithWeb) {
    $arguments += "-WithWeb"
}

$action = New-ScheduledTaskAction -Execute $PowerShell -Argument ($arguments -join " ")
$trigger = New-ScheduledTaskTrigger -AtLogOn
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal `
    -UserId $currentUser `
    -LogonType Interactive `
    -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Force `
        -ErrorAction Stop | Out-Null
} catch {
    Write-Host ""
    Write-Host "Failed to install Scheduled Task '$TaskName'." -ForegroundColor Red
    Write-Host "Reason: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Fix: open PowerShell as Administrator, then rerun:"
    Write-Host "  cd `"$Root`""
    $retry = ".\install-assistabot-login-task.ps1 -Provider $Provider"
    if ($WithWeb) {
        $retry += " -WithWeb"
    }
    Write-Host "  $retry"
    throw
}

Write-Host "Installed Scheduled Task '$TaskName'."
Write-Host "It will start SRE AssistaBot at login with provider: $Provider"
if ($WithWeb) {
    Write-Host "It will also start the ADK Web UI."
}
Write-Host "To remove it, run: .\uninstall-assistabot-login-task.ps1"
