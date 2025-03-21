; Facebook Video Data Tool Windows Installer Script (NSIS)
; Copyright © 2025 Eric Gitonga. All rights reserved.

; Define constants
!define APP_NAME "Facebook Video Data Tool"
!define COMP_NAME "Eric Gitonga"
!define VERSION "1.0.0"
!define COPYRIGHT "Copyright © 2025 ${COMP_NAME}"
!define DESCRIPTION "Tool for retrieving and analyzing Facebook video data"
!define LICENSE_TXT "LICENSE"
!define INSTALLER_NAME "FBVideoDataTool_Setup.exe"
!define MAIN_APP_EXE "FBVideoDataTool.exe"
!define INSTALL_TYPE "SetShellVarContext current"
!define REG_ROOT "HKCU"
!define REG_APP_PATH "Software\Microsoft\Windows\CurrentVersion\App Paths\${MAIN_APP_EXE}"
!define UNINSTALL_PATH "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

; Include Modern UI
!include "MUI2.nsh"

; Set basic information
Name "${APP_NAME}"
Icon "fbv_icon.ico"
OutFile "${INSTALLER_NAME}"
InstallDir "$LOCALAPPDATA\${APP_NAME}"
InstallDirRegKey "${REG_ROOT}" "${REG_APP_PATH}" ""

; Request application privileges
RequestExecutionLevel user

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "fbv_icon.ico"
!define MUI_UNICON "fbv_icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer_welcome.bmp" ; You'll need to create this
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "installer_header.bmp" ; You'll need to create this
!define MUI_HEADERIMAGE_RIGHT

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${LICENSE_TXT}"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Variables
Var PythonInstalled
Var PythonExe
Var EmbeddedPython

; Installer Functions
Function .onInit
    ; Detect Python installation
    ReadRegStr $PythonExe HKLM "Software\Python\PythonCore\3.9\InstallPath" ""
    ${If} $PythonExe == ""
        ReadRegStr $PythonExe HKLM "Software\Python\PythonCore\3.8\InstallPath" ""
    ${EndIf}
    ${If} $PythonExe == ""
        ReadRegStr $PythonExe HKLM "Software\Python\PythonCore\3.7\InstallPath" ""
    ${EndIf}
    
    ${If} $PythonExe != ""
        StrCpy $PythonExe "$PythonExe\python.exe"
        StrCpy $PythonInstalled "1"
        StrCpy $EmbeddedPython "0"
    ${Else}
        StrCpy $PythonInstalled "0"
        StrCpy $EmbeddedPython "1"
    ${EndIf}
FunctionEnd

; Installer Sections
Section "Install"
    ${INSTALL_TYPE}
    SetOverwrite on
    
    ; Create directories
    CreateDirectory "$INSTDIR"
    CreateDirectory "$INSTDIR\app"
    CreateDirectory "$INSTDIR\python" ; For embedded Python if needed
    
    ; If Python is not installed, extract embedded Python
    ${If} $PythonInstalled == "0"
        DetailPrint "Extracting embedded Python..."
        SetOutPath "$INSTDIR\python"
        File /r "embedded_python\*.*"
        StrCpy $PythonExe "$INSTDIR\python\python.exe"
    ${EndIf}
    
    ; Install main application files
    SetOutPath "$INSTDIR\app"
    File /r "dist\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\app\${MAIN_APP_EXE}" "" "$INSTDIR\app\fbv_icon.ico"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\app\${MAIN_APP_EXE}" "" "$INSTDIR\app\fbv_icon.ico"
    
    ; Install Python dependencies
    DetailPrint "Installing Python dependencies..."
    ${If} $EmbeddedPython == "1"
        ExecWait '"$PythonExe" -m pip install --no-warn-script-location -r "$INSTDIR\app\requirements.txt"'
    ${Else}
        ExecWait '"$PythonExe" -m pip install -r "$INSTDIR\app\requirements.txt"'
    ${EndIf}
    
    ; Write registry keys for uninstaller
    WriteRegStr ${REG_ROOT} "${REG_APP_PATH}" "" "$INSTDIR\app\${MAIN_APP_EXE}"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "DisplayName" "${APP_NAME}"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "DisplayIcon" "$INSTDIR\app\fbv_icon.ico"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "DisplayVersion" "${VERSION}"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "Publisher" "${COMP_NAME}"
    
    ; Calculate installation size for Add/Remove Programs
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD ${REG_ROOT} "${UNINSTALL_PATH}" "EstimatedSize" "$0"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ${INSTALL_TYPE}
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove application files
    RMDir /r "$INSTDIR\app"
    
    ; Remove embedded Python if it exists
    IfFileExists "$INSTDIR\python\python.exe" 0 +2
    RMDir /r "$INSTDIR\python"
    
    ; Remove uninstaller
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"
    
    ; Remove registry keys
    DeleteRegKey ${REG_ROOT} "${REG_APP_PATH}"
    DeleteRegKey ${REG_ROOT} "${UNINSTALL_PATH}"
SectionEnd
