[CmdletBinding(SupportsShouldProcess)]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'session_close.ps1')

$ownHost = Resolve-OwnHost
if (-not $ownHost) {
    throw 'close: cannot resolve an owning claude/codex host process ancestor.'
}
$entry = Get-OwnRegistryEntry -OwnHost $ownHost
$sessionId = Get-EntryProperty -Entry $entry -Name 'session_id'
$attachmentCwd = Get-EntryProperty -Entry $entry -Name 'cwd'
if (-not $sessionId -or -not $attachmentCwd -or
    -not (Test-UnderOrEqual -Candidate (Get-Location).Path -Root $attachmentCwd)) {
    throw 'close: no verified registry attachment for this host and current directory; nothing was closed.'
}
$attachment = [pscustomobject]@{
    Attached = $true
    Title = Get-EntryProperty -Entry $entry -Name 'title'
}
$parentShell = Get-ParentShellHost -OwnHost $ownHost
$targetDirectory = $attachmentCwd
try {
    $gitRoot = & git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitRoot) { $targetDirectory = (@($gitRoot)[0]).Trim() }
}
catch {
}
if (-not $PSCmdlet.ShouldProcess("host pid $($ownHost.Pid)", 'Close this session and retain its checkout')) {
    return
}
$stateDirectory = Get-StateDirectory
$resultPath = Join-Path $stateDirectory ('merge-cleanup/results/' + [guid]::NewGuid().ToString('N') + '.json')
$commandParts = @(
    'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File',
    (Join-Path $PSScriptRoot 'finish_reaper.ps1'), '-CloseOnly',
    '-HostPid', $ownHost.Pid, '-HostStart', $ownHost.Started,
    '-SessionId', $sessionId, '-Worktree', $targetDirectory,
    '-Result', $resultPath, '-StateDirectory', $stateDirectory
)
if ($parentShell) {
    $commandParts += @('-ParentPid', $parentShell.Pid, '-ParentStart', $parentShell.Started)
}
if (-not (Start-DetachedReaper -CommandLine (Format-CommandLine -Parts $commandParts))) {
    throw 'close: could not start the session exit observer; nothing was closed.'
}
$deadline = [DateTime]::UtcNow.AddSeconds((Get-EnvDouble -Name 'AGENT_FINISH_SPAWN_TIMEOUT_SECONDS' -Default 15.0))
$started = $false
while ([DateTime]::UtcNow -lt $deadline) {
    $record = Read-JsonFile -Path $resultPath
    if ($record -and (Get-EntryProperty -Entry $record -Name 'started')) { $started = $true; break }
    Start-Sleep -Milliseconds 100
}
if (-not $started) {
    throw 'close: the session exit observer did not confirm startup; nothing was closed.'
}
Invoke-SessionClose -CloseMode $env:AGENT_FINISH_CLOSE_MODE -Attachment $attachment -OwnHost $ownHost -ParentShell $parentShell
