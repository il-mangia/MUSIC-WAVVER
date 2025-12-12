; MUSIC WAVVER Installer Script
; BY IL MANGIA - 29/11/2025 (aggiornato per includere app.exe)

#define MyAppName "MUSIC WAVVER"
#define MyAppVersion "3.0"
#define MyAppPublisher "Il Mangia"
#define MyAppURL "https://github.com/ilmangia/music-wavver"
#define MyAppExeName "Launcher.exe"
#define MyOtherExeName "app.exe"
#define SourceDir "C:\Users\aless\OneDrive\Documenti\VScode\Music Wavver\dist"

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
AllowNoIcons=yes
LicenseFile={#SourceDir}\license.txt
Compression=lzma2/max
SolidCompression=yes
OutputDir=Output
OutputBaseFilename=MUSIC_WAVVER_{#MyAppVersion}_Setup
SetupIconFile={#SourceDir}\logo.ico
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
MinVersion=6.1
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
italian.SettingsPreserved=Impostazioni salvate preservate
english.SettingsPreserved=Saved settings preserved

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; File principali
Source: "{#SourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\{#MyOtherExeName}"; DestDir: "{app}"; Flags: ignoreversion
; File di supporto
Source: "{#SourceDir}\languages.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\license.txt"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{#SourceDir}\license.txt'))
; NOTA: settings.json NON viene incluso per preservare le impostazioni esistenti

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\logo.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Funzione per preservare il file settings.json se esiste già
function ShouldSkipPage(CurPageID: Integer): Boolean;
begin
  Result := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  SettingsPath: string;
  OldSettingsPath: string;
begin
  if CurStep = ssPostInstall then
  begin
    SettingsPath := ExpandConstant('{app}\settings.json');
    OldSettingsPath := ExpandConstant('{app}\settings.json.old');
    
    if FileExists(OldSettingsPath) then
    begin
      if FileExists(SettingsPath) then
        DeleteFile(SettingsPath);
      RenameFile(OldSettingsPath, SettingsPath);
      Log('Ripristinato file settings.json esistente');
    end
    else if FileExists(SettingsPath) then
    begin
      FileCopy(SettingsPath, OldSettingsPath, False);
      Log('Backup del file settings.json esistente');
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  SettingsPath: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('Vuoi mantenere le impostazioni di MUSIC WAVVER per un eventuale reinstallazione?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      SettingsPath := ExpandConstant('{app}\settings.json');
      if FileExists(SettingsPath) then
      begin
        FileCopy(SettingsPath, ExpandConstant('{app}\settings.json.backup'), False);
        Log('Impostazioni salvate preservate in settings.json.backup');
      end;
    end;
  end;
end;

function InitializeSetup(): Boolean;
var
  SettingsPath: string;
  OldSettingsPath: string;
begin
  Result := True;
  SettingsPath := ExpandConstant('{app}\settings.json');
  OldSettingsPath := ExpandConstant('{app}\settings.json.old');
  
  if FileExists(SettingsPath) then
  begin
    if FileExists(OldSettingsPath) then
      DeleteFile(OldSettingsPath);
    FileCopy(SettingsPath, OldSettingsPath, False);
    Log('Backup del file settings.json esistente per aggiornamento');
  end;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;

[Registry]
Root: HKA; Subkey: "Software\Classes\MUSICWAVVER.Document"; ValueType: string; ValueName: ""; ValueData: "MUSIC WAVVER Document"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\MUSICWAVVER.Document\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\MUSICWAVVER.Document\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
