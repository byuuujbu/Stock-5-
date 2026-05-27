$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$TaskName = "DomesticStockSelectionWeb"
$ScriptPath = Join-Path $ProjectRoot "scripts\run_web.ps1"
$LauncherPath = Join-Path $ProjectRoot "scripts\run_web_hidden.vbs"

$Action = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "`"$LauncherPath`""

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Days 365)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Run local stock selection dashboard web server at user logon." `
        -Force
} catch {
    throw
}

try {
    Start-ScheduledTask -TaskName $TaskName
} catch {
    schtasks.exe /Run /TN $TaskName | Out-Host
}

Write-Host "Registered and started task: $TaskName"
