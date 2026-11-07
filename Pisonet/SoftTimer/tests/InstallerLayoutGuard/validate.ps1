# Read-only, source-linked NSIS layout check. No install, registry or task mutation.
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot '../../installer/BlazePisonet-SoftTimer.nsi'
$text = Get-Content -LiteralPath $scriptPath -Raw
$required = @(
    'InstallDir "$PROGRAMFILES64\BlazeSystems\BlazePisonet SoftTimer LAB"',
    'CreateDirectory "$SMPROGRAMS\BlazePisonet SoftTimer LAB"',
    'CreateShortcut "$SMPROGRAMS\BlazePisonet SoftTimer LAB\',
    'RMDir "$SMPROGRAMS\BlazePisonet SoftTimer LAB"',
    'Uninstall\BlazePisonetSoftTimerLab'
)
foreach ($item in $required) {
    if (-not $text.Contains($item)) { throw "Installer layout mismatch: $item" }
}
$forbidden = @(
    'ConfigureFirewall',
    'advfirewall firewall add rule',
    'File "..\..\..\..\out\bundle',
    'CreateDirectory "$SMPROGRAMS\BlazePisonet SoftTimer"'
)
foreach ($item in $forbidden) {
    if ($text.Contains($item)) { throw "Unsafe/outdated installer path: $item" }
}
Write-Host 'INSTALLER_LAYOUT_GUARD_PASS: lab paths and default network exposure checks passed'
