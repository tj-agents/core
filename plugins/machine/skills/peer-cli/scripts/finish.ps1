<#
.SYNOPSIS
Close out a completed delivery: remove its worktree and branch, then close this session's own CLI.

.DESCRIPTION
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File finish.ps1`, run with no arguments from inside
the merged worktree, is `engineering:merge` Step 5's self-close path: the target is this process's own
`git rev-parse --show-toplevel`, which the preflight attachment check already requires to be this
session's own worktree. It requires a fresh `removable` verdict from `cleanup_proof.py` for exactly that
worktree, whose recorded `head`/`branch` must still match the worktree's actual `HEAD` (a commit landed
after `cleanup_proof.py` ran otherwise re-run it), resolves the claude/codex host this session is actually
running under, spawns a detached reaper that waits for that host (and, if its parent process is a shell,
that shell too) to exit and then runs the approved `git worktree remove`/`branch -d|-D` from the primary
checkout, and only then closes this session's own tab or process.

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
. (Join-Path $PSScriptRoot 'session_close.ps1')

function Get-NormalizedPathForm {
    param([string] $Path)

    if (-not $Path) { return $null }
    $full = [IO.Path]::GetFullPath($Path)
    return (($full -replace '\\', '/').TrimEnd('/')).ToLowerInvariant()
}

function Get-WorktreeComparisonForms {
    param([string] $Path)

    $forms = New-Object System.Collections.Generic.List[string]
    $direct = Get-NormalizedPathForm -Path $Path
    if ($direct) { $forms.Add($direct) }
    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop
        $targetProperty = $item.PSObject.Properties['Target']
        $targets = if ($targetProperty) { $targetProperty.Value } else { $null }
        foreach ($target in @($targets)) {
            if (-not $target) { continue }
            $resolvedTarget = $target
            if (-not [IO.Path]::IsPathRooted($resolvedTarget)) {
                $resolvedTarget = Join-Path (Split-Path -Parent $item.FullName) $resolvedTarget
            }
            $form = Get-NormalizedPathForm -Path $resolvedTarget
            if ($form) { $forms.Add($form) }
        }
    }
    catch {
    }
    return $forms
}

function Find-ReceiptPath {
    param([string] $StateDirectory, [string] $ResolvedWorktree)

    $directory = Join-Path $StateDirectory 'merge-cleanup/receipts'
    if (-not (Test-Path -LiteralPath $directory)) { return $null }
    $targetForms = @(Get-WorktreeComparisonForms -Path $ResolvedWorktree)
    $bestPath = $null
    $bestRecordedAt = $null
    foreach ($file in Get-ChildItem -LiteralPath $directory -Filter '*.json' -File) {
        $data = Read-JsonFile -Path $file.FullName
        if (-not $data) { continue }
        $recorded = Get-EntryProperty -Entry $data -Name 'worktree'
        if (-not $recorded) { continue }
        $recordedForms = @(Get-WorktreeComparisonForms -Path $recorded)
        $matches = $false
        foreach ($form in $recordedForms) {
            if ($targetForms -contains $form) { $matches = $true; break }
        }
        if (-not $matches) { continue }
        $recordedAt = [double] (Get-EntryProperty -Entry $data -Name 'recorded_at')
        if ($null -eq $bestRecordedAt -or $recordedAt -gt $bestRecordedAt) {
            $bestPath = $file.FullName
            $bestRecordedAt = $recordedAt
        }
    }
    return $bestPath
}

function Get-ResolvedWorktree {
    param([string] $Path)

    $item = Get-Item -LiteralPath $Path -ErrorAction Stop
    return $item.FullName.TrimEnd('\')
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

function Test-WorktreeMatchesReceipt {
    param([string] $ResolvedWorktree, [pscustomobject] $Receipt)

    $headOutput = & git -C $ResolvedWorktree rev-parse HEAD 2>$null
    $headExit = $LASTEXITCODE
    $branchOutput = & git -C $ResolvedWorktree rev-parse --abbrev-ref HEAD 2>$null
    $branchExit = $LASTEXITCODE
    if ($headExit -ne 0 -or $branchExit -ne 0) { return $false }
    $currentHead = (@($headOutput)[0]).Trim()
    $currentBranch = (@($branchOutput)[0]).Trim()
    $receiptHead = Get-EntryProperty -Entry $Receipt -Name 'head'
    $receiptBranch = Get-EntryProperty -Entry $Receipt -Name 'branch'
    return ($currentHead -eq $receiptHead) -and ($currentBranch -eq $receiptBranch)
}

function Get-FreshRemovableReceipt {
    param([string] $StateDirectory, [string] $ResolvedWorktree)

    $path = Find-ReceiptPath -StateDirectory $StateDirectory -ResolvedWorktree $ResolvedWorktree
    $receipt = if ($path) { Read-JsonFile -Path $path } else { $null }
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
    if (-not (Test-WorktreeMatchesReceipt -ResolvedWorktree $ResolvedWorktree -Receipt $receipt)) {
        throw "finish: '$ResolvedWorktree' HEAD/branch no longer match the receipt cleanup_proof.py recorded " +
            "(a commit or branch change landed after it ran). Run cleanup_proof.py again."
    }
    return $receipt
}

$startingLocation = (Get-Location).Path
$targetWorktree = Resolve-TargetWorktree -Provided $Worktree
$resolvedWorktree = Get-ResolvedWorktree -Path $targetWorktree
$stateDirectory = Get-StateDirectory
$receipt = Get-FreshRemovableReceipt -StateDirectory $stateDirectory -ResolvedWorktree $resolvedWorktree
if ((Get-NormalizedPathForm $resolvedWorktree) -eq
    (Get-NormalizedPathForm (Get-EntryProperty -Entry $receipt -Name 'primary'))) {
    throw 'finish: the primary checkout cannot be removed; use close.ps1 to retain it.'
}

$ownHost = Resolve-OwnHost
if (-not $ownHost) {
    throw 'finish: cannot resolve an owning claude/codex host process ancestor from this session.'
}

$attachment = Get-TitleAndAttachment -ResolvedWorktree $resolvedWorktree -StartingLocation $startingLocation -OwnHost $ownHost
if (-not $attachment.Attached) {
    throw "finish: '$resolvedWorktree' is not this session's own attachment; refusing to close or remove it."
}
if (Test-OtherLiveSessionClaimsWorktree -ResolvedWorktree $resolvedWorktree -OwnHost $ownHost) {
    throw "finish: another live registered session's cwd is under '$resolvedWorktree'; refusing to close or remove it."
}

$parentShell = Get-ParentShellHost -OwnHost $ownHost

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

$resultPath = Join-Path $stateDirectory ('merge-cleanup/results/' + [guid]::NewGuid().ToString('N') + '.json')

$reaperScript = Join-Path $PSScriptRoot 'finish_reaper.ps1'
$commandParts = @(
    'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $reaperScript,
    '-HostPid', $ownHost.Pid, '-HostStart', $ownHost.Started,
    '-Head', (Get-EntryProperty -Entry $receipt -Name 'head'),
    '-Primary', (Get-EntryProperty -Entry $receipt -Name 'primary'),
    '-Worktree', $resolvedWorktree,
    '-Branch', (Get-EntryProperty -Entry $receipt -Name 'branch'),
    '-Default', (Get-EntryProperty -Entry $receipt -Name 'default'),
    '-Result', $resultPath,
    '-StateDirectory', $stateDirectory
)
if ($parentShell) {
    $commandParts += @('-ParentPid', $parentShell.Pid, '-ParentStart', $parentShell.Started)
}
$commandLine = Format-CommandLine -Parts $commandParts

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

Invoke-SessionClose -CloseMode $env:AGENT_FINISH_CLOSE_MODE -Attachment $attachment -OwnHost $ownHost -ParentShell $parentShell
