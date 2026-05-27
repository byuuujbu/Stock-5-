$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LauncherPath = Join-Path $ProjectRoot "scripts\run_web_hidden.vbs"
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "DomesticStockSelectionWeb.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$LauncherPath`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.WindowStyle = 7
$Shortcut.Description = "Run local stock selection dashboard web server at Windows logon."
$Shortcut.Save()

Start-Process -FilePath "wscript.exe" -ArgumentList "`"$LauncherPath`"" -WindowStyle Hidden

Write-Host "Created startup shortcut: $ShortcutPath"
Write-Host "Started web server launcher."
