<#
.SYNOPSIS
Detached worker spawned by `finish.ps1`: wait for the finishing host to exit, then remove its worktree.

.DESCRIPTION
Launched through `Invoke-CimMethod Win32_Process Create` (or the `schtasks` fallback), so it is parented
to the WMI provider host rather than to `finish.ps1`, its caller's job object, or that caller's own
process tree. In cleanup mode (not `-CloseOnly`) it writes its `started` record to `-Result` by exclusive
create, carrying its own `reaper_pid`/`reaper_started_at`; a failed exclusive create means a sibling
invocation already owns this result path, so it exits at once touching nothing. It then waits up to
`-AcceptTimeoutSeconds` for the launcher's `.accepted` signal naming this exact pid and start time,
checking `.cancelled` first on every poll so a cancellation always wins a race; an accepted invocation
writes `.armed` and proceeds, a foreign acceptance exits without writing the result file, and a deadline
or cancellation writes a `not-accepted`/`cancelled` terminal record and exits. Only once armed does it
poll `-HostPid` (identity confirmed by `-HostStart`, since a pid is reused the moment it is free) and,
when `-ParentPid` is given, that process too, until every one of them exits or
`AGENT_FINISH_REAPER_TIMEOUT_SECONDS` (default 600s) elapses. `-CloseOnly` is unaffected: it keeps its
started-only confirmation and skips the accept gate entirely.

A live host (or parent shell) at timeout still holds its own current directory, so Windows cannot remove
it either way; the worktree is left untouched and the result record carries a `timeout` status. Once
every watched process is confirmed gone, it re-checks `.cancelled` once more immediately before touching
the worktree - a cancellation landing during the host wait still wins - then runs
`git -C <primary> worktree remove -- <target>` (never `--force`). Before deleting the branch it requires `refs/heads/<branch>` in the primary to still equal
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
    [string] $Head,
    [string] $Primary,
    [Parameter(Mandatory)] [string] $Worktree,
    [string] $Branch,
    [string] $Default,
    [Parameter(Mandatory)] [string] $Result,
    [string] $StateDirectory,
    [int] $ParentPid = -1,
    [double] $ParentStart = -1,
    [switch] $CloseOnly,
    [string] $SessionId,
    [double] $AcceptTimeoutSeconds = 60
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
    param([string] $StateDirectory, [string] $ResolvedWorktree, [string] $SessionId)

    $directory = Join-Path $StateDirectory 'merge-cleanup/obligations'
    if (-not (Test-Path -LiteralPath $directory)) { return @() }
    $targetForms = @(Get-WorktreeComparisonForms -Path $ResolvedWorktree)
    $matches = New-Object System.Collections.Generic.List[string]
    foreach ($file in Get-ChildItem -LiteralPath $directory -Filter '*.json' -File) {
        $data = Read-JsonFile -Path $file.FullName
        if (-not $data) { continue }
        if ($SessionId) {
            if ((Get-EntryProperty -Entry $data -Name 'session_id') -eq $SessionId) { $matches.Add($file.FullName) }
            continue
        }
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
    if ($null -eq $startTime) { return $false }
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

function ConvertTo-FiniteDouble {
    param($Value)

    if ($null -eq $Value) { return $null }
    $text = [Convert]::ToString($Value, [Globalization.CultureInfo]::InvariantCulture)
    $parsed = 0.0
    if (-not [double]::TryParse($text, [Globalization.NumberStyles]::Float,
            [Globalization.CultureInfo]::InvariantCulture, [ref] $parsed)) {
        return $null
    }
    if ([double]::IsNaN($parsed) -or [double]::IsInfinity($parsed)) { return $null }
    return $parsed
}

function ConvertTo-PositiveInt {
    param($Value)

    $numeric = ConvertTo-FiniteDouble -Value $Value
    if ($null -eq $numeric -or $numeric -le 0 -or $numeric -ne [math]::Floor($numeric) -or $numeric -gt [int]::MaxValue) {
        return $null
    }
    return [int] $numeric
}

function Save-ResultRecord {
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

function Save-RecordExclusive {
    param([string] $Path, [hashtable] $Data)

    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $json = $Data | ConvertTo-Json -Depth 6
    $temp = Join-Path $directory ('.' + (Split-Path -Leaf $Path) + '.' + $PID + '.tmp')
    [IO.File]::WriteAllText($temp, $json, (New-Object Text.UTF8Encoding $false))
    try {
        [IO.File]::Move($temp, $Path)
        return $true
    }
    catch {
        try { [IO.File]::Delete($temp) } catch { }
        return $false
    }
}

function Wait-ForAcceptance {
    param(
        [string] $ResultPath,
        [int] $OwnPid,
        [double] $OwnStartedAt,
        [double] $TimeoutSeconds
    )

    $cancelledPath = "$ResultPath.cancelled"
    $acceptedPath = "$ResultPath.accepted"
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ($true) {
        if (Test-Path -LiteralPath $cancelledPath) { return 'cancelled' }
        $accepted = Read-JsonFile -Path $acceptedPath
        if ($accepted) {
            $acceptedPid = ConvertTo-PositiveInt -Value (Get-EntryProperty -Entry $accepted -Name 'reaper_pid')
            if ($null -ne $acceptedPid -and $acceptedPid -ne $OwnPid) { return 'foreign' }
            if ($null -ne $acceptedPid -and $acceptedPid -eq $OwnPid) {
                $acceptedStartedAt = ConvertTo-FiniteDouble -Value (Get-EntryProperty -Entry $accepted -Name 'reaper_started_at')
                if ($null -ne $acceptedStartedAt -and [math]::Abs($acceptedStartedAt - $OwnStartedAt) -le 2.0) {
                    Save-ResultRecord -Path "$ResultPath.armed" -Data @{ armed = (Now-Epoch); reaper_pid = $PID }
                    return 'accepted'
                }
            }
        }
        if ([DateTime]::UtcNow -ge $deadline) { return 'timeout' }
        Start-Sleep -Milliseconds 100
    }
}

function Save-CloseStartupRecord {
    param([string] $Path, [double] $Started, [int] $HostPid, [string] $Worktree)

    $assemblyName = if ($PSVersionTable.PSEdition -eq 'Desktop') {
        'System.Runtime.Serialization, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089'
    } else {
        'System.Runtime.Serialization.Json'
    }
    $null = [Reflection.Assembly]::Load($assemblyName)
    $settings = [Runtime.Serialization.Json.DataContractJsonSerializerSettings]::new()
    $settings.UseSimpleDictionaryFormat = $true
    $receipt = [Collections.Generic.Dictionary[string,object]]::new()
    $receipt.Add('started', $Started)
    $receipt.Add('host_pid', $HostPid)
    $receipt.Add('worktree', $Worktree)
    $serializer = [Runtime.Serialization.Json.DataContractJsonSerializer]::new($receipt.GetType(), $settings)
    $stream = [IO.MemoryStream]::new()
    try {
        $serializer.WriteObject($stream, $receipt)
        $json = [Text.Encoding]::UTF8.GetString($stream.ToArray())
    }
    finally {
        $stream.Dispose()
    }
    $directory = [IO.Path]::GetDirectoryName($Path)
    $null = [IO.Directory]::CreateDirectory($directory)
    $temp = [IO.Path]::Combine($directory, '.' + [IO.Path]::GetFileName($Path) + '.' + $PID + '.tmp')
    [IO.File]::WriteAllText($temp, $json, [Text.UTF8Encoding]::new($false))
    if ([IO.File]::Exists($Path)) { [IO.File]::Delete($Path) }
    [IO.File]::Move($temp, $Path)
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
$reaperStartedAt = ConvertTo-UnixTime -Value (Get-Process -Id $PID).StartTime
if ($CloseOnly) {
    if (-not $SessionId) { throw 'close observer requires a session identity.' }
}
elseif (-not $Head -or -not $Primary -or -not $Branch -or -not $Default) {
    throw 'cleanup reaper requires the complete removal receipt.'
}

if ($CloseOnly) {
    Save-CloseStartupRecord -Path $Result -Started $startedEpoch -HostPid $HostPid -Worktree $Worktree
}
else {
    $ownedResult = Save-RecordExclusive -Path $Result -Data @{
        started           = $startedEpoch
        host_pid          = $HostPid
        worktree          = $Worktree
        reaper_pid        = $PID
        reaper_started_at = $reaperStartedAt
    }
    if (-not $ownedResult) { return }
}

try {
    if (-not $CloseOnly) {
        $acceptance = Wait-ForAcceptance -ResultPath $Result -OwnPid $PID -OwnStartedAt $reaperStartedAt -TimeoutSeconds $AcceptTimeoutSeconds
        if ($acceptance -eq 'foreign') { return }
        if ($acceptance -eq 'cancelled') {
            Save-ResultRecord -Path $Result -Data @{
                started           = $startedEpoch
                host_pid          = $HostPid
                worktree          = $Worktree
                reaper_pid        = $PID
                reaper_started_at = $reaperStartedAt
                status            = 'cancelled'
                finished          = (Now-Epoch)
            }
            return
        }
        if ($acceptance -eq 'timeout') {
            Save-ResultRecord -Path $Result -Data @{
                started           = $startedEpoch
                host_pid          = $HostPid
                worktree          = $Worktree
                reaper_pid        = $PID
                reaper_started_at = $reaperStartedAt
                status            = 'not-accepted'
                finished          = (Now-Epoch)
            }
            return
        }
    }

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
        if (Test-Path -LiteralPath "$Result.cancelled") {
            Save-ResultRecord -Path $Result -Data @{
                started           = $startedEpoch
                host_pid          = $HostPid
                worktree          = $Worktree
                reaper_pid        = $PID
                reaper_started_at = $reaperStartedAt
                status            = 'cancelled'
                finished          = (Now-Epoch)
            }
            return
        }
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

    if ($CloseOnly) {
        Save-ResultRecord -Path $Result -Data @{
            started = $startedEpoch
            host_pid = $HostPid
            host_started_at = $HostStart
            session_id = $SessionId
            worktree = $Worktree
            checkout_retained = $true
            session_exited = $true
            status = 'session-closed'
            finished = (Now-Epoch)
        }
        foreach ($path in @(Find-ObligationPaths -StateDirectory $resolvedState -SessionId $SessionId)) {
            Remove-Item -LiteralPath $path -Force
        }
        return
    }

    if (Test-Path -LiteralPath "$Result.cancelled") {
        Save-ResultRecord -Path $Result -Data @{
            started           = $startedEpoch
            host_pid          = $HostPid
            worktree          = $Worktree
            reaper_pid        = $PID
            reaper_started_at = $reaperStartedAt
            status            = 'cancelled'
            finished          = (Now-Epoch)
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
