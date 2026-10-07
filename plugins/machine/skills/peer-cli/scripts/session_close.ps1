$ShellProcessNames = @('pwsh', 'powershell', 'cmd', 'bash', 'sh', 'zsh', 'fish', 'nu')

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

function Test-OnlyHostAndConsoleChildren {
    param([int] $ParentPid, [int] $HostPid)

    $consoleStems = @('conhost', 'openconsole')
    $children = @(Get-CimInstance -ClassName Win32_Process -Filter "ParentProcessId = $ParentPid" -ErrorAction SilentlyContinue)
    foreach ($child in $children) {
        if ([int] $child.ProcessId -eq $HostPid) { continue }
        $childStem = [IO.Path]::GetFileNameWithoutExtension($child.Name).ToLowerInvariant()
        if ($consoleStems -notcontains $childStem) { return $false }
    }
    return $true
}

function Get-ParentShellHost {
    param([pscustomobject] $OwnHost)

    $process = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $($OwnHost.Pid)" -ErrorAction SilentlyContinue
    if (-not $process) { return $null }
    $parent = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $($process.ParentProcessId)" -ErrorAction SilentlyContinue
    if (-not $parent) { return $null }
    $stem = [IO.Path]::GetFileNameWithoutExtension($parent.Name).ToLowerInvariant()
    if ($ShellProcessNames -notcontains $stem) { return $null }
    $parentStarted = ConvertTo-UnixTime -Value $parent.CreationDate
    $delta = $OwnHost.Started - $parentStarted
    if ($delta -lt 0 -or $delta -gt 10.0) { return $null }
    if (-not (Test-OnlyHostAndConsoleChildren -ParentPid ([int] $parent.ProcessId) -HostPid $OwnHost.Pid)) { return $null }
    return [pscustomobject]@{
        Pid     = [int] $parent.ProcessId
        Started = $parentStarted
    }
}

function Stop-VerifiedProcess {
    param([pscustomobject] $Target)

    $process = Get-Process -Id $Target.Pid -ErrorAction SilentlyContinue
    if (-not $process) { return }
    $startTime = try { $process.StartTime } catch { $null }
    if ($null -eq $startTime) { return }
    if ([math]::Abs((ConvertTo-UnixTime -Value $startTime) - $Target.Started) -gt 2.0) { return }
    Stop-Process -Id $Target.Pid -Force
}

function Stop-WrapperThenHost {
    param([pscustomobject] $OwnHost, [pscustomobject] $ParentShell)

    if ($ParentShell) { Stop-VerifiedProcess -Target $ParentShell }
    Stop-VerifiedProcess -Target $OwnHost
}

function Test-ProcessVerifiedLive {
    param($ProcessId, $StartedAt)

    if ($null -eq $ProcessId -or $null -eq $StartedAt) { return $false }
    $process = Get-Process -Id ([int] $ProcessId) -ErrorAction SilentlyContinue
    if (-not $process) { return $false }
    $startTime = try { $process.StartTime } catch { $null }
    if ($null -eq $startTime) { return $false }
    return ([math]::Abs((ConvertTo-UnixTime -Value $startTime) - [double] $StartedAt) -le 2.0)
}

function Get-RecordedSessionEntries {
    $directory = Join-Path (Get-StateDirectory) 'cli-sessions'
    if (-not (Test-Path -LiteralPath $directory)) { return @() }
    return @(Get-ChildItem -LiteralPath $directory -Filter '*.json' -File | ForEach-Object {
        try { Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $null }
    } | Where-Object { $_ })
}

function Get-OwnRegistryEntry {
    param([pscustomobject] $OwnHost)

    $matches = @(foreach ($entry in (Get-RecordedSessionEntries)) {
        $entryPid = Get-EntryProperty -Entry $entry -Name 'pid'
        $entryStart = Get-EntryProperty -Entry $entry -Name 'pid_started_at'
        if ($entryPid -eq $OwnHost.Pid -and $null -ne $entryStart -and
            [math]::Abs([double] $entryStart - $OwnHost.Started) -le 2.0) {
            $entry
        }
    })
    if ($matches.Count -eq 0) { return $null }
    $latest = $null
    $latestStarted = 0.0
    $latestCount = 0
    foreach ($entry in $matches) {
        $registered = Get-EntryProperty -Entry $entry -Name 'started_at'
        if ($matches.Count -eq 1 -and $null -eq $registered) { return $entry }
        $started = 0.0
        if (-not [double]::TryParse([Convert]::ToString($registered, [Globalization.CultureInfo]::InvariantCulture), [Globalization.NumberStyles]::Float,
                [Globalization.CultureInfo]::InvariantCulture, [ref] $started) -or
            [double]::IsNaN($started) -or [double]::IsInfinity($started) -or $started -le 0.0) {
            return $null
        }
        if ($started -gt $latestStarted) {
            $latest = $entry
            $latestStarted = $started
            $latestCount = 1
        }
        elseif ($started -eq $latestStarted) { $latestCount++ }
    }
    if ($latestCount -eq 1) { return $latest }
    return $null
}

function Get-TitleAndAttachment {
    param(
        [string] $ResolvedWorktree,
        [string] $StartingLocation,
        [pscustomobject] $OwnHost
    )

    $selfEntry = Get-OwnRegistryEntry -OwnHost $OwnHost
    $selfCwd = if ($selfEntry) { Get-EntryProperty -Entry $selfEntry -Name 'cwd' } else { $null }
    $attached = (Test-UnderOrEqual -Candidate $StartingLocation -Root $ResolvedWorktree) -or
        (Test-UnderOrEqual -Candidate $selfCwd -Root $ResolvedWorktree)
    return [pscustomobject]@{
        Attached = $attached
        Title    = if ($selfEntry) { Get-EntryProperty -Entry $selfEntry -Name 'title' } else { $null }
    }
}

function Test-OtherLiveSessionClaimsWorktree {
    param([string] $ResolvedWorktree, [pscustomobject] $OwnHost)

    foreach ($entry in (Get-RecordedSessionEntries)) {
        $entryPid = Get-EntryProperty -Entry $entry -Name 'pid'
        $entryStart = Get-EntryProperty -Entry $entry -Name 'pid_started_at'
        if ($entryPid -eq $OwnHost.Pid -and $null -ne $entryStart -and
            [math]::Abs([double] $entryStart - $OwnHost.Started) -le 2.0) { continue }
        $entryCwd = Get-EntryProperty -Entry $entry -Name 'cwd'
        if (-not (Test-UnderOrEqual -Candidate $entryCwd -Root $ResolvedWorktree)) { continue }
        if (Test-ProcessVerifiedLive -ProcessId $entryPid -StartedAt $entryStart) { return $true }
    }
    return $false
}

function Test-SingleRegistryEntryWithTitle {
    param([string] $Title)

    $count = 0
    foreach ($entry in (Get-RecordedSessionEntries)) {
        if ((Get-EntryProperty -Entry $entry -Name 'title') -eq $Title) { $count++ }
    }
    return $count -eq 1
}

function ConvertFrom-TabListingJson {
    param([string] $Text)

    if (-not $Text -or -not $Text.Trim()) { return @() }
    try { return @(ConvertFrom-Json -InputObject $Text | ForEach-Object { $_ }) } catch { return @() }
}

function Test-SingleLiveTabInListing {
    param([object[]] $Tabs, [string] $Title)

    $found = @($Tabs | Where-Object { $_.title -eq $Title })
    return $found.Count -eq 1
}

function Get-LiveTerminalTabs {
    $output = & (Join-Path $PSScriptRoot 'close-tab.ps1') -Json 2>$null
    $text = (@($output) | ForEach-Object { [string] $_ }) -join "`n"
    return (ConvertFrom-TabListingJson -Text $text)
}

function Test-SingleLiveTabWithTitle {
    param([string] $Title)

    return (Test-SingleLiveTabInListing -Tabs (Get-LiveTerminalTabs) -Title $Title)
}

function Invoke-SessionClose {
    param(
        [string] $CloseMode,
        [pscustomobject] $Attachment,
        [pscustomobject] $OwnHost,
        [pscustomobject] $ParentShell
    )

    if ($CloseMode -eq 'process') {
        Stop-WrapperThenHost -OwnHost $OwnHost -ParentShell $ParentShell
        Write-Output "finish: closed host pid $($OwnHost.Pid) directly (AGENT_FINISH_CLOSE_MODE=process)."
        return
    }
    if ($Attachment.Title -and
        (Test-SingleRegistryEntryWithTitle -Title $Attachment.Title) -and
        (Test-SingleLiveTabWithTitle -Title $Attachment.Title)) {
        & (Join-Path $PSScriptRoot 'close-tab.ps1') $Attachment.Title -Force
        return
    }
    Stop-WrapperThenHost -OwnHost $OwnHost -ParentShell $ParentShell
    Write-Output "finish: closed host pid $($OwnHost.Pid) directly (no uniquely identified tab to close)."
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
