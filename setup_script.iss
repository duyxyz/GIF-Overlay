#define MyAppName "GIF Overlay"
#define MyAppVersion "1.0.7"
#define MyAppPublisher "DuyXYZ"
#define MyAppURL "https://github.com/duyxyz/GIF-Overlay"
#define MyAppExeName "GIF Overlay.exe"

[Setup]
; Basic setup details
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
; AppExeName is NOT a valid directive, so we remove it. 
; The Executable name is used in [Icons] and [Run] via the define above.

; Make the setup look modern
WizardStyle=modern
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=GIF-Overlay-Setup

; Minimize UAC requests (install to user folder if possible, otherwise admin)
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; IMPORTANT: This assumes we are running this from the repo root
; and PyInstaller has already built the folder into "dist\GIF-Overlay"
Source: "dist\GIF-Overlay\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
