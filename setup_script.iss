[Setup]
; Basic setup details
AppName=GIF Overlay
AppVersion=1.0.7
AppPublisher=DuyXYZ
AppPublisherURL=https://github.com/duyxyz/GIF-Overlay
AppExeName=GIF Overlay.exe

; Make the setup look modern
WizardStyle=modern
DefaultDirName={autopf}\GIF Overlay
DefaultGroupName=GIF Overlay
UninstallDisplayIcon={app}\GIF Overlay.exe
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
Name: "{group}\GIF Overlay"; Filename: "{app}\GIF Overlay.exe"
Name: "{autodesktop}\GIF Overlay"; Filename: "{app}\GIF Overlay.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GIF Overlay.exe"; Description: "{cm:LaunchProgram,GIF Overlay}"; Flags: nowait postinstall skipifsilent
