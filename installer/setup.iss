[Setup]
AppName=XAUUSD AI Trading System
AppVersion=1.0
DefaultDirName={pf}\XAUUSD Trading
DefaultGroupName=XAUUSD Trading
OutputDir=output
OutputBaseFilename=XAUUSD_Trading_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=..\resources\icons\app_icon.ico

[Files]
Source: "..\dist\XAUUSD_Trading_System.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\XAUUSD_README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\XAUUSD Trading System"; Filename: "{app}\XAUUSD_Trading_System.exe"
Name: "{commondesktop}\XAUUSD Trading"; Filename: "{app}\XAUUSD_Trading_System.exe"

[Run]
Filename: "{app}\XAUUSD_Trading_System.exe"; Description: "启动应用"; Flags: postinstall nowait skipifsilent
