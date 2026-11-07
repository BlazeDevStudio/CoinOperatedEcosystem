Unicode True
RequestExecutionLevel admin
ManifestDPIAware true
Name "BlazePisonet SoftTimer LAB Preview"
OutFile "..\out\BlazePisonet-SoftTimer-Setup-v0.4.0-LAB.exe"
InstallDir "$PROGRAMFILES64\BlazeSystems\BlazePisonet SoftTimer LAB"
InstallDirRegKey HKLM "Software\BlazeSystems\BlazePisonet SoftTimer LAB" "InstallDir"
SetCompressor /SOLID lzma
SetCompressorDictSize 64
BrandingText "BlazeSystems · BlazePisonet SoftTimer"
VIProductVersion "0.4.0.0"
VIAddVersionKey /LANG=1033 "ProductName" "BlazePisonet SoftTimer"
VIAddVersionKey /LANG=1033 "ProductVersion" "0.4.0"
VIAddVersionKey /LANG=1033 "CompanyName" "BlazeSystems"
VIAddVersionKey /LANG=1033 "FileDescription" "BlazePisonet SoftTimer Setup"
VIAddVersionKey /LANG=1033 "FileVersion" "0.4.0.0"
VIAddVersionKey /LANG=1033 "LegalCopyright" "Copyright © 2026 BlazeSystems"

!include "MUI2.nsh"
!include "LogicLib.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ; Prevent accidental replacement of the normal installed product.
  IfFileExists "$PROGRAMFILES64\BlazeSystems\BlazePisonet SoftTimer\BlazePisonet.SoftTimer.exe" 0 +3
  MessageBox MB_ICONSTOP|MB_OK "Existing SoftTimer installation detected. Do not install this lab build on an occupied PC."
  Abort
  MessageBox MB_ICONEXCLAMATION|MB_OK "UNSIGNED LAB PREVIEW ONLY. Use a clean disposable Windows test PC or VM. Not approved for live coins or customer deployment."
FunctionEnd


Var TaskResult
Var TaskOutput



Section "BlazePisonet SoftTimer" SEC_MAIN
  SectionIn RO
  SetShellVarContext all
  SetOutPath "$INSTDIR"

  File "..\out\bundle\BlazePisonet.SoftTimer.exe"
  File "..\out\bundle\BlazePisonet.SoftTimer.Watchdog.exe"

  CreateDirectory "$APPDATA\BlazeSystems\BlazePisonetSoftTimer"
  nsExec::ExecToStack '$\"$SYSDIR\icacls.exe$\" $\"$APPDATA\BlazeSystems\BlazePisonetSoftTimer$\" /inheritance:r /grant:r *S-1-5-18:(OI)(CI)F *S-1-5-32-544:(OI)(CI)F /T /C'
  Pop $TaskResult
  Pop $TaskOutput
  DetailPrint "$TaskOutput"

  Delete "$APPDATA\BlazeSystems\BlazePisonetSoftTimer\maintenance.until"

  CreateDirectory "$SMPROGRAMS\BlazePisonet SoftTimer"
  CreateShortcut "$SMPROGRAMS\BlazePisonet SoftTimer LAB\BlazePisonet SoftTimer LAB.lnk" "$INSTDIR\BlazePisonet.SoftTimer.exe"
  CreateShortcut "$SMPROGRAMS\BlazePisonet SoftTimer LAB\Uninstall BlazePisonet SoftTimer LAB.lnk" "$INSTDIR\Uninstall.exe"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKLM "Software\BlazeSystems\BlazePisonet SoftTimer LAB" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlazePisonetSoftTimerLab" "DisplayName" "BlazePisonet SoftTimer (LAB preview)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlazePisonetSoftTimerLab" "DisplayVersion" "0.4.0-lab"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlazePisonetSoftTimerLab" "Publisher" "BlazeSystems"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlazePisonetSoftTimerLab" "DisplayIcon" "$INSTDIR\BlazePisonet.SoftTimer.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlazePisonetSoftTimerLab" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlazePisonetSoftTimerLab" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlazePisonetSoftTimerLab" "NoRepair" 1

  DetailPrint "Registering SoftTimer Windows startup integration..."
  ExecWait '"$INSTDIR\BlazePisonet.SoftTimer.exe" --install-system-integration' $TaskResult
  ${If} $TaskResult != 0
    SetErrorLevel 1603
    Abort "BlazePisonet SoftTimer could not register Windows startup integration."
  ${EndIf}

SectionEnd

Section "Desktop shortcut" SEC_DESKTOP
  SetShellVarContext all
  CreateShortcut "$DESKTOP\BlazePisonet SoftTimer LAB.lnk" "$INSTDIR\BlazePisonet.SoftTimer.exe"
SectionEnd

Section "Uninstall"
  SetShellVarContext all

  CreateDirectory "$APPDATA\BlazeSystems\BlazePisonetSoftTimer"
  FileOpen $0 "$APPDATA\BlazeSystems\BlazePisonetSoftTimer\maintenance.until" w
  FileWrite $0 "4102444800"
  FileClose $0

  ExecWait '"$INSTDIR\BlazePisonet.SoftTimer.exe" --uninstall-system-integration' $TaskResult
  DetailPrint "SoftTimer system-integration removal exit code: $TaskResult"

  nsExec::ExecToStack '$\"$SYSDIR\taskkill.exe$\" /IM BlazePisonet.SoftTimer.exe /F'
  Pop $TaskResult
  Pop $TaskOutput
  nsExec::ExecToStack '$\"$SYSDIR\taskkill.exe$\" /IM BlazePisonet.SoftTimer.Watchdog.exe /F'
  Pop $TaskResult
  Pop $TaskOutput


  Delete "$DESKTOP\BlazePisonet SoftTimer LAB.lnk"
  Delete "$SMPROGRAMS\BlazePisonet SoftTimer LAB\BlazePisonet SoftTimer LAB.lnk"
  Delete "$SMPROGRAMS\BlazePisonet SoftTimer LAB\Uninstall BlazePisonet SoftTimer LAB.lnk"
  RMDir "$SMPROGRAMS\BlazePisonet SoftTimer"

  Delete "$INSTDIR\BlazePisonet.SoftTimer.exe"
  Delete "$INSTDIR\BlazePisonet.SoftTimer.Watchdog.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BlazePisonetSoftTimerLab"
  DeleteRegKey HKLM "Software\BlazeSystems\BlazePisonet SoftTimer LAB"
SectionEnd
