<#
.SYNOPSIS
Detached worker spawned by `finish.ps1`: wait for the finishing host to exit, then remove its worktree.

.DESCRIPTION
Launched through `Invoke-CimMethod Win32_Process Create` (or the `schtasks` fallback), so it is parented
to the WMI provider host rather than to `finish.ps1`, its caller's job object, or that caller's own
process tree. It writes a `started` stamp to `-Result` immediately so the launcher can prove the spawn
succeeded, then polls `-HostPid` (identity confirmed by `-HostStart`, since a pid is reused the moment it
is free) and, when `-ParentPid` is given, that process too, until every one of them exits or
`AGENT_FINISH_REAPER_TIMEOUT_SECONDS` (default 600s) elapses.

A live host (or parent shell) at timeout still holds its own current directory, so Windows cannot remove
it either way; the worktree is left untouched and the result record carries a `timeout` status. Once
every watched process is confirmed gone, it runs `git -C <primary> worktree remove -- <target>` (never
`--force`). Before deleting the branch it requires `refs/heads/<branch>` in the primary to still equal
`-Head`, the proven tip `cleanup_proof.py` recorded: if a later commit moved the branch, the branch is
left in place and the result records a `branch-preserved` status and why, while the worktree removal and
obligation clearing still proceed. Otherwise it deletes the branch, choosing `-d` only when it is still
an ancestor of `origin/<default>`, `-D` otherwise, the same policy `cleanup_proof.py` uses. Full success
(path absent, unregistered) clears the matching `merge_cleanup_gate.py` obligation, located the same way
`finish.ps1` locates its receipt: scanning `merge-cleanup/obligations/*.json` for a recorded `worktree`
field that normalises to the same path; any error leaves the obligation in place and is recorded in the
result instead.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [int] $HostPid,
    [Parameter(Mandatory)] [double] $HostStart,
    [Parameter(Mandatory)] [string] $Head,
    [Parameter(Mandatory)] [string] $Primary,
    [Parameter(Mandatory)] [string] $Worktree,
    [Parameter(Mandatory)] [string] $Branch,
    [Parameter(Mandatory)] [string] $Default,
    [Parameter(Mandatory)] [string] $Result,
    [string] $StateDirectory,
    [int] $ParentPid = -1,
    [double] $ParentStart = -1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-StateDirectory {
    param([string] $Provided)

    if ($Provided) { return $Provided }
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

function Read-JsonFile {
    param([string] $Path)

    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

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

function Find-ObligationPaths {
    param([string] $StateDirectory, [string] $ResolvedWorktree)

    $directory = Join-Path $StateDirectory 'merge-cleanup/obligations'
    if (-not (Test-Path -LiteralPath $directory)) { return @() }
    $targetForms = @(Get-WorktreeComparisonForms -Path $ResolvedWorktree)
    $matches = New-Object System.Collections.Generic.List[string]
    foreach ($file in Get-ChildItem -LiteralPath $directory -Filter '*.json' -File) {
        $data = Read-JsonFile -Path $file.FullName
        if (-not $data) { continue }
        $recorded = Get-EntryProperty -Entry $data -Name 'worktree'
        if (-not $recorded) { continue }
        $recordedForms = @(Get-WorktreeComparisonForms -Path $recorded)
        foreach ($form in $recordedForms) {
            if ($targetForms -contains $form) { $matches.Add($file.FullName); break }
        }
    }
    return $matches
}

function Get-RegisteredWorktreePaths {
    param([string] $PorcelainOutput)

    $paths = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($PorcelainOutput -split "`n")) {
        $trimmed = $line.TrimEnd("`r")
        if ($trimmed.StartsWith('worktree ')) {
            $paths.Add($trimmed.Substring('worktree '.Length))
        }
    }
    return $paths
}

function Test-WorktreeStillRegistered {
    param([string] $PorcelainOutput, [string] $ResolvedWorktree)

    $targetForms = @(Get-WorktreeComparisonForms -Path $ResolvedWorktree)
    foreach ($registered in (Get-RegisteredWorktreePaths -PorcelainOutput $PorcelainOutput)) {
        $registeredForms = @(Get-WorktreeComparisonForms -Path $registered)
        foreach ($form in $registeredForms) {
            if ($targetForms -contains $form) { return $true }
        }
    }
    return $false
}

function ConvertTo-UnixTime {
    param([DateTime] $Value)

    return ([DateTimeOffset]($Value.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0
}

function Test-ProcessExited {
    param([int] $ProcessId, [double] $StartedAt)

    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $process) { return $true }
    $startTime = try { $process.StartTime } catch { $null }
    if ($null -eq $startTime) { return $true }
    return ([math]::Abs((ConvertTo-UnixTime -Value $startTime) - $StartedAt) -gt 2.0)
}

function Get-EnvDouble {
    param([string] $Name, [double] $Default)

    $value = [Environment]::GetEnvironmentVariable($Name)
    if (-not $value) { return $Default }
    $parsed = 0.0
    if ([double]::TryParse($value, [ref] $parsed)) { return $parsed }
    return $Default
}

function Save-ResultRecord {
    param([string] $Path, [hashtable] $Data)

    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $json = $Data | ConvertTo-Json -Depth 6
    $temp = Join-Path $directory ('.' + (Split-Path -Leaf $Path) + '.' + $PID + '.tmp')
    [IO.File]::WriteAllText($temp, $json, (New-Object Text.UTF8Encoding $false))
    if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    Move-Item -LiteralPath $temp -Destination $Path
}

function Invoke-Git {
    param([string] $Cwd, [string[]] $Arguments)

    $allArgs = @('-C', $Cwd) + $Arguments
    $output = & git @allArgs 2>&1
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = ($output -join "`n") }
}

function Now-Epoch {
    return [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0
}

$resolvedState = Resolve-StateDirectory -Provided $StateDirectory
$startedEpoch = Now-Epoch

Save-ResultRecord -Path $Result -Data @{
    started  = $startedEpoch
    host_pid = $HostPid
    worktree = $Worktree
}

try {
    $waitTargets = New-Object System.Collections.Generic.List[pscustomobject]
    $waitTargets.Add([pscustomobject]@{ Pid = $HostPid; Started = $HostStart })
    if ($ParentPid -gt 0) { $waitTargets.Add([pscustomobject]@{ Pid = $ParentPid; Started = $ParentStart }) }

    $timeoutSeconds = Get-EnvDouble -Name 'AGENT_FINISH_REAPER_TIMEOUT_SECONDS' -Default 600.0
    $deadline = [DateTime]::UtcNow.AddSeconds($timeoutSeconds)
    $exited = $false
    while ([DateTime]::UtcNow -lt $deadline) {
        $allExited = $true
        foreach ($target in $waitTargets) {
            if (-not (Test-ProcessExited -ProcessId $target.Pid -StartedAt $target.Started)) { $allExited = $false; break }
        }
        if ($allExited) { $exited = $true; break }
        Start-Sleep -Milliseconds 500
    }

    if (-not $exited) {
        Save-ResultRecord -Path $Result -Data @{
            started  = $startedEpoch
            host_pid = $HostPid
            worktree = $Worktree
            status   = 'timeout'
            error    = "host pid $HostPid (or its parent shell) did not exit within $timeoutSeconds seconds"
            finished = (Now-Epoch)
        }
        return
    }

    $removeResult = Invoke-Git -Cwd $Primary -Arguments @('worktree', 'remove', '--', $Worktree)
    if ($removeResult.ExitCode -ne 0) {
        Save-ResultRecord -Path $Result -Data @{
            started  = $startedEpoch
            host_pid = $HostPid
            worktree = $Worktree
            status   = 'failed'
            error    = "git worktree remove failed: $($removeResult.Output)"
            finished = (Now-Epoch)
        }
        return
    }

    $branchPreserved = $false
    $branchPreservedReason = $null
    $branchRef = Invoke-Git -Cwd $Primary -Arguments @('rev-parse', '--verify', '--quiet', "refs/heads/$Branch")
    if ($branchRef.ExitCode -ne 0) {
        $branchPreserved = $true
        $branchPreservedReason = "refs/heads/$Branch no longer exists in $Primary"
    }
    elseif ($branchRef.Output.Trim() -ne $Head) {
        $branchPreserved = $true
        $branchPreservedReason = "refs/heads/$Branch is now $($branchRef.Output.Trim()), not the receipt head $Head"
    }

    if (-not $branchPreserved) {
        $ancestorCheck = Invoke-Git -Cwd $Primary -Arguments @('merge-base', '--is-ancestor', "refs/heads/$Branch", "origin/$Default")
        $deleteFlag = if ($ancestorCheck.ExitCode -eq 0) { '-d' } else { '-D' }
        $branchResult = Invoke-Git -Cwd $Primary -Arguments @('branch', $deleteFlag, $Branch)
        if ($branchResult.ExitCode -ne 0) {
            Save-ResultRecord -Path $Result -Data @{
                started  = $startedEpoch
                host_pid = $HostPid
                worktree = $Worktree
                status   = 'failed'
                error    = "git branch $deleteFlag $Branch failed: $($branchResult.Output)"
                finished = (Now-Epoch)
            }
            return
        }
    }

    $pathAbsent = -not (Test-Path -LiteralPath $Worktree)
    $porcelain = (Invoke-Git -Cwd $Primary -Arguments @('worktree', 'list', '--porcelain')).Output
    $unregistered = -not (Test-WorktreeStillRegistered -PorcelainOutput $porcelain -ResolvedWorktree $Worktree)

    if (-not ($pathAbsent -and $unregistered)) {
        Save-ResultRecord -Path $Result -Data @{
            started  = $startedEpoch
            host_pid = $HostPid
            worktree = $Worktree
            status   = 'failed'
            error    = 'worktree path or its registration is still present after cleanup'
            finished = (Now-Epoch)
        }
        return
    }

    if ($branchPreserved) {
        Save-ResultRecord -Path $Result -Data @{
            started  = $startedEpoch
            host_pid = $HostPid
            worktree = $Worktree
            status   = 'branch-preserved'
            reason   = $branchPreservedReason
            finished = (Now-Epoch)
        }
    }
    else {
        Save-ResultRecord -Path $Result -Data @{
            started  = $startedEpoch
            host_pid = $HostPid
            worktree = $Worktree
            status   = 'succeeded'
            finished = (Now-Epoch)
        }
    }

    foreach ($obligationPath in @(Find-ObligationPaths -StateDirectory $resolvedState -ResolvedWorktree $Worktree)) {
        try { Remove-Item -LiteralPath $obligationPath -Force } catch { }
    }
}
catch {
    Save-ResultRecord -Path $Result -Data @{
        started  = $startedEpoch
        host_pid = $HostPid
        worktree = $Worktree
        status   = 'failed'
        error    = $_.Exception.Message
        finished = (Now-Epoch)
    }
}
