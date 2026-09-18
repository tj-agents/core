[CmdletBinding()]
param(
    [string]$UserProfilePath = $env:USERPROFILE,
    [switch]$Disabled,
    [switch]$Start,
    [switch]$Preview
)

$ErrorActionPreference = 'Stop'
$taskName = 'CLI Session AutoSave'
$listenerPath = Join-Path $UserProfilePath 'cli-session-shutdown-listener.ps1'
$powershellPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$listenerPath`""
$repetitionInterval = New-TimeSpan -Minutes 1
$restartInterval = New-TimeSpan -Minutes 1
$startBoundary = (Get-Date).AddMinutes(1)
$definition = [pscustomobject][ordered]@{
    TaskName = $taskName
    Execute = $powershellPath
    Arguments = $arguments
    UserId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    StartBoundary = $startBoundary
    RepetitionInterval = $repetitionInterval
    RestartCount = 999
    RestartInterval = $restartInterval
    MultipleInstances = 'IgnoreNew'
    Enabled = -not $Disabled
}

if ($Preview) {
    return $definition
}
if ($Start -and $Disabled) {
    throw 'The autosave task cannot be started while it is disabled.'
}
if (-not (Test-Path -LiteralPath $listenerPath -PathType Leaf)) {
    throw "The installed autosave listener does not exist: $listenerPath"
}

$action = New-ScheduledTaskAction -Execute $definition.Execute -Argument $definition.Arguments
$trigger = New-ScheduledTaskTrigger -Once -At $definition.StartBoundary -RepetitionInterval $definition.RepetitionInterval
$settingsParameters = @{
    AllowStartIfOnBatteries = $true
    DontStopIfGoingOnBatteries = $true
    ExecutionTimeLimit = [timespan]::Zero
    Hidden = $true
    MultipleInstances = $definition.MultipleInstances
    RestartCount = $definition.RestartCount
    RestartInterval = $definition.RestartInterval
    StartWhenAvailable = $true
}
if ($Disabled) { $settingsParameters.Disable = $true }
$settings = New-ScheduledTaskSettingsSet @settingsParameters
$principal = New-ScheduledTaskPrincipal -UserId $definition.UserId -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Continuously protects live Claude Code and Codex CLI conversations for recovery.'
Register-ScheduledTask -TaskName $definition.TaskName -InputObject $task -Force | Out-Null
if ($Start) { Start-ScheduledTask -TaskName $definition.TaskName }

$installed = Get-ScheduledTask -TaskName $definition.TaskName
$info = Get-ScheduledTaskInfo -TaskName $definition.TaskName
[pscustomobject][ordered]@{
    TaskName = $installed.TaskName
    State = [string]$installed.State
    Enabled = [string]$installed.State -ne 'Disabled'
    NextRunTime = $info.NextRunTime
    Execute = [string]$installed.Actions.Execute
    Arguments = [string]$installed.Actions.Arguments
}
