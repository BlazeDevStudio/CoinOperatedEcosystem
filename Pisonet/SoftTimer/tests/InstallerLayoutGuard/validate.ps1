# Read-only, source-linked NSIS layout check. No install, registry or task mutation.
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot '../../installer/BlazePisonet-SoftTimer.nsi'
$text = Get-Content -LiteralPath $scriptPath -Raw
$required = @(
    'InstallDir "$PROGRAMFILES64\BlazeSystems\BlazePisonet SoftTimer LAB"',
    'CreateDirectory "$SMPROGRAMS\BlazePisonet SoftTimer LAB"',
    'CreateShortcut "$SMPROGRAMS\BlazePisonet SoftTimer LAB\',
    'RMDir "$SMPROGRAMS\BlazePisonet SoftTimer LAB"',
    'Uninstall\BlazePisonetSoftTimerLab',
    'IfFileExists "$COMMONAPPDATA\BlazeSystems\BlazePisonetSoftTimer\*.*"',
    'LAB file-copy install complete; no Windows startup tasks created.'
)
foreach ($item in $required) {
    if (-not $text.Contains($item)) { throw "Installer layout mismatch: $item" }
}
$forbidden = @(
    'ConfigureFirewall',
    'advfirewall firewall add rule',
    'File "..\..\..\..\out\bundle',
    'CreateDirectory "$SMPROGRAMS\BlazePisonet SoftTimer"',
    '--install-system-integration',
    '--uninstall-system-integration',
    'taskkill.exe',
    'icacls.exe',
    'maintenance.until',
    'ExecWait',
    'nsExec::',
    'DeleteRegKey HKLM "Software\BlazeSystems\BlazePisonet SoftTimer"'
)
foreach ($item in $forbidden) {
    if ($text.Contains($item)) { throw "Unsafe/outdated installer path: $item" }
}
Write-Host 'INSTALLER_LAYOUT_GUARD_PASS: LAB file-copy-only; no production task, process, state or ACL mutation'
