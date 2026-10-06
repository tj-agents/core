<#
.SYNOPSIS
Close out a completed delivery: remove its worktree and branch, then close this session's own CLI.

.DESCRIPTION
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File finish.ps1`, run with no arguments from inside
the merged worktree, is `engineering:merge` Step 5's self-close path: the target is this process's own
`git rev-parse --show-toplevel`, which the preflight attachment check already requires to be this
session's own worktree. It requires a fresh `removable` verdict from `cleanup_proof.py` for exactly that
worktree, resolves the claude/codex host this session is actually running under, spawns a detached reaper
that waits for that host to exit and then runs the approved `git worktree remove`/`branch -d|-D` from the
primary checkout, and only then closes this session's own tab or process.

`-Worktree <target>` overrides the target explicitly; it exists for tests, not the documented invocation,
since a Claude auto-mode allow rule for this script can only match an exact, argument-free command.

The reaper is spawned through `Invoke-CimMethod Win32_Process Create`, which parents it to the WMI
provider host rather than this process or any job object it sits inside — the property that lets it
outlive the very tab-close that follows it. A `schtasks /create /sc once` one-shot is the fallback when
CIM is unavailable. Nothing is closed until the reaper proves it started by writing to its result file;
any failure before that point aborts without closing or removing anything.

`AGENT_CLI_HOST_NAMES` overrides the claude/codex executable-stem set for tests, mirroring
`register_session.py`. `AGENT_FINISH_CLOSE_MODE=process` forces the Stop-Process close path even when a
tab title is recorded, so a test can close a fake host process without ever touching Windows Terminal.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Position = 0)]
    [string] $Worktree
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ReceiptMaxAgeSeconds = 3600.0

function Get-StateDirectory {
    $override = $env:AGENT_STATE_DIRECTORY
    if ($override) { return $override }
    return (Join-Path $HOME '.agents-state')
}

function Get-EntryProperty {
    param($Entry, [string] $Name)

    if ($null -eq $Entry) { return $null }
    $property = $Entry.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-Sha256Hex {
    param([string] $Text)

    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha256.ComputeHash($bytes)
    }
    finally {
        $sha256.Dispose()
    }
    return -join ($hashBytes | ForEach-Object { $_.ToString('x2') })
}

function Get-WorktreeDigest {
    param([string] $ResolvedWorktree)

    $posix = $ResolvedWorktree -replace '\\', '/'
    return Get-Sha256Hex -Text $posix
}

function Get-ReceiptPath {
    param([string] $ResolvedWorktree)

    $digest = Get-WorktreeDigest -ResolvedWorktree $ResolvedWorktree
    return Join-Path (Get-StateDirectory) "merge-cleanup/receipts/$digest.json"
}

function Get-ResolvedWorktree {
    param([string] $Path)

    $item = Get-Item -LiteralPath $Path -ErrorAction Stop
    return $item.FullName.TrimEnd('\')
}

function Read-JsonFile {
    param([string] $Path)

    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

function Test-UnderOrEqual {
    param([string] $Candidate, [string] $Root)

    if (-not $Candidate -or -not $Root) { return $false }
    $c = ($Candidate.TrimEnd('\', '/') -replace '\\', '/').ToLowerInvariant()
    $r = ($Root.TrimEnd('\', '/') -replace '\\', '/').ToLowerInvariant()
    return ($c -eq $r) -or $c.StartsWith("$r/")
}

function Resolve-TargetWorktree {
    param([string] $Provided)

    if ($Provided) { return $Provided }
    $toplevel = & git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $toplevel) {
        throw 'finish: no -Worktree was given and the current directory is not inside a Git worktree ' +
            '(git rev-parse --show-toplevel failed). Run finish.ps1 with no arguments from inside the merged worktree.'
    }
    return (@($toplevel)[0]).Trim()
}

function Get-FreshRemovableReceipt {
    param([string] $ResolvedWorktree)

    $path = Get-ReceiptPath -ResolvedWorktree $ResolvedWorktree
    $receipt = Read-JsonFile -Path $path
    if (-not $receipt) {
        throw "finish: no cleanup_proof.py receipt recorded for '$ResolvedWorktree'. Run cleanup_proof.py first."
    }
    if ((Get-EntryProperty -Entry $receipt -Name 'verdict') -ne 'removable') {
        throw "finish: the receipt for '$ResolvedWorktree' is not 'removable'. Run cleanup_proof.py again."
    }
    $recordedAt = Get-EntryProperty -Entry $receipt -Name 'recorded_at'
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0
    if ($null -eq $recordedAt -or ($now - [double] $recordedAt) -gt $ReceiptMaxAgeSeconds) {
        throw "finish: the receipt for '$ResolvedWorktree' is stale (older than one hour). Run cleanup_proof.py again."
    }
    $receiptWorktree = Get-EntryProperty -Entry $receipt -Name 'worktree'
    if ($receiptWorktree -and (($receiptWorktree -replace '\\', '/') -ne ($ResolvedWorktree -replace '\\', '/'))) {
        throw "finish: the receipt is for '$receiptWorktree', not '$ResolvedWorktree'."
    }
    return $receipt
}

function Get-HostNames {
    $override = $env:AGENT_CLI_HOST_NAMES
    if (-not $override) { return @('claude', 'codex') }
    $names = @($override -split ',' | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ })
    if ($names.Count -eq 0) { return @('claude', 'codex') }
    return $names
}

function ConvertTo-UnixTime {
    param([DateTime] $Value)

    return ([DateTimeOffset]($Value.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0
}

function Resolve-OwnHost {
    param([int] $DepthCap = 10)

    $hostNames = Get-HostNames
    $current = $PID
    $seen = @{}
    for ($depth = 0; $depth -lt $DepthCap; $depth++) {
        if ($null -eq $current -or $seen.ContainsKey($current)) { return $null }
        $seen[$current] = $true
        $process = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $current" -ErrorAction SilentlyContinue
        if (-not $process) { return $null }
        $stem = [IO.Path]::GetFileNameWithoutExtension($process.Name).ToLowerInvariant()
        if ($hostNames -contains $stem) {
            return [pscustomobject]@{
                Pid     = [int] $process.ProcessId
                Started = ConvertTo-UnixTime -Value $process.CreationDate
            }
        }
        $current = [int] $process.ParentProcessId
    }
    return $null
}

function Get-RecordedSessionEntries {
    $directory = Join-Path (Get-StateDirectory) 'cli-sessions'
    if (-not (Test-Path -LiteralPath $directory)) { return @() }
    return @(Get-ChildItem -LiteralPath $directory -Filter '*.json' -File | ForEach-Object {
        try { Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $null }
    } | Where-Object { $_ })
}

function Get-TitleAndAttachment {
    param(
        [string] $ResolvedWorktree,
        [string] $StartingLocation,
        [pscustomobject] $OwnHost
    )

    $selfEntry = $null
    $titleEntry = $null
    foreach ($entry in (Get-RecordedSessionEntries)) {
        $cwd = Get-EntryProperty -Entry $entry -Name 'cwd'
        if (-not (Test-UnderOrEqual -Candidate $cwd -Root $ResolvedWorktree)) { continue }
        if (-not $titleEntry) { $titleEntry = $entry }
        $entryPid = Get-EntryProperty -Entry $entry -Name 'pid'
        $entryStart = Get-EntryProperty -Entry $entry -Name 'pid_started_at'
        if ($entryPid -eq $OwnHost.Pid -and $null -ne $entryStart -and
            [math]::Abs([double] $entryStart - $OwnHost.Started) -le 2.0) {
            $selfEntry = $entry
        }
    }

    $attached = ($null -ne $selfEntry) -or (Test-UnderOrEqual -Candidate $StartingLocation -Root $ResolvedWorktree)
    [pscustomobject]@{
        Attached = $attached
        Title    = if ($titleEntry) { Get-EntryProperty -Entry $titleEntry -Name 'title' } else { $null }
    }
}

function Format-CommandLineArgument {
    param([string] $Value)

    $text = [string] $Value
    if ($text -eq '') { return '""' }
    if ($text -match '[\s"]') { return '"' + ($text -replace '"', '\"') + '"' }
    return $text
}

function Format-CommandLine {
    param([string[]] $Parts)

    return ($Parts | ForEach-Object { Format-CommandLineArgument $_ }) -join ' '
}

function Start-DetachedReaper {
    param([string] $CommandLine)

    try {
        $result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create `
            -Arguments @{ CommandLine = $CommandLine } -ErrorAction Stop
        if ($result.ReturnValue -eq 0) { return $true }
    }
    catch {
    }

    $taskName = 'agent-finish-reaper-' + [guid]::NewGuid().ToString('N')
    try {
        & schtasks.exe /create /tn $taskName /sc once /st 00:00 /rl highest /f /tr $CommandLine 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { return $false }
        & schtasks.exe /run /tn $taskName 2>$null | Out-Null
        $ran = $LASTEXITCODE -eq 0
        & schtasks.exe /delete /tn $taskName /f 2>$null | Out-Null
        return $ran
    }
    catch {
        return $false
    }
}

function Get-EnvDouble {
    param([string] $Name, [double] $Default)

    $value = [Environment]::GetEnvironmentVariable($Name)
    if (-not $value) { return $Default }
    $parsed = 0.0
    if ([double]::TryParse($value, [ref] $parsed)) { return $parsed }
    return $Default
}

$startingLocation = (Get-Location).Path
$targetWorktree = Resolve-TargetWorktree -Provided $Worktree
$resolvedWorktree = Get-ResolvedWorktree -Path $targetWorktree
$stateDirectory = Get-StateDirectory
$receipt = Get-FreshRemovableReceipt -ResolvedWorktree $resolvedWorktree

$ownHost = Resolve-OwnHost
if (-not $ownHost) {
    throw 'finish: cannot resolve an owning claude/codex host process ancestor from this session.'
}

$attachment = Get-TitleAndAttachment -ResolvedWorktree $resolvedWorktree -StartingLocation $startingLocation -OwnHost $ownHost
if (-not $attachment.Attached) {
    throw "finish: '$resolvedWorktree' is not this session's own attachment; refusing to close or remove it."
}

# Release any lock this process holds on the target directory before the reaper tries to remove it -
# Windows refuses to delete a directory that is any process's current location.
$primary = Get-EntryProperty -Entry $receipt -Name 'primary'
if ($primary -and (Test-Path -LiteralPath $primary)) {
    Set-Location -LiteralPath $primary
}

if (-not $PSCmdlet.ShouldProcess($resolvedWorktree, 'Spawn the cleanup reaper and close this session')) {
    Write-Output "What if: would spawn the reaper for '$resolvedWorktree' and close this session (pid $($ownHost.Pid))."
    return
}

$resultPath = Join-Path $stateDirectory ("merge-cleanup/results/" + (Get-WorktreeDigest -ResolvedWorktree $resolvedWorktree) + '.json')
if (Test-Path -LiteralPath $resultPath) { Remove-Item -LiteralPath $resultPath -Force }

$reaperScript = Join-Path $PSScriptRoot 'finish_reaper.ps1'
$commandLine = Format-CommandLine -Parts @(
    'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $reaperScript,
    '-HostPid', $ownHost.Pid, '-HostStart', $ownHost.Started,
    '-Primary', (Get-EntryProperty -Entry $receipt -Name 'primary'),
    '-Worktree', $resolvedWorktree,
    '-Branch', (Get-EntryProperty -Entry $receipt -Name 'branch'),
    '-Default', (Get-EntryProperty -Entry $receipt -Name 'default'),
    '-Result', $resultPath,
    '-StateDirectory', $stateDirectory
)

if (-not (Start-DetachedReaper -CommandLine $commandLine)) {
    throw 'finish: could not spawn the cleanup reaper; neither CIM process creation nor the schtasks fallback succeeded.'
}

$spawnTimeoutSeconds = Get-EnvDouble -Name 'AGENT_FINISH_SPAWN_TIMEOUT_SECONDS' -Default 5.0
$deadline = [DateTime]::UtcNow.AddSeconds($spawnTimeoutSeconds)
$started = $false
while ([DateTime]::UtcNow -lt $deadline) {
    $record = Read-JsonFile -Path $resultPath
    if ($record -and (Get-EntryProperty -Entry $record -Name 'started')) { $started = $true; break }
    Start-Sleep -Milliseconds 100
}
if (-not $started) {
    throw "finish: the reaper did not confirm it started within $spawnTimeoutSeconds seconds; nothing was closed."
}

$closeMode = $env:AGENT_FINISH_CLOSE_MODE
if ($closeMode -eq 'process') {
    Stop-Process -Id $ownHost.Pid -Force
    Write-Output "finish: closed host pid $($ownHost.Pid) directly (AGENT_FINISH_CLOSE_MODE=process)."
}
elseif ($attachment.Title) {
    & (Join-Path $PSScriptRoot 'close-tab.ps1') $attachment.Title -Force
}
else {
    Stop-Process -Id $ownHost.Pid -Force
    Write-Output "finish: closed host pid $($ownHost.Pid) directly (no recorded tab title)."
}
