; Inno Setup script for PreflightQC (Phase 11, criteria P11-A7 and P13-A1).
;
; PER-USER BY DEFAULT, NO ADMINISTRATOR PROMPT.
;
; PrivilegesRequired=lowest is the whole point: the target user is an editor or a
; freelancer on a managed laptop who very often cannot elevate. An installer that demands
; administrator rights is, for a meaningful share of the audience, an installer that does
; not work.
;
; Built by packaging/build.py, which passes the version and package directory:
;   ISCC /DMyAppVersion=1.0.0 /DPackageDir=...\dist\PreflightQC /O...\dist\installer installer.iss

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#ifndef PackageDir
  #define PackageDir "..\dist\PreflightQC"
#endif

#define MyAppName "PreflightQC"
#define MyAppExeName "PreflightQC.exe"
#define MyAppPublisher "PreflightQC"

[Setup]
AppId={{9F1D5A2C-6B84-4E31-9C77-2A5D4E8B31F0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion=0.1.0
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=PreflightQC-{#MyAppVersion}-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; No elevation. With PrivilegesRequired=lowest, {autopf} resolves to the per-user
; %LOCALAPPDATA%\Programs, so the whole install stays inside the user's profile.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; The licence page shows the EULA. LGPL obligations are met by the licenses/ folder that
; ships inside the application directory and by THIRD-PARTY-NOTICES.txt, both of which are
; also reachable from the product's About screen offline.
LicenseFile={#PackageDir}\licenses\EULA.txt
InfoAfterFile={#PackageDir}\licenses\THIRD-PARTY-NOTICES.txt

UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Everything the build produced, verbatim. The third-party binaries in bin\ and the Qt
; libraries in _internal\PySide6\ are copied unmodified and keep their own names --
; renaming or repacking either would breach the LGPL checklist (gate G-7).
Source: "{#PackageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Nothing here on purpose.
;
; Uninstall removes the application directory only. Custom client profiles, saved
; configuration and logs live under %LOCALAPPDATA%\PreflightQC and are deliberately left
; behind: a profile is a client's delivery specification that the user authored, and
; deleting someone's work during an uninstall is not a decision an installer should make.
; This behaviour is documented for criterion P13-A12.
