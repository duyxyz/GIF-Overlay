#define MyAppName "GIF Overlay"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "DuyXYZ"
#define MyAppURL "https://github.com/duyxyz/GIF-Overlay"
#define MyAppExeName "GIF-Overlay.exe"

[Setup]
; Basic setup details
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
ChangesAssociations=yes

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

[Registry]
Root: HKCU; Subkey: "Software\Classes\.gif\OpenWithProgids"; ValueType: string; ValueName: "GIFOverlay.gif"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\GIFOverlay.gif"; ValueType: string; ValueName: ""; ValueData: "GIF Image"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\GIFOverlay.gif\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCU; Subkey: "Software\Classes\GIFOverlay.gif\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

