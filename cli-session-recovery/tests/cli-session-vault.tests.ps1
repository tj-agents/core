$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot '..\cli-session-vault.psm1'
Import-Module $modulePath -Force

function New-TestEntry([string]$Tool, [string]$Id, [string]$TerminalId, [string]$Source, [string]$WindowGroup = $null) {
    [pscustomobject][ordered]@{
        tool = $Tool
        id = $Id
        cwd = 'C:\repo'
        title = 'repo'
        transcriptPath = "C:\transcripts\$Id.jsonl"
        terminalId = $TerminalId
        windowGroup = $WindowGroup
        processId = 100
        processStartedAt = '2026-08-04T08:00:00Z'
        startedAt = '2026-08-04T09:00:00Z'
        lastSeenAt = '2026-08-04T09:00:00Z'
        source = $Source
    }
}

function Assert-Equal($Expected, $Actual, [string]$Message) {
    if ($Expected -ne $Actual) {
        throw "$Message Expected=[$Expected] Actual=[$Actual]"
    }
}

$old = New-TestEntry codex old terminal-one startup
$otherTerminal = New-TestEntry codex other terminal-two startup
$claudeSameTerminal = New-TestEntry claude claude terminal-one startup
$cleared = New-TestEntry codex cleared terminal-one clear

$emptySessions = @()
$firstSession = @(Update-CliSessionSet -Sessions $emptySessions -HookEventName SessionStart -Tool codex -SessionId old -Entry $old)
Assert-Equal 1 $firstSession.Count 'The first hook event must populate an empty active registry.'
$nullSessions = $null
$firstNullSession = @(Update-CliSessionSet -Sessions $nullSessions -HookEventName SessionStart -Tool codex -SessionId old -Entry $old)
Assert-Equal 1 $firstNullSession.Count 'The first hook event must populate an uninitialized active registry.'

$afterClear = @(Update-CliSessionSet @($old, $otherTerminal, $claudeSameTerminal) SessionStart codex cleared $cleared)
Assert-Equal 3 $afterClear.Count '/clear must replace only the previous Codex chat in its terminal.'
Assert-Equal 0 @($afterClear | Where-Object id -eq old).Count 'The pre-clear chat must leave the active set.'
Assert-Equal 1 @($afterClear | Where-Object id -eq cleared).Count 'The post-clear chat must enter the active set.'
Assert-Equal 1 @($afterClear | Where-Object id -eq other).Count 'A different terminal must be preserved.'
Assert-Equal 1 @($afterClear | Where-Object id -eq claude).Count 'A different tool in the same terminal must be preserved.'

$afterLateEnd = @(Update-CliSessionSet $afterClear SessionEnd codex old)
Assert-Equal 3 $afterLateEnd.Count 'A delayed predecessor SessionEnd must not remove its replacement.'
Assert-Equal 1 @($afterLateEnd | Where-Object id -eq cleared).Count 'The replacement must survive a delayed predecessor SessionEnd.'

$compacted = New-TestEntry codex cleared terminal-one compact
$afterCompact = @(Update-CliSessionSet $afterLateEnd SessionStart codex cleared $compacted)
Assert-Equal 3 $afterCompact.Count 'Compaction must update in place.'
Assert-Equal 1 @($afterCompact | Where-Object id -eq cleared).Count 'Compaction must not duplicate a chat.'
Assert-Equal compact (@($afterCompact | Where-Object id -eq cleared)[0].source) 'Compaction must retain the updated entry.'

$legacy = New-TestEntry codex legacy migrated-live-process legacy-final-snapshot
$afterLegacy = @(Update-CliSessionSet @($legacy, $old) SessionStart codex cleared $cleared)
Assert-Equal 2 $afterLegacy.Count 'Unrelated legacy entries require explicit reconciliation.'
Assert-Equal 1 @($afterLegacy | Where-Object id -eq legacy).Count 'The runtime invariant must not guess across unrelated terminal identities.'

$olderOwned = New-TestEntry codex old terminal-one resume
$olderOwned.processId = 200
$olderOwned.processStartedAt = '2026-08-04T08:00:00Z'
$olderOwned.lastSeenAt = '2026-08-04T08:30:00Z'
$newerOwned = New-TestEntry codex cleared terminal-one clear
$newerOwned.processId = 200
$newerOwned.processStartedAt = '2026-08-04T08:00:00Z'
$newerOwned.lastSeenAt = '2026-08-04T09:30:00Z'
$ownedProcess = [pscustomobject]@{
    Name = 'codex.exe'
    ProcessId = 200
    ParentProcessId = 300
    CreationDate = [datetime]'2026-08-04T08:00:00Z'
    ExecutablePath = 'C:\node_modules\@openai\codex\vendor\codex.exe'
    CommandLine = 'codex.exe resume 00000000-0000-0000-0000-000000000001'
}
$fallbackProcess = [pscustomobject]@{
    Name = 'codex.exe'
    ProcessId = 201
    ParentProcessId = 300
    CreationDate = [datetime]'2026-08-04T08:01:00Z'
    ExecutablePath = 'C:\node_modules\@openai\codex\vendor\codex.exe'
    CommandLine = 'codex.exe resume 00000000-0000-0000-0000-000000000002'
}
$terminalProcess = [pscustomobject]@{
    Name = 'WindowsTerminal.exe'
    ProcessId = 300
    ParentProcessId = 1
    CreationDate = [datetime]'2026-08-04T07:59:00Z'
    CommandLine = 'WindowsTerminal.exe -Embedding'
}
$recoveryData = [pscustomobject]@{ bootId = 'unknown'; sessions = @($olderOwned, $newerOwned) }
$liveKeys = Get-LiveCliSessionKeys $recoveryData @($ownedProcess, $fallbackProcess, $terminalProcess)
Assert-Equal $true $liveKeys.ContainsKey('codex:cleared') 'The latest hook-owned ID must represent a live post-clear process.'
Assert-Equal $false $liveKeys.ContainsKey('codex:old') 'An older hook-owned ID for the same process must not remain live.'
Assert-Equal $false $liveKeys.ContainsKey('codex:00000000-0000-0000-0000-000000000001') 'The launch argument must not override a newer hook-owned ID.'
Assert-Equal $true $liveKeys.ContainsKey('codex:00000000-0000-0000-0000-000000000002') 'The launch argument must remain the fallback without hook ownership.'

$writerIdA = '00000000-0000-0000-0000-000000000005'
$writerIdB = '00000000-0000-0000-0000-000000000006'
$writerIdC = '00000000-0000-0000-0000-000000000007'
$writerProcess = [pscustomobject]@{
    Name = 'codex.exe'
    ProcessId = 205
    ParentProcessId = 300
    CreationDate = [datetime]'2026-08-04T08:02:00Z'
    ExecutablePath = 'C:\node_modules\@openai\codex\vendor\codex.exe'
    CommandLine = 'codex.exe'
}
$writerPaths = @(
    "C:\Users\TommySeery\.codex\sessions\rollout-$writerIdA.jsonl",
    "C:\Users\TommySeery\.codex\sessions\rollout-$writerIdB.jsonl"
)
$writerLiveKeys = Get-LiveCliSessionKeys ([pscustomobject]@{ sessions=@() }) @($writerProcess, $terminalProcess) @{ 205=$writerPaths }
Assert-Equal $true $writerLiveKeys.ContainsKey("codex:$writerIdA") 'An open transcript must identify a live Codex conversation when its command line has no resume ID.'
Assert-Equal $true $writerLiveKeys.ContainsKey("codex:$writerIdB") 'One Codex process must expose every distinct transcript it currently writes.'
Assert-Equal 2 $writerLiveKeys.Count 'Transcript discovery must remain conversation-based when one process owns multiple IDs.'
$writerOwned = New-TestEntry codex old terminal-writer clear
$writerOwned.processId = 205
$writerOwned.processStartedAt = '2026-08-04T08:02:00Z'
$replacementWriterKeys = Get-LiveCliSessionKeys ([pscustomobject]@{ sessions=@($writerOwned) }) @($writerProcess, $terminalProcess) @{ 205=@($writerPaths[1]) }
Assert-Equal $false $replacementWriterKeys.ContainsKey('codex:old') 'A verified writer ID must replace stale hook ownership for the same process.'
Assert-Equal $true $replacementWriterKeys.ContainsKey("codex:$writerIdB") 'The current writer ID must survive stale hook replacement.'

$writerScratch = Join-Path ([System.IO.Path]::GetTempPath()) "cli-session-writers-$([guid]::NewGuid().ToString('N'))"
$writerRoot = Join-Path $writerScratch '.codex\sessions'
New-Item -ItemType Directory -Path $writerRoot -Force | Out-Null
try {
    $topLevelTranscript = Join-Path $writerRoot "rollout-$writerIdA.jsonl"
    $subagentTranscript = Join-Path $writerRoot "rollout-$writerIdB.jsonl"
    $secondTopLevelTranscript = Join-Path $writerRoot "rollout-$writerIdC.jsonl"
    [System.IO.File]::WriteAllText($topLevelTranscript, '{"type":"session_meta","payload":{"source":"cli"}}', (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($subagentTranscript, '{"type":"session_meta","payload":{"source":{"subagent":{"other":"guardian"}}}}', (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($secondTopLevelTranscript, '{"type":"session_meta","payload":{"source":"cli"}}', (New-Object System.Text.UTF8Encoding($false)))
    $filteredWriterMap = Get-CliTranscriptWriterMatches @($writerProcess) {
        param($Process)
        @($topLevelTranscript, $subagentTranscript, $secondTopLevelTranscript, (Join-Path $writerScratch 'unrelated.jsonl'))
    }
    Assert-Equal 2 @($filteredWriterMap[205]).Count 'Writer discovery must keep every verified top-level CLI transcript and reject helpers.'
    Assert-Equal $true (@($filteredWriterMap[205]) -contains $topLevelTranscript) 'Writer discovery must preserve the first top-level session ID.'
    Assert-Equal $true (@($filteredWriterMap[205]) -contains $secondTopLevelTranscript) 'Writer discovery must preserve a second top-level session ID held by the same writer.'
    $secondWriterProcess = $writerProcess.PSObject.Copy()
    $secondWriterProcess.ProcessId = 206
    $batchCalls = 0
    $batchProcessCount = 0
    $batchedWriterMap = Get-CliTranscriptWriterMatches -Processes @($writerProcess, $secondWriterProcess) -BatchOpenFileResolver {
        param($Processes)
        $script:batchCalls++
        $script:batchProcessCount = @($Processes).Count
        @{ 205=@($topLevelTranscript); 206=@($secondTopLevelTranscript) }
    }
    Assert-Equal 1 $batchCalls 'Writer discovery must inspect the machine-wide handle table only once for all CLI processes.'
    Assert-Equal 2 $batchProcessCount 'The batch handle probe must receive every CLI writer together.'
    Assert-Equal 1 @($batchedWriterMap[205]).Count 'The batch handle probe must preserve the first writer result.'
    Assert-Equal 1 @($batchedWriterMap[206]).Count 'The batch handle probe must preserve the second writer result.'
    Assert-Equal $false (Test-CliTranscriptIsResumable codex $subagentTranscript) 'A Codex guardian subagent must never become a recoverable Terminal conversation.'
    $slowProbe = Join-Path $writerScratch 'slow-probe.ps1'
    [System.IO.File]::WriteAllText($slowProbe, "param([int[]]`$ProcessId,[string]`$OutputPath,[string]`$ErrorPath)`r`nStart-Sleep -Seconds 10", (New-Object System.Text.UTF8Encoding($false)))
    $probeTimedOut = $false
    $probeTimeoutError = $null
    try {
        & (Get-Module cli-session-vault) {
            param($Process, $Worker)
            Invoke-CliOpenFileProbeWorker @($Process) 200 $Worker
        } $writerProcess $slowProbe | Out-Null
    } catch {
        $probeTimeoutError = $_.Exception.Message
        $probeTimedOut = $_.Exception.Message -like 'Transcript inspection exceeded*'
    }
    Assert-Equal $true $probeTimedOut "A stalled handle probe must be stopped at its deadline instead of hanging desktop Save. Error: $probeTimeoutError"
    $claudeTopLevelTranscript = Join-Path $writerScratch ".claude\projects\project\$writerIdA.jsonl"
    $claudeSubagentTranscript = Join-Path $writerScratch ".claude\projects\project\$writerIdA\subagents\agent-$writerIdB.jsonl"
    New-Item -ItemType Directory -Path (Split-Path -Parent $claudeTopLevelTranscript) -Force | Out-Null
    New-Item -ItemType Directory -Path (Split-Path -Parent $claudeSubagentTranscript) -Force | Out-Null
    [System.IO.File]::WriteAllText($claudeTopLevelTranscript, '{}', (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($claudeSubagentTranscript, '{}', (New-Object System.Text.UTF8Encoding($false)))
    Assert-Equal $true (Test-CliTranscriptIsResumable claude $claudeTopLevelTranscript) 'A top-level Claude transcript must remain recoverable.'
    Assert-Equal $false (Test-CliTranscriptIsResumable claude $claudeSubagentTranscript) 'A Claude subagent must never become a recoverable Terminal conversation.'
    $claudeWriterProcess = [pscustomobject]@{
        Name = 'claude.exe'
        ProcessId = 207
        ParentProcessId = 300
        CreationDate = [datetime]'2026-08-04T08:03:00Z'
        ExecutablePath = 'C:\Users\TommySeery\.local\bin\claude.exe'
        CommandLine = 'C:\Users\TommySeery\.local\bin\claude.exe'
    }
    $claudeResolverCalls = 0
    $claudeWriterMap = Get-CliTranscriptWriterMatches -Processes @($claudeWriterProcess) -BatchOpenFileResolver {
        @{ 207=@('C:\repo\.claude') }
    } -ClaudeTranscriptResolver {
        param($Process, $OpenFiles)
        $script:claudeResolverCalls++
        $claudeTopLevelTranscript
    }
    Assert-Equal 1 $claudeResolverCalls 'Claude discovery must resolve the exact registered transcript without relying on an open transcript handle.'
    Assert-Equal $claudeTopLevelTranscript @($claudeWriterMap[207])[0] 'Claude registered-session discovery must retain the current top-level transcript.'
    $originalUserProfile = $env:USERPROFILE
    try {
        $env:USERPROFILE = $writerScratch
        $claudeCwd = Join-Path $writerScratch 'repo'
        $encodedClaudeCwd = $claudeCwd -replace '[:\\/]', '-'
        $actualClaudeProject = Join-Path $writerScratch ".claude\projects\$encodedClaudeCwd"
        $claudeSessions = Join-Path $writerScratch '.claude\sessions'
        New-Item -ItemType Directory -Path $actualClaudeProject,$claudeSessions,$claudeCwd -Force | Out-Null
        $sameCwdProcess = $claudeWriterProcess.PSObject.Copy()
        $sameCwdProcess.ProcessId = 208
        $sameCwdProcess.CreationDate = [datetime]'2026-08-04T08:04:00Z'
        $claudeWriterProcess.CommandLine = "C:\Users\TommySeery\.local\bin\claude.exe --resume $writerIdB"
        $firstClaudeTranscript = Join-Path $actualClaudeProject "$writerIdA.jsonl"
        $secondClaudeTranscript = Join-Path $actualClaudeProject "$writerIdC.jsonl"
        [System.IO.File]::WriteAllText($firstClaudeTranscript, '{}', (New-Object System.Text.UTF8Encoding($false)))
        [System.IO.File]::WriteAllText($secondClaudeTranscript, '{}', (New-Object System.Text.UTF8Encoding($false)))
        @{
            pid=207
            sessionId=$writerIdA
            cwd=$claudeCwd
            procStart=$claudeWriterProcess.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString()
        } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $claudeSessions '207.json') -Encoding UTF8
        @{
            pid=208
            sessionId=$writerIdC
            cwd=$claudeCwd
            procStart=$sameCwdProcess.CreationDate.ToUniversalTime().ToFileTimeUtc().ToString()
        } | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $claudeSessions '208.json') -Encoding UTF8
        $registeredClaudeMap = Get-CliTranscriptWriterMatches -Processes @($claudeWriterProcess, $sameCwdProcess) -BatchOpenFileResolver {
            @{ 207=@(); 208=@() }
        }
        Assert-Equal $firstClaudeTranscript @($registeredClaudeMap[207])[0] 'A Claude registration must override an older explicit resume argument after the conversation changes.'
        Assert-Equal $secondClaudeTranscript @($registeredClaudeMap[208])[0] 'Two Claude processes in the same working directory must retain distinct registered sessions.'
        $staleRegistrationRejected = $false
        $sameCwdProcess.CreationDate = $sameCwdProcess.CreationDate.AddMinutes(1)
        try {
            Get-CliTranscriptWriterMatches -Processes @($sameCwdProcess) -BatchOpenFileResolver { @{ 208=@() } } | Out-Null
        } catch {
            $staleRegistrationRejected = $_.Exception.Message -like 'Claude session registration is stale*'
        }
        Assert-Equal $true $staleRegistrationRejected 'PID reuse must not attach a stale Claude registration to a newer process.'
    } finally {
        $env:USERPROFILE = $originalUserProfile
    }
} finally {
    Remove-Item -LiteralPath $writerScratch -Recurse -Force -ErrorAction SilentlyContinue
}

$liveProbeFailure = [pscustomobject]@{
    Name = 'codex.exe'
    ProcessId = $PID
    ParentProcessId = 300
    CreationDate = [datetime]'2026-08-04T08:02:00Z'
    ExecutablePath = 'C:\node_modules\@openai\codex\vendor\codex.exe'
    CommandLine = 'codex.exe'
}
$probeFailedLoudly = $false
try {
    Get-CliTranscriptWriterMatches @($liveProbeFailure) { throw 'probe denied' } | Out-Null
} catch {
    $probeFailedLoudly = $_.Exception.Message -like 'Cannot inspect transcript handles for live codex process*'
}
Assert-Equal $true $probeFailedLoudly 'A writer-inspection failure for a still-live CLI must fail loudly instead of silently omitting it.'

$orphanedProcess = [pscustomobject]@{
    Name = 'codex.exe'
    ProcessId = 202
    ParentProcessId = 999
    CreationDate = [datetime]'2026-08-04T08:02:00Z'
    ExecutablePath = 'C:\node_modules\@openai\codex\vendor\codex.exe'
    CommandLine = 'codex.exe resume 00000000-0000-0000-0000-000000000003'
}
$orphanedKeys = Get-LiveCliSessionKeys $recoveryData @($orphanedProcess)
Assert-Equal 0 $orphanedKeys.Count 'A CLI whose Terminal parent is gone must not block restore.'
Assert-Equal 1 @(Get-OrphanedCliProcesses @($orphanedProcess)).Count 'A CLI whose Terminal parent is gone must be reported as detached.'

$reusedTerminalPid = [pscustomobject]@{
    Name = 'WindowsTerminal.exe'
    ProcessId = 999
    ParentProcessId = 1
    CreationDate = [datetime]'2026-08-04T09:00:00Z'
    CommandLine = 'WindowsTerminal.exe -Embedding'
}
Assert-Equal $false (Test-CliProcessHasTerminalAncestor $orphanedProcess (New-CliProcessIndex @($orphanedProcess, $reusedTerminalPid))) 'A newer Terminal process that reused a dead parent PID must not adopt an orphaned CLI.'

$shellProcess = [pscustomobject]@{
    Name = 'powershell.exe'
    ProcessId = 301
    ParentProcessId = 300
    CreationDate = [datetime]'2026-08-04T08:00:30Z'
    CommandLine = 'powershell.exe'
}
$nestedProcess = [pscustomobject]@{
    Name = 'codex.exe'
    ProcessId = 203
    ParentProcessId = 301
    CreationDate = [datetime]'2026-08-04T08:01:30Z'
    ExecutablePath = 'C:\node_modules\@openai\codex\vendor\codex.exe'
    CommandLine = 'codex.exe resume 00000000-0000-0000-0000-000000000004'
}
Assert-Equal $true (Test-CliProcessHasTerminalAncestor $nestedProcess (New-CliProcessIndex @($terminalProcess, $shellProcess, $nestedProcess))) 'A CLI launched through PowerShell must remain live while its Terminal ancestry exists.'

$desktopClaude = [pscustomobject]@{
    Name = 'claude.exe'
    ProcessId = 204
    ParentProcessId = 300
    CreationDate = [datetime]'2026-08-04T08:02:30Z'
    CommandLine = 'C:\Program Files\Claude\claude.exe'
}
Assert-Equal $null (Get-CliProcessTool $desktopClaude) 'Claude Desktop must never be treated as a Claude CLI process.'

$duplicateId = '10000000-0000-0000-0000-000000000001'
$duplicateEntry = New-TestEntry claude $duplicateId terminal-one resume
$duplicateEntry.processId = 401
$duplicateEntry.processStartedAt = '2026-08-04T08:03:00Z'
$endingDuplicate = [pscustomobject]@{
    Name = 'claude.exe'
    ProcessId = 401
    ParentProcessId = 300
    CreationDate = [datetime]'2026-08-04T08:03:00Z'
    CommandLine = "C:\Users\TommySeery\.local\bin\claude.exe --resume $duplicateId"
}
$survivingDuplicate = [pscustomobject]@{
    Name = 'claude.exe'
    ProcessId = 402
    ParentProcessId = 300
    CreationDate = [datetime]'2026-08-04T08:04:00Z'
    CommandLine = "C:\Users\TommySeery\.local\bin\claude.exe --resume $duplicateId"
}
$afterDuplicateEnd = @(Update-CliSessionSetForEnd @($duplicateEntry) claude $duplicateId @($endingDuplicate, $survivingDuplicate, $terminalProcess) $endingDuplicate)
Assert-Equal 1 $afterDuplicateEnd.Count 'Closing one duplicate process must retain the surviving logical conversation.'
Assert-Equal 402 $afterDuplicateEnd[0].processId 'The surviving duplicate process must become the registry owner.'
$afterFinalDuplicateEnd = @(Update-CliSessionSetForEnd @($duplicateEntry) claude $duplicateId @($endingDuplicate, $terminalProcess) $endingDuplicate)
Assert-Equal 0 $afterFinalDuplicateEnd.Count 'Closing the final process must remove the logical conversation.'

$emptyClosedSessions = @()
$closedSessions = @(Update-CliClosedSessionSet -ClosedSessions $emptyClosedSessions -HookEventName SessionEnd -Tool claude -SessionId $duplicateId -SessionStillActive $false -ProcessId $endingDuplicate.ProcessId -ProcessStartedAt $endingDuplicate.CreationDate.ToUniversalTime().ToString('o'))
Assert-Equal 1 $closedSessions.Count 'Closing the final copy of a conversation must record a tombstone.'
$nullClosedSessions = $null
Assert-Equal 1 @(Update-CliClosedSessionSet -ClosedSessions $nullClosedSessions -HookEventName SessionEnd -Tool claude -SessionId $duplicateId -SessionStillActive $false).Count 'The first close event must populate an uninitialized tombstone registry.'
$filteredClosedMap = Get-OpenCliSessionProcessMap @{ "claude:$duplicateId" = $survivingDuplicate; 'codex:old' = $ownedProcess } ([pscustomobject]@{ sessions=$closedSessions })
Assert-Equal $false $filteredClosedMap.ContainsKey("claude:$duplicateId") 'A lingering process must not resurrect a conversation after SessionEnd.'
Assert-Equal $true $filteredClosedMap.ContainsKey('codex:old') 'A tombstone must not remove unrelated live conversations.'
$duplicateStillOpen = @(Update-CliClosedSessionSet @() SessionEnd claude $duplicateId $true)
Assert-Equal 0 $duplicateStillOpen.Count 'Closing one duplicate must not tombstone a conversation that is still open elsewhere.'
$delayedStartSessions = @(Update-CliClosedSessionSet $closedSessions SessionStart claude $duplicateId $false $endingDuplicate.ProcessId $endingDuplicate.CreationDate.ToUniversalTime().ToString('o'))
Assert-Equal 1 $delayedStartSessions.Count 'A delayed start event from the closed process must not erase its tombstone.'
$reopenedSessions = @(Update-CliClosedSessionSet $closedSessions SessionStart claude $duplicateId $false 999 '2026-08-04T10:00:00Z')
Assert-Equal 0 $reopenedSessions.Count 'Starting a closed conversation again must clear its tombstone.'

$olderSource = [pscustomobject]@{
    Path = 'older.json'
    Priority = 90
    Data = [pscustomobject]@{ complete=$true; mode='manual'; generatedAt='2026-08-04T09:00:00Z'; sessions=@($old) }
}
$newerConsumedSource = [pscustomobject]@{
    Path = 'newer.json'
    Priority = 80
    Data = [pscustomobject]@{ complete=$true; generatedAt='2026-08-04T10:00:00Z'; consumedAt='2026-08-04T10:01:00Z'; sessions=@($cleared) }
}
$selectedSource = Select-NewestCliRecoverySource @($olderSource, $newerConsumedSource)
Assert-Equal older.json $selectedSource.Path 'An unconsumed desktop Save must remain authoritative even when active state is newer.'
$olderSource.Data | Add-Member -NotePropertyName consumedAt -NotePropertyValue '2026-08-04T09:01:00Z'
$selectedConsumedSource = Select-NewestCliRecoverySource @($olderSource, $newerConsumedSource)
Assert-Equal newer.json $selectedConsumedSource.Path 'After the desktop Save is consumed, Restore must use the newest complete set.'
$legacyAutosaveAtPinnedPath = [pscustomobject]@{
    Path = 'pinned.json'
    Priority = 90
    Data = [pscustomobject]@{ complete=$true; mode='autosave'; generatedAt='2026-08-04T09:00:00Z'; sessions=@($old) }
}
$selectedOverLegacyAutosave = Select-NewestCliRecoverySource @($legacyAutosaveAtPinnedPath, $newerConsumedSource)
Assert-Equal newer.json $selectedOverLegacyAutosave.Path 'A legacy autosave in pinned.json must not gain manual-save authority from its filename.'
Assert-Equal 0 @(Get-CliSnapshotUnsavedSessions $olderSource.Data).Count 'A legacy snapshot with no unsaved-session field must not produce a blank warning.'
$partialSnapshot = New-CliSessionSnapshot manual @($old) '2026-08-04T08:00:00Z' @('codex:cannot-recover')
Assert-Equal 'codex:cannot-recover' @(Get-CliSnapshotUnsavedSessions $partialSnapshot)[0] 'A partial snapshot must preserve the exact unsaved session key.'

$closed = New-TestEntry codex closed terminal-three startup
$liveProcessMap = @{ 'codex:old' = $ownedProcess }
$liveEntries = @(Select-LiveCliSessionEntries ([pscustomobject]@{ sessions=@($old, $closed) }) $liveProcessMap)
Assert-Equal 1 $liveEntries.Count 'Saving must exclude sessions whose CLI process has closed.'
Assert-Equal old $liveEntries[0].id 'Saving must retain the session whose CLI process is live.'

$fallbackEntry = New-TestEntry codex not-registered terminal-four resume
$resolvedLive = Resolve-LiveCliSessionEntries @(
    [pscustomobject]@{ sessions=@($old) },
    [pscustomobject]@{ sessions=@($fallbackEntry) }
) @{ 'codex:old' = $ownedProcess; 'codex:not-registered' = $fallbackProcess }
Assert-Equal 2 $resolvedLive.Entries.Count 'Saving must recover a live session from prior recovery data when the active registry entry is missing.'
Assert-Equal 0 $resolvedLive.MissingKeys.Count 'A recovered fallback entry must not be reported as unsaved.'

$inheritScratch = Join-Path ([System.IO.Path]::GetTempPath()) "cli-session-inherit-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $inheritScratch -Force | Out-Null
try {
    $inheritedId = '00000000-0000-0000-0000-000000000007'
    $inheritedTranscript = Join-Path $inheritScratch "rollout-$inheritedId.jsonl"
    [System.IO.File]::WriteAllText($inheritedTranscript, ('{"timestamp":"2026-08-04T08:02:00Z","payload":{"cwd":' + ($inheritScratch | ConvertTo-Json -Compress) + '}}'), (New-Object System.Text.UTF8Encoding($false)))
    $previousProcessEntry = New-TestEntry codex predecessor terminal-inherit clear 'windows-terminal-window:555'
    $previousProcessEntry.processId = $fallbackProcess.ProcessId
    $previousProcessEntry.processStartedAt = $fallbackProcess.CreationDate.ToUniversalTime().ToString('o')
    $inheritedResolution = Resolve-LiveCliSessionEntries @([pscustomobject]@{ sessions=@($previousProcessEntry) }) @{ "codex:$inheritedId"=$fallbackProcess } {
        param($Tool, $Id)
        Get-Item -LiteralPath $inheritedTranscript
    }
    Assert-Equal 'windows-terminal-window:555' (Get-CliSessionWindowGroup $inheritedResolution.Entries[0]) 'A replacement transcript must inherit the verified window of the same creation-time-valid process.'
} finally {
    Remove-Item -LiteralPath $inheritScratch -Recurse -Force -ErrorAction SilentlyContinue
}

$partiallyResolvedLive = Resolve-LiveCliSessionEntries @(
    [pscustomobject]@{ sessions=@($old) }
) @{ 'codex:old' = $ownedProcess; 'codex:cannot-recover' = $fallbackProcess }
Assert-Equal 1 $partiallyResolvedLive.Entries.Count 'One missing registry entry must not prevent healthy live sessions from being saved.'
Assert-Equal 'codex:cannot-recover' $partiallyResolvedLive.MissingKeys[0] 'A live session with no usable metadata must be reported explicitly.'

$transcriptScratch = Join-Path ([System.IO.Path]::GetTempPath()) "cli-session-transcript-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $transcriptScratch -Force | Out-Null
try {
    $discoveredId = '00000000-0000-0000-0000-000000000007'
    $discoveredTranscript = Join-Path $transcriptScratch "rollout-$discoveredId.jsonl"
    $cwdJson = $transcriptScratch.Replace('\', '\\')
    @(
        "{`"timestamp`":`"2026-08-04T08:02:00Z`",`"type`":`"session_meta`",`"payload`":{`"cwd`":`"$cwdJson`"}}",
        '{"timestamp":"2026-08-04T09:02:00Z","type":"event_msg","payload":{"type":"user_message"}}'
    ) | Set-Content -LiteralPath $discoveredTranscript -Encoding UTF8
    $discoveredProcessMap = Get-LiveCliSessionProcessMap ([pscustomobject]@{ sessions=@() }) @($writerProcess, $terminalProcess) @{ 205=@($discoveredTranscript) }
    $discoveredEntries = Resolve-LiveCliSessionEntries @() $discoveredProcessMap
    Assert-Equal 1 $discoveredEntries.Entries.Count 'Save must synthesize recovery metadata directly from a live transcript when all hook registries missed it.'
    Assert-Equal $discoveredId $discoveredEntries.Entries[0].id 'Synthesized recovery metadata must retain the transcript session ID.'
    Assert-Equal $discoveredTranscript $discoveredEntries.Entries[0].transcriptPath 'Metadata resolution must reuse the verified writer path instead of recursively scanning the transcript archive.'
    Assert-Equal '2026-08-04T09:02:00Z' $discoveredEntries.Entries[0].lastSeenAt 'Synthesized recovery metadata must use transcript activity for recency.'
    Assert-Equal 0 $discoveredEntries.MissingKeys.Count 'A live transcript with valid metadata must never be reported as unsaved.'
} finally {
    Remove-Item -LiteralPath $transcriptScratch -Recurse -Force -ErrorAction SilentlyContinue
}

$emptyWindowGroups = @(Set-CliSessionWindowGroups -Entries @() -ProcessMap @{})
Assert-Equal 0 $emptyWindowGroups.Count 'An empty live set must remain empty without being mistaken for the process map.'

$sameWindowA = New-TestEntry codex window-a terminal-a startup 'windows-terminal-window:100'
$sameWindowB = New-TestEntry claude window-b terminal-b startup 'windows-terminal-window:100'
$otherWindow = New-TestEntry codex window-c terminal-c startup 'windows-terminal-window:200'
Assert-Equal (Get-CliRestoreWindowTarget $sameWindowA) (Get-CliRestoreWindowTarget $sameWindowB) 'Sessions from one Terminal window must restore into one named window.'
Assert-Equal $false ((Get-CliRestoreWindowTarget $sameWindowA) -eq (Get-CliRestoreWindowTarget $otherWindow)) 'Sessions from different Terminal windows must restore into different named windows.'

$launchArguments = @(Get-CliRestoreLaunchArguments $sameWindowA 'C:\Users\TommySeery\start-saved-cli.ps1')
$profileIndex = [array]::IndexOf($launchArguments, '--profile')
Assert-Equal '{61c54bbd-c2c6-5271-96e7-009a87ff44bf}' $launchArguments[$profileIndex + 1] 'Restore must use the Windows PowerShell profile and its icon.'
Assert-Equal $true ($launchArguments -contains 'powershell.exe') 'Restore must launch the same shell as the selected Windows PowerShell profile.'
Assert-Equal $false ($launchArguments -contains '-NoProfile') 'Restore must load PowerShell normally instead of bypassing the user profile.'
Assert-Equal $true ($launchArguments -contains 'repo [window-a]') 'Restored tab titles must include a short session ID so conversations are distinguishable.'
$stableRestoreGroup = New-TestEntry claude stable-group terminal-stable resume 'cli-recovery-0123456789abcdef'
Assert-Equal 'cli-recovery-0123456789abcdef' (Get-CliRestoreWindowTarget $stableRestoreGroup) 'A restored named window must remain stable across later recovery cycles.'

$lockScratch = Join-Path ([System.IO.Path]::GetTempPath()) "cli-session-lock-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $lockScratch -Force | Out-Null
$blockerScript = Join-Path $lockScratch 'hold-lock.ps1'
$testMutexName = "Local\CliSessionVaultTest$([guid]::NewGuid().ToString('N'))"
Set-Content -LiteralPath $blockerScript -Encoding UTF8 -Value @'
param([string]$Ready, [int]$HoldSeconds, [string]$MutexName)
$mutex = New-Object System.Threading.Mutex($false, $MutexName)
$mutex.WaitOne() | Out-Null
Set-Content -LiteralPath $Ready -Value 'ready'
Start-Sleep -Seconds $HoldSeconds
'@

function Start-LockHolder([string]$Scratch, [string]$Script, [int]$HoldSeconds, [string]$MutexName) {
    $ready = Join-Path $Scratch "ready-$([guid]::NewGuid().ToString('N')).txt"
    $holder = Start-Process -FilePath 'powershell.exe' -PassThru -WindowStyle Hidden -ArgumentList @(
        '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$Script`"", '-Ready', "`"$ready`"", '-HoldSeconds', $HoldSeconds, '-MutexName', $MutexName
    )
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $ready)) { Start-Sleep -Milliseconds 100 }
    if (-not (Test-Path -LiteralPath $ready)) {
        Stop-Process -Id $holder.Id -Force -ErrorAction SilentlyContinue
        throw 'The test lock holder never acquired the registry lock.'
    }
    return $holder
}

$blocker = Start-LockHolder $lockScratch $blockerScript 30 $testMutexName
try {
    $blockedSaveRan = $false
    Invoke-WithCliSessionLock -TimeoutMilliseconds 1000 -ProceedWithoutLock -MutexName $testMutexName { $script:blockedSaveRan = $true } | Out-Null
    Assert-Equal $true $blockedSaveRan 'A busy registry lock must never stop a save from writing.'
    Assert-Equal $false (Get-CliSessionLastLockAcquired) 'A save that proceeds without the lock must report that it did.'

    $blockedHookFailed = $false
    try {
        Invoke-WithCliSessionLock -TimeoutMilliseconds 1000 -MutexName $testMutexName { 'unreachable' } | Out-Null
    } catch {
        $blockedHookFailed = $true
    }
    Assert-Equal $true $blockedHookFailed 'A hook must still fail closed rather than write without the lock.'

    $saveLockRan = $false
    $saveLockFailed = $false
    try {
        Invoke-WithCliSessionSaveLock -TimeoutMilliseconds 1000 -MutexName $testMutexName { $script:saveLockRan = $true } | Out-Null
    } catch {
        $saveLockFailed = $_.Exception.Message -eq 'Another CLI session save is already running.'
    }
    Assert-Equal $true $saveLockFailed 'A second desktop Save must fail immediately while a Save is already running.'
    Assert-Equal $false $saveLockRan 'Concurrent desktop Saves must not repeat expensive discovery work.'

    $pinVault = Join-Path $lockScratch 'pin-vault'
    New-Item -ItemType Directory -Path $pinVault -Force | Out-Null
    $prepared = New-CliSessionSnapshot autosave @($sameWindowA, $sameWindowB, $otherWindow) '2026-08-04T08:00:00Z'
    Write-CliSessionJson (Join-Path $pinVault 'autosave.json') $prepared
    $autosaveHashBeforePin = (Get-FileHash -LiteralPath (Join-Path $pinVault 'autosave.json') -Algorithm SHA256).Hash
    $pinProcess = Start-Process -FilePath 'powershell.exe' -PassThru -WindowStyle Hidden -ArgumentList @(
        '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$(Join-Path $PSScriptRoot '..\save-sessions.ps1')`"", '-Vault', "`"$pinVault`"", '-Pin', '-Quiet', '-SaveMutexName', $testMutexName
    )
    $pinFinished = $pinProcess.WaitForExit(5000)
    if (-not $pinFinished) { Stop-Process -Id $pinProcess.Id -Force -ErrorAction SilentlyContinue }
    Assert-Equal $true $pinFinished 'Desktop Save must finish within five seconds while the autosave mutex is held.'
    Assert-Equal 0 $pinProcess.ExitCode 'Desktop Save must succeed while autosave is blocked.'
    $pinned = Read-CliSessionJson (Join-Path $pinVault 'pinned.json')
    Assert-Equal manual $pinned.mode 'Desktop Save must create a manual authoritative snapshot.'
    Assert-Equal 3 @($pinned.sessions).Count 'Desktop Save must atomically copy every prepared session without discovery.'
    Assert-Equal autosave $pinned.sourceMode 'Desktop Save must record that it pinned the completed autosave state.'
    Assert-Equal $autosaveHashBeforePin (Get-FileHash -LiteralPath (Join-Path $pinVault 'autosave.json') -Algorithm SHA256).Hash 'Desktop Save must never mutate the autosave source.'
    $pinnedHashBeforeRepeat = (Get-FileHash -LiteralPath (Join-Path $pinVault 'pinned.json') -Algorithm SHA256).Hash
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot '..\save-sessions.ps1') -Vault $pinVault -Pin -Quiet -SaveMutexName $testMutexName
    Assert-Equal 0 $LASTEXITCODE 'A repeated desktop Save must also bypass autosave contention.'
    Assert-Equal $pinnedHashBeforeRepeat (Get-FileHash -LiteralPath (Join-Path $pinVault 'pinned.json') -Algorithm SHA256).Hash 'Desktop Save must not replace a newer unconsumed manual pin with older prepared state.'
} finally {
    Stop-Process -Id $blocker.Id -Force -ErrorAction SilentlyContinue
    $blocker.WaitForExit(5000) | Out-Null
    Invoke-WithCliSessionLock -TimeoutMilliseconds 5000 -MutexName $testMutexName { } | Out-Null
}

$saveLockRan = $false
Invoke-WithCliSessionSaveLock -TimeoutMilliseconds 1000 -MutexName $testMutexName { $script:saveLockRan = $true } | Out-Null
Assert-Equal $true $saveLockRan 'The save-wide lock must be released after the active Save exits.'

$abandonedRan = $false
$abandoner = Start-LockHolder $lockScratch $blockerScript 60 $testMutexName
try {
    Stop-Process -Id $abandoner.Id -Force -ErrorAction SilentlyContinue
    $abandoner.WaitForExit(5000) | Out-Null
    Invoke-WithCliSessionLock -TimeoutMilliseconds 5000 -MutexName $testMutexName { $script:abandonedRan = $true } | Out-Null
} finally {
    Stop-Process -Id $abandoner.Id -Force -ErrorAction SilentlyContinue
}
Assert-Equal $true $abandonedRan 'A lock abandoned by a killed holder must not fail the next save.'
Assert-Equal $true (Get-CliSessionLastLockAcquired) 'An abandoned mutex must count as acquired.'

$reacquiredRan = $false
Invoke-WithCliSessionLock -TimeoutMilliseconds 5000 -MutexName $testMutexName { $script:reacquiredRan = $true } | Out-Null
Assert-Equal $true $reacquiredRan 'The lock must be released after an abandoned-mutex acquisition.'
Remove-Item -LiteralPath $lockScratch -Recurse -Force -ErrorAction SilentlyContinue

$cachedDiscovery = @{
    TitleMap = @{}
    ProcessWindowGroups = @{ '100' = 'windows-terminal-window:900' }
}
$cachedEntry = New-TestEntry codex cached terminal-cached startup
$cachedMap = @{ 'codex:cached' = [pscustomobject]@{ ProcessId = 100 } }
$discoveryStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$cachedResult = @(Set-CliSessionWindowGroups -Entries @($cachedEntry) -ProcessMap $cachedMap -Discovery $cachedDiscovery)
$discoveryStopwatch.Stop()
Assert-Equal 'windows-terminal-window:900' (Get-CliSessionWindowGroup $cachedResult[0]) 'A supplied window discovery must be used verbatim.'
Assert-Equal $true ($discoveryStopwatch.Elapsed.TotalSeconds -lt 2) 'A supplied window discovery must skip all Terminal probing.'
$staleCachedEntry = New-TestEntry codex cached terminal-cached startup 'cli-recovery-stale'
$refreshedCachedResult = @(Set-CliSessionWindowGroups -Entries @($staleCachedEntry) -ProcessMap $cachedMap -Discovery $cachedDiscovery)
Assert-Equal 'windows-terminal-window:900' (Get-CliSessionWindowGroup $refreshedCachedResult[0]) 'Verified live window discovery must replace a stale saved group.'

$truncatedDiscovery = @{
    TitleMap = @{ 'repo' = @('windows-terminal-window:111') }
    ProcessWindowGroups = @{}
}
$savedGroupEntry = New-TestEntry codex saved-group terminal-saved startup 'windows-terminal-window:222'
$savedGroupResult = @(Set-CliSessionWindowGroups -Entries @($savedGroupEntry) -ProcessMap @{} -Discovery $truncatedDiscovery)
Assert-Equal 'windows-terminal-window:222' (Get-CliSessionWindowGroup $savedGroupResult[0]) 'A truncated probe must keep the saved window group instead of guessing from the tab title.'

$noGroupEntry = New-TestEntry codex no-group terminal-none startup
$noGroupResult = @(Set-CliSessionWindowGroups -Entries @($noGroupEntry) -ProcessMap @{} -Discovery $truncatedDiscovery)
Assert-Equal 'windows-terminal-window:111' (Get-CliSessionWindowGroup $noGroupResult[0]) 'An entry with no saved window group must still fall back to a unique tab title.'

$probeOrderMap = @{
    'codex:has-group' = [pscustomobject]@{ ProcessId = 700 }
    'codex:needs-group' = [pscustomobject]@{ ProcessId = 800 }
}
$probeOrderEntries = @(
    (New-TestEntry codex has-group terminal-a startup 'windows-terminal-window:333'),
    (New-TestEntry codex needs-group terminal-b startup)
)
$probeOrder = @(Get-CliSessionWindowProbeOrder $probeOrderMap $probeOrderEntries)
Assert-Equal 800 $probeOrder[0] 'Sessions with no known window must be probed before the deadline can expire.'
Assert-Equal 2 $probeOrder.Count 'Every live session must remain in the probe order.'
Assert-Equal 1 @(Get-CliSessionWindowProbeOrder @{ 'codex:unknown' = [pscustomobject]@{ ProcessId = 900 } } $null).Count 'Probe ordering must tolerate a registry with no matching entries.'
Assert-Equal 800 @(Get-CliSessionWindowProbeOrder $probeOrderMap $probeOrderEntries -UnknownOnly)[0] 'An unknown-only probe must target the session with no saved window.'
Assert-Equal 1 @(Get-CliSessionWindowProbeOrder $probeOrderMap $probeOrderEntries -UnknownOnly).Count 'An unknown-only probe must skip sessions whose window is already saved.'

$verifiedTabDiscovery = @{ TerminalResponding=$true; ProbeComplete=$true; ProcessWindowGroups=@{ '700'='windows-terminal-window:333' } }
$visibleProcessMap = Select-CliSessionProcessMapByWindowEvidence $probeOrderMap $verifiedTabDiscovery
Assert-Equal 1 $visibleProcessMap.Count 'A complete responsive Terminal probe must exclude a live CLI process whose tab is gone.'
Assert-Equal $true $visibleProcessMap.ContainsKey('codex:has-group') 'A complete responsive Terminal probe must retain the CLI writer with a visible tab.'
$partialTabDiscovery = @{ TerminalResponding=$true; ProbeComplete=$false; ProcessWindowGroups=@{ '700'='windows-terminal-window:333' } }
Assert-Equal 2 (Select-CliSessionProcessMapByWindowEvidence $probeOrderMap $partialTabDiscovery).Count 'An incomplete tab probe must not produce a partial recovery set.'
Assert-Equal $false (Test-CliSessionWindowProbeComplete @(700, 701) @(700, 701) @(701)) 'Attempting every process must not make a window probe complete when one process could not be verified.'
Assert-Equal $true (Test-CliSessionWindowProbeComplete @(700, 701) @(701, 700) @()) 'A window probe is complete only when every process was verified without a probe failure.'
$frozenTabDiscovery = @{ TerminalResponding=$false; ProbeComplete=$false; ProcessWindowGroups=@{} }
Assert-Equal 2 (Select-CliSessionProcessMapByWindowEvidence $probeOrderMap $frozenTabDiscovery).Count 'A frozen Terminal must fall back to verified live writer evidence.'

$knownOnlyStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$knownOnlyDiscovery = Get-CliSessionWindowDiscovery @{ 'codex:has-group' = [pscustomobject]@{ ProcessId = 700 } } @($probeOrderEntries[0])
$knownOnlyStopwatch.Stop()
Assert-Equal 0 $knownOnlyDiscovery.ProcessWindowGroups.Count 'A save must not probe Terminal when every live session already has a saved window.'
Assert-Equal 0 $knownOnlyDiscovery.TitleMap.Count 'A save must not walk Terminal tab titles when it has nothing to learn.'
Assert-Equal $true ($knownOnlyStopwatch.Elapsed.TotalSeconds -lt 2) 'A save with nothing to learn must skip Terminal automation entirely.'

$restoreScratch = Join-Path ([System.IO.Path]::GetTempPath()) "cli-session-restore-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $restoreScratch -Force | Out-Null
try {
    $claudeTranscriptRoot = Join-Path $restoreScratch '.claude\projects\project'
    New-Item -ItemType Directory -Path $claudeTranscriptRoot -Force | Out-Null
    $goodTranscript = Join-Path $claudeTranscriptRoot 'good.jsonl'
    Set-Content -LiteralPath $goodTranscript -Value '{}' -Encoding UTF8
    $goodEntry = New-TestEntry claude '20000000-0000-0000-0000-000000000001' terminal-good startup
    $goodEntry.cwd = $restoreScratch
    $goodEntry.transcriptPath = $goodTranscript
    $lostEntry = New-TestEntry claude '20000000-0000-0000-0000-000000000002' terminal-lost startup
    $lostEntry.cwd = $restoreScratch
    $lostEntry.transcriptPath = Join-Path $restoreScratch 'deleted-by-claude.jsonl'

    $split = Split-CliRecoverySet @($goodEntry, $lostEntry)
    Assert-Equal 1 $split.Restorable.Count 'A conversation whose transcript vanished must not block the rest of the recovery set.'
    Assert-Equal '20000000-0000-0000-0000-000000000001' $split.Restorable[0].id 'The healthy conversation must still restore.'
    Assert-Equal 1 $split.Unrestorable.Count 'A conversation whose transcript vanished must be reported as skipped.'
    Assert-Equal $true ($split.Unrestorable[0].Problem -like 'transcript no longer exists*') 'A skipped conversation must say why it cannot be resumed.'

    $codexTranscriptRoot = Join-Path $restoreScratch '.codex\sessions'
    New-Item -ItemType Directory -Path $codexTranscriptRoot -Force | Out-Null
    $restorableCodexTranscript = Join-Path $codexTranscriptRoot 'rollout-20000000-0000-0000-0000-000000000005.jsonl'
    $guardianCodexTranscript = Join-Path $codexTranscriptRoot 'rollout-20000000-0000-0000-0000-000000000006.jsonl'
    [System.IO.File]::WriteAllText($restorableCodexTranscript, '{"type":"session_meta","payload":{"source":"cli"}}', (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($guardianCodexTranscript, '{"type":"session_meta","payload":{"source":{"subagent":{"other":"guardian"}}}}', (New-Object System.Text.UTF8Encoding($false)))
    $restorableCodexEntry = New-TestEntry codex '20000000-0000-0000-0000-000000000005' terminal-codex startup
    $restorableCodexEntry.cwd = $restoreScratch
    $restorableCodexEntry.transcriptPath = $restorableCodexTranscript
    $guardianCodexEntry = New-TestEntry codex '20000000-0000-0000-0000-000000000006' terminal-guardian startup
    $guardianCodexEntry.cwd = $restoreScratch
    $guardianCodexEntry.transcriptPath = $guardianCodexTranscript
    $pollutedSplit = Split-CliRecoverySet @($restorableCodexEntry, $guardianCodexEntry)
    Assert-Equal 1 $pollutedSplit.Restorable.Count 'Restore must keep a top-level Codex conversation from a polluted historical recovery set.'
    Assert-Equal '20000000-0000-0000-0000-000000000005' $pollutedSplit.Restorable[0].id 'Restore must select only the top-level Codex conversation.'
    Assert-Equal 1 $pollutedSplit.Unrestorable.Count 'Restore must independently reject a saved Codex guardian session.'
    Assert-Equal $true ($pollutedSplit.Unrestorable[0].Problem -like 'transcript is not a top-level resumable codex conversation*') 'Restore must report a guardian transcript as non-resumable.'

    $claudeSubagentRoot = Join-Path $claudeTranscriptRoot 'session\subagents'
    New-Item -ItemType Directory -Path $claudeSubagentRoot -Force | Out-Null
    $claudeSubagentTranscript = Join-Path $claudeSubagentRoot 'agent-20000000-0000-0000-0000-000000000007.jsonl'
    [System.IO.File]::WriteAllText($claudeSubagentTranscript, '{}', (New-Object System.Text.UTF8Encoding($false)))
    $claudeSubagentEntry = New-TestEntry claude '20000000-0000-0000-0000-000000000007' terminal-claude-subagent startup
    $claudeSubagentEntry.cwd = $restoreScratch
    $claudeSubagentEntry.transcriptPath = $claudeSubagentTranscript
    Assert-Equal $true ((Get-CliSessionEntryProblem $claudeSubagentEntry) -like 'transcript is not a top-level resumable claude conversation*') 'Restore must independently reject a saved Claude subagent.'

    $noTranscriptEntry = New-TestEntry codex '20000000-0000-0000-0000-000000000003' terminal-none startup
    $noTranscriptEntry.cwd = $restoreScratch
    $noTranscriptEntry.transcriptPath = $null
    Assert-Equal $null (Get-CliSessionEntryProblem $noTranscriptEntry) 'An entry that never recorded a transcript path must stay restorable.'

    $goneCwdEntry = New-TestEntry codex '20000000-0000-0000-0000-000000000004' terminal-gone startup
    $goneCwdEntry.cwd = Join-Path $restoreScratch 'removed-repo'
    $goneCwdEntry.transcriptPath = $goodTranscript
    Assert-Equal $true ((Get-CliSessionEntryProblem $goneCwdEntry) -like 'working directory does not exist*') 'A deleted working directory must make one entry unrestorable.'

    Assert-Equal 0 (Split-CliRecoverySet @($lostEntry, $goneCwdEntry)).Restorable.Count 'A recovery set with nothing restorable must report zero restorable entries.'
} finally {
    Remove-Item -LiteralPath $restoreScratch -Recurse -Force -ErrorAction SilentlyContinue
}

$staleVault = Join-Path ([System.IO.Path]::GetTempPath()) "cli-session-stale-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $staleVault -Force | Out-Null
try {
    $staleFile = Join-Path $staleVault 'active.json.999.abc.tmp'
    Set-Content -LiteralPath $staleFile -Value '' -Encoding UTF8
    (Get-Item -LiteralPath $staleFile).LastWriteTime = (Get-Date).AddDays(-2)
    $freshFile = Join-Path $staleVault 'active.json.999.def.tmp'
    Set-Content -LiteralPath $freshFile -Value '' -Encoding UTF8
    Assert-Equal 1 (Remove-CliSessionStaleTemporaryFiles $staleVault) 'Only abandoned temporary files must be swept.'
    Assert-Equal $false (Test-Path -LiteralPath $staleFile) 'An abandoned temporary file must be removed.'
    Assert-Equal $true (Test-Path -LiteralPath $freshFile) 'An in-flight temporary file must survive the sweep.'
} finally {
    Remove-Item -LiteralPath $staleVault -Recurse -Force -ErrorAction SilentlyContinue
}

$installProfile = Join-Path ([System.IO.Path]::GetTempPath()) "cli-session-install-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path (Join-Path $installProfile '.codex') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $installProfile '.claude') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $installProfile 'Desktop') -Force | Out-Null
try {
    $testShortcutShell = New-Object -ComObject WScript.Shell
    $staleSaveShortcut = $testShortcutShell.CreateShortcut((Join-Path $installProfile 'Desktop\SAVE CLI SESSIONS.lnk'))
    $staleSaveShortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $staleSaveShortcut.Arguments = '-Command stale-inline-launcher'
    $staleSaveShortcut.Save()
    $recoveryHook = [pscustomobject]@{ type='command'; command='powershell.exe -File C:\Users\TommySeery\cli-session-hook.ps1 -Tool claude'; timeout=30 }
    $unrelatedHook = [pscustomobject]@{ type='command'; command='powershell.exe -File C:\Users\TommySeery\other-hook.ps1'; timeout=30 }
    $codexHooks = [pscustomobject]@{
        hooks = [pscustomobject]@{
            SessionStart = @([pscustomobject]@{ hooks=@($recoveryHook, $unrelatedHook) })
            UserPromptSubmit = @([pscustomobject]@{ hooks=@($recoveryHook) })
        }
        feature = 'preserved'
    }
    $claudeSettings = [pscustomobject]@{
        hooks = [pscustomobject]@{
            SessionStart = @([pscustomobject]@{ hooks=@($recoveryHook, $unrelatedHook) })
            SessionEnd = @([pscustomobject]@{ hooks=@($recoveryHook) })
        }
        effortLevel = 'high'
    }
    [System.IO.File]::WriteAllText((Join-Path $installProfile '.codex\hooks.json'), ($codexHooks | ConvertTo-Json -Depth 20), (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText((Join-Path $installProfile '.claude\settings.json'), ($claudeSettings | ConvertTo-Json -Depth 20), (New-Object System.Text.UTF8Encoding($false)))
    & (Join-Path $PSScriptRoot '..\install-cli-session-recovery.ps1') -UserProfilePath $installProfile | Out-Null
    $installedCodexHooks = Get-Content -LiteralPath (Join-Path $installProfile '.codex\hooks.json') -Raw | ConvertFrom-Json
    $installedCodexCommands = @($installedCodexHooks.hooks.PSObject.Properties.Value.hooks.command)
    Assert-Equal 0 @($installedCodexCommands | Where-Object { $_ -match '(?i)cli-session-hook\.ps1' }).Count 'Install must remove every Codex recovery lifecycle hook.'
    Assert-Equal 1 @($installedCodexCommands | Where-Object { $_ -match '(?i)other-hook\.ps1' }).Count 'Install must preserve unrelated Codex hooks.'
    Assert-Equal preserved $installedCodexHooks.feature 'Install must preserve unrelated Codex settings.'
    $installedClaudeSettings = Get-Content -LiteralPath (Join-Path $installProfile '.claude\settings.json') -Raw | ConvertFrom-Json
    $installedClaudeCommands = @($installedClaudeSettings.hooks.PSObject.Properties.Value.hooks.command)
    Assert-Equal 0 @($installedClaudeCommands | Where-Object { $_ -match '(?i)cli-session-hook\.ps1' }).Count 'Install must remove every Claude recovery lifecycle hook.'
    Assert-Equal 1 @($installedClaudeCommands | Where-Object { $_ -match '(?i)other-hook\.ps1' }).Count 'Install must preserve unrelated Claude hooks.'
    Assert-Equal high $installedClaudeSettings.effortLevel 'Install must preserve unrelated Claude settings.'
    $installedListener = Join-Path $installProfile 'cli-session-shutdown-listener.ps1'
    $installedAutoSaveConfigurator = Join-Path $installProfile 'configure-cli-session-autosave.ps1'
    $installedLauncher = Join-Path $installProfile 'save-sessions-hidden.vbs'
    $installedOpenFileProbe = Join-Path $installProfile 'probe-cli-open-files.ps1'
    $installedWindowProbe = Join-Path $installProfile 'probe-cli-window.ps1'
    Assert-Equal $true (Test-Path -LiteralPath $installedListener -PathType Leaf) 'Install must deploy the hookless transcript-creation autosave listener.'
    Assert-Equal $true (Test-Path -LiteralPath $installedAutoSaveConfigurator -PathType Leaf) 'Install must deploy the autosave scheduled-task repair utility.'
    Assert-Equal $true (Test-Path -LiteralPath $installedLauncher -PathType Leaf) 'Install must deploy the desktop Save launcher from source control.'
    Assert-Equal $true (Test-Path -LiteralPath $installedOpenFileProbe -PathType Leaf) 'Install must deploy the bounded open-file probe worker.'
    Assert-Equal $true (Test-Path -LiteralPath $installedWindowProbe -PathType Leaf) 'Install must deploy the bounded Terminal window probe worker.'
    $installedSaveShortcut = $testShortcutShell.CreateShortcut((Join-Path $installProfile 'Desktop\SAVE CLI SESSIONS.lnk'))
    Assert-Equal (Join-Path $env:SystemRoot 'System32\wscript.exe') $installedSaveShortcut.TargetPath 'Install must replace a stale inline Save shortcut with the supported VBS launcher.'
    Assert-Equal "`"$(Join-Path $installProfile 'save-sessions-hidden.vbs')`"" $installedSaveShortcut.Arguments 'The Save shortcut must target the installed launcher instead of a repository source path.'
    $installedRestoreShortcut = $testShortcutShell.CreateShortcut((Join-Path $installProfile 'Desktop\RESTORE CLI SESSIONS.lnk'))
    Assert-Equal (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') $installedRestoreShortcut.TargetPath 'Install must create the supported Restore shortcut.'
    $listenerText = [System.IO.File]::ReadAllText($installedListener)
    Assert-Equal $true ($listenerText -match "Register-ObjectEvent[\s\S]+-EventName Created") 'The autosave listener must react to new transcript creation.'
    Assert-Equal $false ($listenerText -match '(?i)cli-session-hook\.ps1') 'Conversation-start autosave must not restore lifecycle hooks.'
    Assert-Equal $true ($listenerText -match '\$processSetChanged\s*=\s*-not \[string\]::IsNullOrWhiteSpace\(\$lastProcessSignature\)') 'A restarted listener must immediately capture CLI processes that were already running.'
    Assert-Equal $true ($listenerText -match '\[int\]\$SafetySaveIntervalSeconds\s*=\s*300') 'The listener must periodically reconcile even when filesystem events are missed.'
    Assert-Equal $true ($listenerText -match 'Invoke-ListenerSave -AutoSave -VerifyWindowGroups:\$safetySaveDue') 'The periodic autosave must refresh exact Terminal window grouping before desktop Save pins it.'
    Assert-Equal $true ($listenerText -match 'AUTOSAVE_ERROR=[\s\S]+\$RetryDelaySeconds') 'A failed autosave must remain inside the listener and schedule a retry.'
    Assert-Equal $true ($listenerText -match 'WaitForExit\(120000\)[\s\S]+Stop-Process -Id \$saveProcess\.Id') 'The listener must stop only its own save child if autosave exceeds its hard deadline.'
    Assert-Equal $true ($listenerText -match '\$subscription -and \$subscription\.PSObject\.Properties') 'Listener cleanup must tolerate an unavailable event subscription without masking the original failure.'
    $launcherText = [System.IO.File]::ReadAllText($installedLauncher)
    Assert-Equal $true ($launcherText -match 'shell\.Exec\(command\)[\s\S]+Do While process\.Status = 0[\s\S]+latest completed automatic recovery set') 'Desktop Save must explain that it is pinning already-prepared state.'
    Assert-Equal $true ($launcherText -match 'DateDiff\("s", startedAt, Now\) >= 10[\s\S]+process\.Terminate') 'Desktop Save must stop only its own worker after a hard ten-second deadline.'
    Assert-Equal $false ($launcherText -match 'shell\.Run\(command, 0, True\)') 'Desktop Save must not disappear into an opaque synchronous hidden wait.'
    $autoSaveDefinition = & $installedAutoSaveConfigurator -UserProfilePath $installProfile -Preview
    Assert-Equal 'CLI Session AutoSave' $autoSaveDefinition.TaskName 'The installer must repair the stable autosave task name.'
    Assert-Equal 1 $autoSaveDefinition.RepetitionInterval.TotalMinutes 'The task must act as a one-minute watchdog if the long-running listener exits.'
    Assert-Equal 999 $autoSaveDefinition.RestartCount 'The task must retry listener failures instead of waiting for the next logon.'
    Assert-Equal 'IgnoreNew' $autoSaveDefinition.MultipleInstances 'Watchdog triggers must never create duplicate listener processes.'
    Assert-Equal $true $autoSaveDefinition.Enabled 'A normal installation must enable automatic recovery.'
    Assert-Equal $true ($autoSaveDefinition.Arguments -like "*$installedListener*") 'The autosave task must launch the listener deployed into the selected profile.'
    $saveText = [System.IO.File]::ReadAllText((Join-Path $installProfile 'save-sessions.ps1'))
    Assert-Equal $true ($saveText -match 'elseif \(\$AutoSave\) \{ Join-Path \$Vault ''autosave\.json'' \}') 'Automatic saves must write their own prepared recovery file.'
    Assert-Equal $false ($saveText -match '\$Pin -or \$AutoSave') 'Automatic saves must never overwrite the authoritative manual pin.'
    Assert-Equal $true ($saveText -match 'elseif \(\$AutoSave\) \{ ''autosave'' \}') 'Automatic snapshots must be distinguishable from manual desktop saves.'
    Assert-Equal $true ($saveText -match 'if \(\$Pin\) \{[\s\S]+Invoke-CliSessionPin[\s\S]+exit 0[\s\S]+Invoke-WithCliSessionSaveLock') 'Desktop Save must finish before the discovery and save-mutex path is reached.'
    Assert-Equal $true ($saveText -match "matching live transcript writers[\s\S]+resolving live conversation metadata[\s\S]+discovering Terminal window groups[\s\S]+confirming live transcript writers[\s\S]+committing the verified recovery set") 'Save status must identify the exact active discovery stage instead of appearing silently hung.'
    $windowProbeText = [System.IO.File]::ReadAllText($installedWindowProbe)
    Assert-Equal $true ($windowProbeText -match 'Get-WindowsTerminalTitleWindowMap') 'Terminal title UI Automation must run inside the bounded window-probe worker.'
    $moduleText = [System.IO.File]::ReadAllText((Join-Path $installProfile 'cli-session-vault.psm1'))
    $windowDiscoveryText = [regex]::Match($moduleText, 'function Get-CliSessionWindowDiscovery[\s\S]+?(?=function Select-CliSessionProcessMapByWindowEvidence)').Value
    Assert-Equal $false ($windowDiscoveryText -match 'Get-WindowsTerminalTitleWindowMap') 'The save process must never run Terminal title UI Automation outside the bounded worker.'
    & (Join-Path $PSScriptRoot '..\install-cli-session-recovery.ps1') -UserProfilePath $installProfile | Out-Null
    $reinstalledClaudeSettings = Get-Content -LiteralPath (Join-Path $installProfile '.claude\settings.json') -Raw | ConvertFrom-Json
    $reinstalledClaudeCommands = @($reinstalledClaudeSettings.hooks.PSObject.Properties.Value.hooks.command)
    Assert-Equal 0 @($reinstalledClaudeCommands | Where-Object { $_ -match '(?i)cli-session-hook\.ps1' }).Count 'Repeated installs must keep Claude recovery hooks absent.'
    Assert-Equal 1 @($reinstalledClaudeCommands | Where-Object { $_ -match '(?i)other-hook\.ps1' }).Count 'Repeated installs must continue preserving unrelated Claude hooks.'
} finally {
    Remove-Item -LiteralPath $installProfile -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Output 'PASS cli-session-vault.tests.ps1'
