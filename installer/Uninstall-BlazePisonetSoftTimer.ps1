param(
    [switch]$RemoveData,
    [string]$InstallDir = "$env:ProgramFiles\BlazeSystems\BlazePisonet SoftTimer"
)
$ErrorActionPreference = 'SilentlyContinue'

function Is-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
if (-not (Is-Admin)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'))
    exit
}

$DataDir = Join-Path $env:ProgramData 'BlazeSystems\BlazePisonetSoftTimer'
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
[IO.File]::WriteAllText((Join-Path $DataDir 'maintenance.until'), [DateTimeOffset]::UtcNow.AddHours(1).ToUnixTimeSeconds().ToString())

Get-Process 'BlazePisonet.SoftTimer','BlazePisonet.SoftTimer.Watchdog' -ErrorAction SilentlyContinue | Stop-Process -Force
& schtasks.exe /Delete /TN 'BlazePisonet SoftTimer' /F | Out-Null
& schtasks.exe /Delete /TN 'BlazePisonet SoftTimer Watchdog' /F | Out-Null
& netsh.exe advfirewall firewall delete rule name='BlazePisonet SoftTimer Centralized' | Out-Null
& netsh.exe http delete urlacl url='http://+:8765/softtimer/' | Out-Null

$system = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\System'
$explorer = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer'
Remove-ItemProperty -Path $system -Name DisableTaskMgr,DisableRegistryTools -ErrorAction SilentlyContinue
Remove-ItemProperty -Path $explorer -Name NoLogoff,NoClose -ErrorAction SilentlyContinue

$hosts = "$env:SystemRoot\System32\drivers\etc\hosts"
if (Test-Path $hosts) {
    $text = Get-Content $hosts -Raw
    $text = [regex]::Replace($text, '(?ms)^# BLAZEPISONET SOFTTIMER START\r?\n.*?^# BLAZEPISONET SOFTTIMER END\r?\n?', '')
    Set-Content -Path $hosts -Value $text -Encoding ASCII
}

Remove-Item -Path $InstallDir -Recurse -Force
if ($RemoveData) { Remove-Item -Path $DataDir -Recurse -Force }
Write-Host 'BlazePisonet SoftTimer uninstalled.'
if (-not $RemoveData) { Write-Host "Configuration and paid-time state were preserved at $DataDir" }
