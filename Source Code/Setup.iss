; ==============================================
; MUSIC WAVVER 4.5 INSTALLER
; BY IL MANGIA - MAXATO FIXED
; ==============================================

#define MyAppName "MUSIC WAVVER"
#define MyAppVersion "4.5"
#define MyAppPublisher "Il Mangia"
#define MyAppURL "https://github.com/ilmangia/music-wavver"

#define LauncherExe "Launcher.exe"
#define MainExe "MUSIC WAVVER.exe"

#define SourceDir "E:\Documenti\VScode\Music Wavver\dist\Win"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

UsePreviousAppDir=yes
AllowNoIcons=yes
PrivilegesRequired=admin
MinVersion=6.1
ArchitecturesInstallIn64BitMode=x64

Compression=lzma2/max
SolidCompression=yes

CloseApplications=yes
RestartApplications=no

OutputDir=Output
OutputBaseFilename=MUSIC_WAVVER_4.5_Setup
SetupIconFile={#SourceDir}\Logo.ico

UninstallDisplayIcon={app}\{#LauncherExe}

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; --- EXE PRINCIPALI ---
Source: "{#SourceDir}\{#LauncherExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\{#MainExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\playlists.py"; DestDir: "{app}"; Flags: ignoreversion

; --- FILE SUPPORTO ---
Source: "{#SourceDir}\languages.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\Logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\Logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\playlist_urls.log"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\ytdownloader.log"; DestDir: "{app}"; Flags: ignoreversion

; NON includiamo settings.json per preservarlo

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#LauncherExe}"; IconFilename: "{app}\Logo.ico"
Name: "{group}\Disinstalla {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#LauncherExe}"; IconFilename: "{app}\Logo.ico"

[Run]
Filename: "{app}\{#LauncherExe}"; Description: "Avvia {#MyAppName}"; Flags: nowait postinstall

[Dirs]
Name: "{app}"; Permissions: users-full

[Registry]
Root: HKA; Subkey: "Software\Classes\MUSICWAVVER.Document"; ValueType: string; ValueName: ""; ValueData: "MUSIC WAVVER Document"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\MUSICWAVVER.Document\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#LauncherExe},0"
Root: HKA; Subkey: "Software\Classes\MUSICWAVVER.Document\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#LauncherExe}"" ""%1"""

[Code]

var
  SettingsBackup: string;

procedure CurStepChanged(CurStep: TSetupStep);
var
  SettingsPath: string;
begin
  if CurStep = ssInstall then
  begin
    SettingsPath := ExpandConstant('{app}\settings.json');
    SettingsBackup := ExpandConstant('{tmp}\settings.json');

    if FileExists(SettingsPath) then
    begin
      if FileCopy(SettingsPath, SettingsBackup, False) then
        Log('Backup settings.json creato prima update');
    end;
  end;

  if CurStep = ssPostInstall then
  begin
    SettingsPath := ExpandConstant('{app}\settings.json');

    if FileExists(SettingsBackup) then
    begin
      if FileExists(SettingsPath) then
        DeleteFile(SettingsPath);

      if FileCopy(SettingsBackup, SettingsPath, False) then
        Log('settings.json ripristinato dopo update');
    end;
  end;
end;
