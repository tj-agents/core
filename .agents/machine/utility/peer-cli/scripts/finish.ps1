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
running under, then runs a three-phase started/accepted/armed handshake (`Invoke-ReaperHandshake`) with a
detached reaper before closing this session's own tab or process.

`-Worktree <target>` overrides the target explicitly; it exists for tests, not the documented invocation,
since a Claude auto-mode allow rule for this script can only match an exact, argument-free command.

The reaper is spawned through `Invoke-CimMethod Win32_Process Create`, which parents it to the WMI
provider host rather than this process or any job object it sits inside — the property that lets it
outlive the very tab-close that follows it. A `schtasks /create /sc once` one-shot is the fallback when
CIM is unavailable. The reaper is inert until explicitly accepted: it writes a `started` record (its own
pid and start time) and waits; this process validates that record's identity against the live invocation,
re-checks the receipt and shared-claims preflight, then writes `.accepted` and waits for the reaper's
`.armed` acknowledgement before closing anything. Any failure at any phase - a failed spawn, an
unconfirmed, stale or foreign `started` record, a refreshed preflight check that now fails, or a missing
`.armed` acknowledgement - writes `.cancelled`, best-effort kills a matching reaper by its invocation GUID,
and aborts without closing or removing anything. Once armed, the reaper re-checks `.cancelled` again
immediately before touching the worktree, so a late cancellation still wins. `-AcceptTimeoutSeconds` on the
reaper's command line (from `AGENT_FINISH_ACCEPT_TIMEOUT_SECONDS`) carries the accept bound, since a
CIM-spawned child inherits no environment.

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

function Get-EpochSeconds {
    return [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0
}

function Save-AtomicJson {
    param([string] $Path, [hashtable] $Data)

    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $json = $Data | ConvertTo-Json -Depth 6
    $temp = Join-Path $directory ('.' + (Split-Path -Leaf $Path) + '.' + $PID + '.tmp')
    [IO.File]::WriteAllText($temp, $json, (New-Object Text.UTF8Encoding $false))
    $attempts = 3
    for ($attempt = 1; $attempt -le $attempts; $attempt++) {
        try {
            if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
            Move-Item -LiteralPath $temp -Destination $Path
            return
        }
        catch {
            if ($attempt -eq $attempts) { throw }
            Start-Sleep -Milliseconds 100
        }
    }
}

function Invoke-HandshakeKillSweep {
    param([string] $ResultPath)

    $guid = [IO.Path]::GetFileNameWithoutExtension($ResultPath)
    $startedRecord = Read-JsonFile -Path $ResultPath
    $expectedStartedAt = $null
    if ($startedRecord) {
        $expectedStartedAt = ConvertTo-FiniteDouble -Value (Get-EntryProperty -Entry $startedRecord -Name 'reaper_started_at')
    }
    $candidates = @(Get-CimInstance -ClassName Win32_Process -Filter "Name = 'powershell.exe' AND CommandLine LIKE '%$guid%'" -ErrorAction SilentlyContinue)
    foreach ($candidate in $candidates) {
        $candidatePid = [int] $candidate.ProcessId
        if ($candidatePid -eq $PID) { continue }
        $commandLine = [string] $candidate.CommandLine
        if (-not $commandLine -or $commandLine -notlike "*$guid*") { continue }
        if ($null -ne $expectedStartedAt -and $candidate.CreationDate) {
            $candidateStartedAt = ConvertTo-UnixTime -Value $candidate.CreationDate
            if ([math]::Abs($candidateStartedAt - $expectedStartedAt) -gt 2.0) { continue }
        }
        Stop-Process -Id $candidatePid -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-HandshakeCancel {
    param([string] $ResultPath, [string] $Reason)

    Save-AtomicJson -Path "$ResultPath.cancelled" -Data @{ cancelled = (Get-EpochSeconds); reason = $Reason }
    if (Read-JsonFile -Path $ResultPath) {
        $evidenceDeadline = [DateTime]::UtcNow.AddSeconds(1.0)
        while ([DateTime]::UtcNow -lt $evidenceDeadline) {
            $record = Read-JsonFile -Path $ResultPath
            if ($record -and (Get-EntryProperty -Entry $record -Name 'status')) { break }
            Start-Sleep -Milliseconds 100
        }
    }
    Invoke-HandshakeKillSweep -ResultPath $ResultPath
    throw "finish: $Reason; nothing was closed."
}

function Invoke-ReaperHandshake {
    param(
        [string] $StateDirectory,
        [string] $ResolvedWorktree,
        [pscustomobject] $Receipt,
        [pscustomobject] $OwnHost,
        [pscustomobject] $ParentShell,
        [pscustomobject] $Attachment,
        [string] $ResultPath
    )

    $spawnEpoch = Get-EpochSeconds
    $reaperScript = Join-Path $PSScriptRoot 'finish_reaper.ps1'
    $spawnTimeoutSeconds = Get-EnvDouble -Name 'AGENT_FINISH_SPAWN_TIMEOUT_SECONDS' -Default 15.0
    $acceptTimeoutSeconds = Get-EnvDouble -Name 'AGENT_FINISH_ACCEPT_TIMEOUT_SECONDS' -Default 60.0
    $acceptTimeoutFloor = [math]::Max(60.0, $spawnTimeoutSeconds + 30.0)
    if ($acceptTimeoutSeconds -lt $acceptTimeoutFloor) { $acceptTimeoutSeconds = $acceptTimeoutFloor }
    $acceptTimeoutText = $acceptTimeoutSeconds.ToString([Globalization.CultureInfo]::InvariantCulture)
    $commandParts = @(
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $reaperScript,
        '-HostPid', $OwnHost.Pid, '-HostStart', $OwnHost.Started,
        '-Head', (Get-EntryProperty -Entry $Receipt -Name 'head'),
        '-Primary', (Get-EntryProperty -Entry $Receipt -Name 'primary'),
        '-Worktree', $ResolvedWorktree,
        '-Branch', (Get-EntryProperty -Entry $Receipt -Name 'branch'),
        '-Default', (Get-EntryProperty -Entry $Receipt -Name 'default'),
        '-Result', $ResultPath,
        '-StateDirectory', $StateDirectory,
        '-AcceptTimeoutSeconds', $acceptTimeoutText
    )
    if ($ParentShell) {
        $commandParts += @('-ParentPid', $ParentShell.Pid, '-ParentStart', $ParentShell.Started)
    }
    $commandLine = Format-CommandLine -Parts $commandParts

    $spawnResult = Start-DetachedReaper -CommandLine $commandLine
    if (-not ($spawnResult -is [hashtable])) {
        Invoke-HandshakeCancel -ResultPath $ResultPath `
            -Reason 'could not spawn the cleanup reaper; neither CIM process creation nor the schtasks fallback succeeded'
        return
    }
    $spawnPid = ConvertTo-PositiveInt -Value $spawnResult.ProcessId

    $confirmDeadline = [DateTime]::UtcNow.AddSeconds($spawnTimeoutSeconds)
    $validatedRecord = $null
    while ($true) {
        $record = Read-JsonFile -Path $ResultPath
        if ($null -ne $record) {
            $valid = $false
            try {
                $recordStarted = ConvertTo-FiniteDouble -Value (Get-EntryProperty -Entry $record -Name 'started')
                $recordHostPid = ConvertTo-PositiveInt -Value (Get-EntryProperty -Entry $record -Name 'host_pid')
                $recordWorktree = Get-EntryProperty -Entry $record -Name 'worktree'
                $recordReaperPid = ConvertTo-PositiveInt -Value (Get-EntryProperty -Entry $record -Name 'reaper_pid')
                $recordReaperStartedAt = ConvertTo-FiniteDouble -Value (Get-EntryProperty -Entry $record -Name 'reaper_started_at')

                $valid = ($null -ne $recordStarted) -and ($recordStarted -ge ($spawnEpoch - 2.0)) -and
                    ($null -ne $recordHostPid) -and ($recordHostPid -eq $OwnHost.Pid) -and
                    ($recordWorktree) -and ((Get-NormalizedPathForm $recordWorktree) -eq (Get-NormalizedPathForm $ResolvedWorktree)) -and
                    ($null -ne $recordReaperPid) -and ((-not $spawnPid) -or ($recordReaperPid -eq $spawnPid)) -and
                    ($null -ne $recordReaperStartedAt) -and ($recordReaperStartedAt -gt 0)
            }
            catch {
                $valid = $false
            }

            if ($valid) {
                $validatedRecord = [pscustomobject]@{ ReaperPid = $recordReaperPid; ReaperStartedAt = $recordReaperStartedAt }
                break
            }
            Invoke-HandshakeCancel -ResultPath $ResultPath -Reason 'the reaper startup record did not match this invocation'
            return
        }
        if ([DateTime]::UtcNow -ge $confirmDeadline) {
            Invoke-HandshakeCancel -ResultPath $ResultPath `
                -Reason "the reaper did not confirm it started within $spawnTimeoutSeconds seconds"
            return
        }
        Start-Sleep -Milliseconds 100
    }

    if (-not (Test-WorktreeMatchesReceipt -ResolvedWorktree $ResolvedWorktree -Receipt $Receipt)) {
        Invoke-HandshakeCancel -ResultPath $ResultPath `
            -Reason "'$ResolvedWorktree' HEAD/branch no longer match the receipt cleanup_proof.py recorded"
        return
    }
    if (Test-OtherLiveSessionClaimsWorktree -ResolvedWorktree $ResolvedWorktree -OwnHost $OwnHost) {
        Invoke-HandshakeCancel -ResultPath $ResultPath `
            -Reason "another live registered session's cwd is under '$ResolvedWorktree'"
        return
    }

    Save-AtomicJson -Path "$ResultPath.accepted" -Data @{
        accepted          = (Get-EpochSeconds)
        reaper_pid        = $validatedRecord.ReaperPid
        reaper_started_at = $validatedRecord.ReaperStartedAt
        host_pid          = $OwnHost.Pid
    }

    $armedTimeoutSeconds = Get-EnvDouble -Name 'AGENT_FINISH_ARMED_TIMEOUT_SECONDS' -Default 10.0
    $armedDeadline = [DateTime]::UtcNow.AddSeconds($armedTimeoutSeconds)
    $armed = $false
    while ([DateTime]::UtcNow -lt $armedDeadline) {
        $armedRecord = Read-JsonFile -Path "$ResultPath.armed"
        if ($armedRecord) {
            $armedPid = ConvertTo-PositiveInt -Value (Get-EntryProperty -Entry $armedRecord -Name 'reaper_pid')
            if ($null -ne $armedPid -and $armedPid -eq $validatedRecord.ReaperPid) { $armed = $true; break }
        }
        Start-Sleep -Milliseconds 100
    }
    if (-not $armed) {
        Invoke-HandshakeCancel -ResultPath $ResultPath -Reason 'the reaper did not acknowledge acceptance in time'
        return
    }

    try {
        Invoke-SessionClose -CloseMode $env:AGENT_FINISH_CLOSE_MODE -Attachment $Attachment -OwnHost $OwnHost -ParentShell $ParentShell
    }
    catch {
        Save-AtomicJson -Path "$ResultPath.cancelled" -Data @{ cancelled = (Get-EpochSeconds); reason = 'session close failed' }
        throw
    }
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

Invoke-ReaperHandshake -StateDirectory $stateDirectory -ResolvedWorktree $resolvedWorktree -Receipt $receipt `
    -OwnHost $ownHost -ParentShell $parentShell -Attachment $attachment -ResultPath $resultPath
