$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$app=Join-Path $root 'src/BlazePisonet.SoftTimer/BlazePisonet.SoftTimer.csproj'
$wd=Join-Path $root 'src/BlazePisonet.SoftTimer.Watchdog/BlazePisonet.SoftTimer.Watchdog.csproj'
dotnet restore $app
if ($LASTEXITCODE -ne 0) { throw "SoftTimer restore failed (dotnet exit code $LASTEXITCODE)." }
dotnet restore $wd
if ($LASTEXITCODE -ne 0) { throw "Watchdog restore failed (dotnet exit code $LASTEXITCODE)." }
dotnet build $app -c Release -warnaserror
if ($LASTEXITCODE -ne 0) { throw "SoftTimer build failed (dotnet exit code $LASTEXITCODE)." }
dotnet build $wd -c Release -warnaserror
if ($LASTEXITCODE -ne 0) { throw "Watchdog build failed (dotnet exit code $LASTEXITCODE)." }
# Publish real unsigned, self-contained Windows executables for spare-machine lab review.
# Publishing does not authorize customer deployment, payment acceptance, or a signed installer.
$labOut=Join-Path $root 'out/lab-publish'
New-Item -Path $labOut -ItemType Directory -Force | Out-Null
dotnet publish $app -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o $labOut
if ($LASTEXITCODE -ne 0) { throw "SoftTimer publish failed (dotnet exit code $LASTEXITCODE)." }
dotnet publish $wd -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o $labOut
if ($LASTEXITCODE -ne 0) { throw "Watchdog publish failed (dotnet exit code $LASTEXITCODE)." }
foreach ($filename in @('BlazePisonet.SoftTimer.exe', 'BlazePisonet.SoftTimer.Watchdog.exe')) {
    $payload=Join-Path $labOut $filename
    if (-not (Test-Path -Path $payload -PathType Leaf) -or (Get-Item -Path $payload).Length -le 0) {
        throw "Published executable missing or empty: $filename"
    }
}
Write-Host 'Build and unsigned self-contained Windows lab publish passed. NO-GO FOR SHOP INSTALL.'
