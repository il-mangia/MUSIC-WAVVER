#define MyAppName "MUSIC WAVVER"
#define MyAppVersion "6.0"
#define MyAppPublisher "Il Mangia"
#define MyAppExeName "MUSIC WAVVER.exe"
#define MyLauncherExeName "Launcher.exe"

[Setup]
; AppId deve rimanere costante tra le versioni per permettere il rilevamento dell'aggiornamento
AppId={{8B1D4F3A-7E2C-4B9A-9D8E-0F1A2B3C4D5E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Richiede privilegi ADMIN
PrivilegesRequired=admin
; Se vuoi un'icona personalizzata per l'installer, converti Logo.png in Logo.ico
; SetupIconFile=Logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "MUSIC WAVVER.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "Launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "Logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "languages.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "themes.json"; DestDir: "{app}"; Flags: ignoreversion
; Cartella _internal fondamentale
Source: "_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyLauncherExeName}"; IconFilename: "{app}\Logo.png"
Name: "{group}\{#MyAppName} (Direct)"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\Logo.png"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyLauncherExeName}"; Tasks: desktopicon; IconFilename: "{app}\Logo.png"

[Run]
Filename: "{app}\{#MyLauncherExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
/////////////////////////////////////////////////////////////////////
// Funzione per disinstallare automaticamente versioni precedenti
/////////////////////////////////////////////////////////////////////
function GetUninstallString(): String;
var
  sUninstPath: String;
  sUninstString: String;
begin
  sUninstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + '{#SetupSetting("AppId")}' + '_is1';
  sUninstString := '';
  if not RegQueryStringValue(HKLM, sUninstPath, 'UninstallString', sUninstString) then
    RegQueryStringValue(HKCU, sUninstPath, 'UninstallString', sUninstString);
  Result := sUninstString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function InitializeSetup(): Boolean;
var
  V: Integer;
  sUninstString: String;
begin
  Result := True;
  if IsUpgrade() then
  begin
    sUninstString := GetUninstallString();
    sUninstString := RemoveQuotes(sUninstString);
    if MsgBox('È stata rilevata una versione precedente di MUSIC WAVVER. Verra disinstallata prima di procedere con la versione 6. Continuare?', mbInformation, MB_YESNO) = IDYES then
    begin
      Exec(sUninstString, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_SHOW, ewWaitUntilTerminated, V);
    end
    else
    begin
      Result := False;
    end;
  end;
end;