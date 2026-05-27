Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\.."
shell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\run_web.ps1", 0, False
