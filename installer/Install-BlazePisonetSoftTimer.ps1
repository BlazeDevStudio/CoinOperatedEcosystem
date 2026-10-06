param(
    [string]$InstallDir = "$env:ProgramFiles\BlazeSystems\BlazePisonet SoftTimer"
)
$ErrorActionPreference = 'Stop'

function Is-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Is-Admin)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'))
    exit
}

$Source = Split-Path -Parent $PSScriptRoot
$AppSource = Join-Path $Source 'app'
if (-not (Test-Path (Join-Path $AppSource 'BlazePisonet.SoftTimer.exe'))) {
    throw "Release package is incomplete: app\BlazePisonet.SoftTimer.exe was not found."
}

Write-Host "Installing BlazePisonet SoftTimer to $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path (Join-Path $AppSource '*') -Destination $InstallDir -Recurse -Force

$DataDir = Join-Path $env:ProgramData 'BlazeSystems\BlazePisonetSoftTimer'
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
# Data contains account hashes, device bindings and integration keys. Keep it away from ordinary users.
& icacls.exe $DataDir /inheritance:r /grant:r 'SYSTEM:(OI)(CI)F' 'Administrators:(OI)(CI)F' /T /C | Out-Null

$Agent = Join-Path $InstallDir 'BlazePisonet.SoftTimer.exe'
$Watchdog = Join-Path $InstallDir 'BlazePisonet.SoftTimer.Watchdog.exe'
$User = "$env:USERDOMAIN\$env:USERNAME"

& schtasks.exe /Delete /TN 'BlazePisonet SoftTimer' /F 2>$null | Out-Null
& schtasks.exe /Delete /TN 'BlazePisonet SoftTimer Watchdog' /F 2>$null | Out-Null
& schtasks.exe /Create /TN 'BlazePisonet SoftTimer' /SC ONLOGON /TR ('"'+$Agent+'"') /RL HIGHEST /RU $User /F | Out-Null
& schtasks.exe /Create /TN 'BlazePisonet SoftTimer Watchdog' /SC MINUTE /MO 1 /TR ('"'+$Watchdog+'"') /RL HIGHEST /RU $User /F | Out-Null

# Centralized mode uses TCP 8765 by default. The rule is local-subnet-only and can be removed if centralized mode is unused.
& netsh.exe advfirewall firewall delete rule name='BlazePisonet SoftTimer Centralized' 2>$null | Out-Null
& netsh.exe advfirewall firewall add rule name='BlazePisonet SoftTimer Centralized' dir=in action=allow protocol=TCP localport=8765 remoteip=localsubnet profile=private | Out-Null

# HttpListener can bind because the app is elevated. Add an explicit URL ACL as a compatibility fallback for the current user.
& netsh.exe http delete urlacl url='http://+:8765/softtimer/' 2>$null | Out-Null
& netsh.exe http add urlacl url='http://+:8765/softtimer/' user=$User | Out-Null

Write-Host 'Starting BlazePisonet SoftTimer...'
Start-Process -FilePath $Agent -WorkingDirectory $InstallDir
Write-Host 'Installation complete.'
Write-Host 'First run: set the administrator password, select the timer source, then enable SoftTimer.'
