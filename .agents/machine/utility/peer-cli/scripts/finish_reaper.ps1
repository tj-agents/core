<#
.SYNOPSIS
Detached worker spawned by `finish.ps1`: wait for the finishing host to exit, then remove its worktree.

.DESCRIPTION
Launched through `Invoke-CimMethod Win32_Process Create` (or the `schtasks` fallback), so it is parented
to the WMI provider host rather than to `finish.ps1`, its caller's job object, or that caller's own
process tree. It writes a `started` stamp to `-Result` immediately so the launcher can prove the spawn
succeeded, then polls `-HostPid` (identity confirmed by `-HostStart`, since a pid is reused the moment it
is free) until it exits or `-HostStart`/`AGENT_FINISH_REAPER_TIMEOUT_SECONDS` (default 600s) elapses.

A live host at timeout still holds its own current directory, so Windows cannot remove it either way;
the worktree is left untouched and the result record carries a `timeout` status. Once the host is
confirmed gone, it runs `git -C <primary> worktree remove -- <target>` (never `--force`) and
`git branch -d|-D` from the primary, chosen the same way `cleanup_proof.py` does: `-d` only when the
branch is still an ancestor of `origin/<default>`. Full success (path absent, unregistered, branch gone)
clears the matching `merge_cleanup_gate.py` obligation, keyed by the identical worktree digest; any error
leaves the obligation in place and is recorded in the result instead.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [int] $HostPid,
    [Parameter(Mandatory)] [double] $HostStart,
    [Parameter(Mandatory)] [string] $Primary,
    [Parameter(Mandatory)] [string] $Worktree,
    [Parameter(Mandatory)] [string] $Branch,
    [Parameter(Mandatory)] [string] $Default,
    [Parameter(Mandatory)] [string] $Result,
    [string] $StateDirectory
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

function ConvertTo-UnixTime {
    param([DateTime] $Value)

    return ([DateTimeOffset]($Value.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0
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
    $timeoutSeconds = Get-EnvDouble -Name 'AGENT_FINISH_REAPER_TIMEOUT_SECONDS' -Default 600.0
    $deadline = [DateTime]::UtcNow.AddSeconds($timeoutSeconds)
    $exited = $false
    while ([DateTime]::UtcNow -lt $deadline) {
        $process = Get-Process -Id $HostPid -ErrorAction SilentlyContinue
        if (-not $process) { $exited = $true; break }
        $startTime = try { $process.StartTime } catch { $null }
        if ($null -eq $startTime) { $exited = $true; break }
        $actual = ConvertTo-UnixTime -Value $startTime
        if ([math]::Abs($actual - $HostStart) -gt 2.0) { $exited = $true; break }
        Start-Sleep -Milliseconds 500
    }

    if (-not $exited) {
        Save-ResultRecord -Path $Result -Data @{
            started  = $startedEpoch
            host_pid = $HostPid
            worktree = $Worktree
            status   = 'timeout'
            error    = "host pid $HostPid did not exit within $timeoutSeconds seconds"
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

    $pathAbsent = -not (Test-Path -LiteralPath $Worktree)
    $porcelain = (Invoke-Git -Cwd $Primary -Arguments @('worktree', 'list', '--porcelain')).Output
    $normalizedWorktree = ($Worktree -replace '\\', '/')
    $unregistered = -not (($porcelain -replace '\\', '/') -like "*$normalizedWorktree*")

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

    Save-ResultRecord -Path $Result -Data @{
        started  = $startedEpoch
        host_pid = $HostPid
        worktree = $Worktree
        status   = 'succeeded'
        finished = (Now-Epoch)
    }

    $obligationPath = Join-Path $resolvedState ('merge-cleanup/obligations/' + (Get-WorktreeDigest -ResolvedWorktree $Worktree) + '.json')
    if (Test-Path -LiteralPath $obligationPath) {
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
