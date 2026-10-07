$ErrorActionPreference = 'Stop'

$repository = Split-Path -Parent $PSScriptRoot
$peerCli = Join-Path $repository '.agents\machine\utility\peer-cli\scripts\peer-cli.ps1'
$scratch = Join-Path ([IO.Path]::GetTempPath()) "peer-cli-tests-$([guid]::NewGuid().ToString('N'))"
$originalStateDirectory = $env:AGENT_STATE_DIRECTORY
function Assert-Contains {
    param([string] $Actual, [string] $Expected, [string] $Message)

    if (-not $Actual.Contains($Expected)) { throw "$Message Output: $Actual" }
}

function Assert-NotContains {
    param([string] $Actual, [string] $Unexpected, [string] $Message)

    if ($Actual.Contains($Unexpected)) { throw "$Message Output: $Actual" }
}

function Write-RecordedSession {
    param([string] $Directory, [string] $SessionId, [string] $Cwd)

    [pscustomobject]@{
        title = $SessionId
        session_id = $SessionId
        cwd = $Cwd
        pid = $PID
        started_at = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Directory "$SessionId.json")
}

function Assert-True {
    param([object] $Actual, [string] $Message)

    if ($Actual -ne $true) { throw "$Message Actual: $Actual" }
}

function Assert-False {
    param([object] $Actual, [string] $Message)

    if ($Actual -ne $false) { throw "$Message Actual: $Actual" }
}

function Assert-Null {
    param([object] $Actual, [string] $Message)

    if ($null -ne $Actual) { throw "$Message Actual: $Actual" }
}

function Assert-Throws {
    param([scriptblock] $Block, [string] $Message)

    $threw = $false
    try { & $Block | Out-Null } catch { $threw = $true }
    if (-not $threw) { throw $Message }
}

function ConvertTo-EpochSeconds {
    param([DateTime] $Value)

    return ([DateTimeOffset]($Value.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0
}

function Wait-ProcessGone {
    param([int] $ProcessId, [int] $TimeoutMilliseconds = 5000)

    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMilliseconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (-not (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) { return $true }
        Start-Sleep -Milliseconds 100
    }
    return (-not (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue))
}

function Write-RawEntry {
    param([string] $Directory, [string] $SessionId, [hashtable] $Fields)

    $Fields | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Directory "$SessionId.json") -Encoding UTF8
}

function Invoke-FakeHostRegistration {
    param(
        [string] $HostExeName,
        [switch] $ViaShell,
        [string] $StateDirectory,
        [string] $SessionId,
        [string] $WorkDirectory
    )

    $fakeHost = Join-Path $WorkDirectory $HostExeName
    Copy-Item -LiteralPath $env:ComSpec -Destination $fakeHost -Force

    $registerScript = Join-Path $repository '.agents\machine\utility\peer-cli\scripts\register_session.py'
    $payloadFile = Join-Path $WorkDirectory "$SessionId.payload.json"
    $stdoutFile = Join-Path $WorkDirectory "$SessionId.stdout.log"
    $stderrFile = Join-Path $WorkDirectory "$SessionId.stderr.log"
    # Windows PowerShell 5.1's Set-Content -Encoding UTF8 prepends a BOM, which register_session.py's
    # stdin read does not strip; write the payload with .NET directly so both hosts send plain UTF-8.
    $payloadJson = @{ session_id = $SessionId; cwd = 'C:/fake' } | ConvertTo-Json
    [IO.File]::WriteAllText($payloadFile, $payloadJson, (New-Object Text.UTF8Encoding $false))

    $innerCommand = "python -B `"$registerScript`""
    $arguments = if ($ViaShell) { @('/c', "cmd /c $innerCommand") } else { @('/c', $innerCommand) }

    $previousState = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $StateDirectory
    $process = $null
    try {
        $process = Start-Process -FilePath $fakeHost -ArgumentList $arguments `
            -RedirectStandardInput $payloadFile -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile `
            -PassThru -WindowStyle Hidden
        $startTimeEpoch = ConvertTo-EpochSeconds -Value $process.StartTime
        if (-not $process.WaitForExit(20000)) {
            & taskkill.exe /PID $process.Id /T /F | Out-Null
            throw "fake host '$HostExeName' did not exit in time."
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousState
    }

    $entryPath = Join-Path $StateDirectory "cli-sessions\$SessionId.json"
    if (-not (Test-Path -LiteralPath $entryPath)) {
        $stdoutText = if (Test-Path -LiteralPath $stdoutFile) { Get-Content -LiteralPath $stdoutFile -Raw } else { '' }
        $stderrText = if (Test-Path -LiteralPath $stderrFile) { Get-Content -LiteralPath $stderrFile -Raw } else { '' }
        throw "No registry entry written for session '$SessionId'. stdout: $stdoutText stderr: $stderrText"
    }

    [pscustomobject]@{
        ProcessId      = $process.Id
        StartTimeEpoch = $startTimeEpoch
        Entry          = (Get-Content -LiteralPath $entryPath -Raw | ConvertFrom-Json)
    }
}

function Invoke-PeerCliList {
    param([string] $WorkingDirectory, [string] $Under, [switch] $IncludeUnrecorded)

    Push-Location -LiteralPath $WorkingDirectory
    try {
        if ($IncludeUnrecorded) {
            if (-not $PSBoundParameters.ContainsKey('Under')) {
                return (& $peerCli list -IncludeUnrecorded 2>&1 | Out-String)
            }
            return (& $peerCli list -IncludeUnrecorded -Under $Under 2>&1 | Out-String)
        }
        if (-not $PSBoundParameters.ContainsKey('Under')) {
            return (& $peerCli list 2>&1 | Out-String)
        }
        return (& $peerCli list -Under $Under 2>&1 | Out-String)
    }
    finally {
        Pop-Location
    }
}

try {
    $stateDirectory = Join-Path $scratch 'state\cli-sessions'
    $repositoryRoot = Join-Path $scratch 'org\repo'
    $recordedDirectory = Join-Path $repositoryRoot 'child'
    $siblingDirectory = Join-Path $scratch 'org\sibling\child'
    $nearMissDirectory = Join-Path $scratch 'org\repo-other\child'
    $outsideDirectory = Join-Path $scratch 'outside'
    New-Item -ItemType Directory -Path $stateDirectory, $recordedDirectory, $siblingDirectory, $nearMissDirectory, $outsideDirectory, (Join-Path $repositoryRoot '.git') -Force | Out-Null
    $env:AGENT_STATE_DIRECTORY = Split-Path -Parent $stateDirectory

    Write-RecordedSession -Directory $stateDirectory -SessionId 'relative-scope' -Cwd $recordedDirectory
    $relativeOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under '.'
    Assert-Contains -Actual $relativeOutput -Expected 'relative-scope' -Message 'Relative -Under did not include the recorded session.'

    Write-RecordedSession -Directory $stateDirectory -SessionId 'parent-relative-scope' -Cwd $siblingDirectory
    $parentRelativeOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under '..'
    Assert-Contains -Actual $parentRelativeOutput -Expected 'parent-relative-scope' -Message 'Parent-relative -Under did not include the sibling session.'

    $forwardSlashDirectory = $recordedDirectory -replace '\\', '/'
    Write-RecordedSession -Directory $stateDirectory -SessionId 'forward-slash-scope' -Cwd $forwardSlashDirectory
    $forwardSlashRoot = $repositoryRoot -replace '\\', '/'
    $slashOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under $forwardSlashRoot
    Assert-Contains -Actual $slashOutput -Expected 'forward-slash-scope' -Message 'Forward-slash paths did not match the scope.'

    Write-RecordedSession -Directory $stateDirectory -SessionId 'near-prefix' -Cwd $nearMissDirectory
    $boundaryOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under $repositoryRoot
    Assert-NotContains -Actual $boundaryOutput -Unexpected 'near-prefix' -Message 'A sibling path sharing the repository prefix matched the scope.'

    $missingScope = Join-Path $scratch 'missing-scope'
    $missingScopeOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under $missingScope
    Assert-Contains -Actual $missingScopeOutput -Expected 'No CLI sessions in scope.' -Message 'A missing explicit scope did not produce an empty result.'

    $defaultOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot
    Assert-Contains -Actual $defaultOutput -Expected 'parent-relative-scope' -Message 'The default organization scope did not include the sibling session.'

    $emptyState = Join-Path $scratch 'empty-state'
    $env:AGENT_STATE_DIRECTORY = $emptyState
    . $peerCli list -All | Out-Null
    function Get-Item {
        param([string] $LiteralPath)
        [pscustomobject]@{ Parent = $null }
    }
    if ($null -ne (Get-OrganizationRoot -RepoRoot 'drive-root')) {
        throw 'A repository at a drive root must not have an organization root.'
    }
    Remove-Item function:Get-Item
    function Get-OrganizationRoot {
        param([string] $RepoRoot)
        return $null
    }
    $driveRoot = [IO.Path]::GetPathRoot($repositoryRoot)
    $driveRootScope = Get-ListScope -Sessions @(
        [pscustomobject]@{ SessionId = 'drive-root'; Cwd = $driveRoot; Recorded = $true },
        [pscustomobject]@{ SessionId = 'drive-root-child'; Cwd = (Join-Path $driveRoot 'repository-child'); Recorded = $true },
        [pscustomobject]@{ SessionId = 'outside-drive-root'; Cwd = '\\outside-server\share'; Recorded = $true }
    ) -RepoRoot $driveRoot
    $driveRootSessions = ($driveRootScope.Sessions | ForEach-Object { $_.SessionId }) -join ','
    if ($driveRootSessions -ne 'drive-root,drive-root-child') {
        throw "Drive-root fallback returned the wrong sessions: $driveRootSessions"
    }

    $env:AGENT_STATE_DIRECTORY = Split-Path -Parent $stateDirectory
    $fakeClaude = Join-Path $scratch 'claude.exe'
    Copy-Item -LiteralPath $env:ComSpec -Destination $fakeClaude
    $fakeProcess = Start-Process -FilePath $fakeClaude -ArgumentList '/c', 'ping -n 31 127.0.0.1 > nul' -PassThru -WindowStyle Hidden
    try {
        $unrecordedUnderOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -IncludeUnrecorded -Under $outsideDirectory
        Assert-Contains -Actual $unrecordedUnderOutput -Expected ([string]$fakeProcess.Id) -Message 'Unrecorded sessions were hidden by the explicit scope filter.'
        $unrecordedDefaultOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -IncludeUnrecorded
        Assert-Contains -Actual $unrecordedDefaultOutput -Expected ([string]$fakeProcess.Id) -Message 'Unrecorded sessions were hidden by the default scope filter.'
    }
    finally {
        if (Get-Process -Id $fakeProcess.Id -ErrorAction SilentlyContinue) {
            & taskkill.exe /PID $fakeProcess.Id /T /F 2>$null | Out-Null
        }
        $fakeProcess.WaitForExit()
        $fakeProcess.Dispose()
    }

    $registryDirectory = Join-Path $scratch 'registry-truth'
    $registryState = Join-Path $registryDirectory 'state'
    $registryWork = Join-Path $registryDirectory 'work'
    New-Item -ItemType Directory -Path $registryState, $registryWork -Force | Out-Null

    $codexResult = Invoke-FakeHostRegistration -HostExeName 'codex.exe' -ViaShell `
        -StateDirectory $registryState -SessionId 'fake-codex-session' -WorkDirectory $registryWork
    Assert-True -Actual ($codexResult.Entry.pid -eq $codexResult.ProcessId) `
        -Message 'The entry recorded via a shell-hop Codex host did not carry the fake codex.exe pid.'
    Assert-True -Actual ($codexResult.Entry.host -eq 'codex') `
        -Message 'The entry recorded via a shell-hop Codex host did not record host=codex.'
    Assert-True -Actual ([math]::Abs($codexResult.Entry.pid_started_at - $codexResult.StartTimeEpoch) -le 2.0) `
        -Message 'pid_started_at did not match the fake codex.exe StartTime within 2 seconds.'

    $claudeResult = Invoke-FakeHostRegistration -HostExeName 'claude.exe' `
        -StateDirectory $registryState -SessionId 'fake-claude-session' -WorkDirectory $registryWork
    Assert-True -Actual ($claudeResult.Entry.pid -eq $claudeResult.ProcessId) `
        -Message 'The entry recorded via a direct Claude host did not carry the fake claude.exe pid.'
    Assert-True -Actual ($claudeResult.Entry.host -eq 'claude') `
        -Message 'The entry recorded via a direct Claude host did not record host=claude.'
    Assert-True -Actual ([math]::Abs($claudeResult.Entry.pid_started_at - $claudeResult.StartTimeEpoch) -le 2.0) `
        -Message 'pid_started_at did not match the fake claude.exe StartTime within 2 seconds.'

    $livenessDirectory = Join-Path $registryWork 'liveness.exe'
    Copy-Item -LiteralPath $env:ComSpec -Destination $livenessDirectory -Force
    $longRunner = Start-Process -FilePath $livenessDirectory -ArgumentList '/c', 'ping -n 31 127.0.0.1 > nul' -PassThru -WindowStyle Hidden
    $longRunnerStart = ConvertTo-EpochSeconds -Value $longRunner.StartTime
    try {
        $deadRunner = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
        $deadRunnerStart = ConvertTo-EpochSeconds -Value $deadRunner.StartTime
        $deadRunner.WaitForExit(5000) | Out-Null
        $deadPid = $deadRunner.Id

        $sessionsDirectory = Join-Path $registryState 'cli-sessions'

        Write-RawEntry -Directory $sessionsDirectory -SessionId 'alive-new-field' -Fields @{
            title = 'alive-new-field'; session_id = 'alive-new-field'; cwd = 'C:/fake'
            pid = $longRunner.Id; pid_started_at = $longRunnerStart; started_at = $longRunnerStart
        }
        Write-RawEntry -Directory $sessionsDirectory -SessionId 'mismatched-new-field' -Fields @{
            title = 'mismatched-new-field'; session_id = 'mismatched-new-field'; cwd = 'C:/fake'
            pid = $longRunner.Id; pid_started_at = ($longRunnerStart - 3600); started_at = $longRunnerStart
        }
        Write-RawEntry -Directory $sessionsDirectory -SessionId 'legacy-dead' -Fields @{
            title = 'legacy-dead'; session_id = 'legacy-dead'; cwd = 'C:/fake'
            pid = $deadPid; started_at = $deadRunnerStart
        }
        Write-RawEntry -Directory $sessionsDirectory -SessionId 'stale-new-field' -Fields @{
            title = 'stale-new-field'; session_id = 'stale-new-field'; cwd = 'C:/fake'
            pid = $deadPid; pid_started_at = $deadRunnerStart; started_at = $deadRunnerStart
        }

        $previousState3 = $env:AGENT_STATE_DIRECTORY
        $env:AGENT_STATE_DIRECTORY = $registryState
        try {
            . $peerCli list -All | Out-Null
            Assert-True -Actual (Get-SessionLiveness -ProcessId $longRunner.Id -PidStartedAt $longRunnerStart -LegacyStartedAt $longRunnerStart) `
                -Message 'Get-SessionLiveness did not treat a matching pid_started_at as alive.'
            Assert-False -Actual (Get-SessionLiveness -ProcessId $longRunner.Id -PidStartedAt ($longRunnerStart - 3600) -LegacyStartedAt $longRunnerStart) `
                -Message 'Get-SessionLiveness did not treat a pid_started_at 1 hour off as not alive.'
            Assert-Null -Actual (Get-SessionLiveness -ProcessId $deadPid -PidStartedAt $null -LegacyStartedAt $deadRunnerStart) `
                -Message 'Get-SessionLiveness did not treat a legacy entry with a dead pid as unknown.'
            Assert-False -Actual (Get-SessionLiveness -ProcessId $deadPid -PidStartedAt $deadRunnerStart -LegacyStartedAt $deadRunnerStart) `
                -Message 'Get-SessionLiveness did not treat a new-field entry with a dead pid as provably not alive.'

            Assert-Throws -Block { & $peerCli close 'legacy-dead' } `
                -Message 'close did not refuse an unknown (legacy, dead-pid) entry without -Force.'

            & $peerCli close 'mismatched-new-field' | Out-Null
            Assert-True -Actual ($null -ne (Get-Process -Id $longRunner.Id -ErrorAction SilentlyContinue)) `
                -Message 'close against a provably stale (mismatched start time) entry stopped the still-running process.'

            & $peerCli close 'stale-new-field' | Out-Null

            $closeTabScript = Join-Path $repository '.agents\machine\utility\peer-cli\scripts\close-tab.ps1'
            . $closeTabScript -List | Out-Null

            Assert-True -Actual (Test-TabIsLive -Title 'legacy-dead') `
                -Message 'Test-TabIsLive did not treat a legacy dead-pid entry as live.'
            Assert-False -Actual (Test-TabIsLive -Title 'stale-new-field') `
                -Message 'Test-TabIsLive did not treat a provably-stale new-field entry as closable.'
            Assert-True -Actual (Test-TabIsLive -Title 'alive-new-field') `
                -Message 'Test-TabIsLive did not treat a matching live entry as live.'

            $includeUnrecordedOutput = (& $peerCli list -All -IncludeUnrecorded 2>&1 | Out-String)
            Assert-Contains -Actual $includeUnrecordedOutput -Expected ([string]$longRunner.Id) `
                -Message '-IncludeUnrecorded did not list the fake long-running codex-named host.'

            & $peerCli close 'alive-new-field' -Force | Out-Null
            Assert-True -Actual (Wait-ProcessGone -ProcessId $longRunner.Id) `
                -Message 'close -Force against a matching-start-time live entry did not stop the process.'
        }
        finally {
            $env:AGENT_STATE_DIRECTORY = $previousState3
        }
    }
    finally {
        foreach ($proc in @($longRunner)) {
            if ($proc -and (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) {
                & taskkill.exe /PID $proc.Id /T /F 2>$null | Out-Null
            }
            if ($proc) { $proc.WaitForExit(); $proc.Dispose() }
        }
    }
}
finally {
    $env:AGENT_STATE_DIRECTORY = $originalStateDirectory
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS peer-cli.tests.ps1'
