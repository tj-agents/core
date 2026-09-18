[CmdletBinding()]
param(
    [int]$SafetySaveIntervalSeconds = 300,
    [int]$RetryDelaySeconds = 15
)

$ErrorActionPreference = 'Stop'
$vault = Join-Path $env:USERPROFILE '.cli-session-vault'
$statusPath = Join-Path $vault 'shutdown-listener-status.txt'
$saveScript = Join-Path $env:USERPROFILE 'save-sessions.ps1'
$modulePath = Join-Path $env:USERPROFILE 'cli-session-vault.psm1'
New-Item -ItemType Directory -Path $vault -Force | Out-Null
Import-Module $modulePath -Force

trap {
    [System.IO.File]::WriteAllText($statusPath, "ERROR $($_.Exception.Message) $(Get-Date -Format o)")
    exit 1
}

function Get-TopLevelCliProcessSignature {
    $processes = @(Get-CimInstance Win32_Process)
    $processIndex = New-CliProcessIndex $processes
    $identities = foreach ($process in $processes) {
        if (-not (Get-CliProcessTool $process) -or -not (Test-CliProcessHasTerminalAncestor $process $processIndex)) { continue }
        $parent = if ($processIndex.ContainsKey([int]$process.ParentProcessId)) { $processIndex[[int]$process.ParentProcessId] } else { $null }
        if ($parent -and (Get-CliProcessTool $parent)) { continue }
        "$($process.ProcessId):$(([datetime]$process.CreationDate).ToUniversalTime().Ticks)"
    }
    return @($identities | Sort-Object) -join '|'
}

function Invoke-ListenerSave([switch]$AutoSave, [switch]$Shutdown, [switch]$VerifyWindowGroups) {
    $arguments = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $saveScript, '-Quiet')
    if ($AutoSave) { $arguments += '-AutoSave' }
    if ($Shutdown) { $arguments += '-Shutdown' }
    if ($VerifyWindowGroups) { $arguments += '-VerifyWindowGroups' }
    $saveProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -WindowStyle Hidden -PassThru
    try {
        if (-not $saveProcess.WaitForExit(120000)) {
            Stop-Process -Id $saveProcess.Id -Force -ErrorAction SilentlyContinue
            $saveProcess.WaitForExit(5000) | Out-Null
            throw 'CLI session save exceeded 120 seconds and was stopped. The previous recovery set was preserved.'
        }
        if ($saveProcess.ExitCode -ne 0) { throw "CLI session save exited with code $($saveProcess.ExitCode)." }
    } finally {
        $saveProcess.Dispose()
    }
}

$subscriptions = New-Object System.Collections.ArrayList
$watchers = New-Object System.Collections.ArrayList
$sessionEndingError = $null
try {
    $sessionEndingSubscription = Register-ObjectEvent -InputObject ([Microsoft.Win32.SystemEvents]) -EventName SessionEnding -SourceIdentifier 'CliSessionEnding'
    if ($sessionEndingSubscription) { $subscriptions.Add($sessionEndingSubscription) | Out-Null }
} catch {
    $sessionEndingError = $_.Exception.Message
}
$roots = @(
    (Join-Path $env:USERPROFILE '.codex\sessions'),
    (Join-Path $env:USERPROFILE '.claude\projects')
)
$watcherIndex = 0
foreach ($root in $roots) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
    $watcher = New-Object System.IO.FileSystemWatcher $root, '*.jsonl'
    $watcher.IncludeSubdirectories = $true
    $watcher.NotifyFilter = [System.IO.NotifyFilters]::FileName
    $watcher.EnableRaisingEvents = $true
    $watchers.Add($watcher) | Out-Null
    $createdSubscription = Register-ObjectEvent -InputObject $watcher -EventName Created -SourceIdentifier "CliTranscriptCreated$watcherIndex"
    if ($createdSubscription) { $subscriptions.Add($createdSubscription) | Out-Null }
    $errorSubscription = Register-ObjectEvent -InputObject $watcher -EventName Error -SourceIdentifier "CliTranscriptWatcherError$watcherIndex"
    if ($errorSubscription) { $subscriptions.Add($errorSubscription) | Out-Null }
    $watcherIndex++
}
$initialStatus = "ACTIVE PID=$PID WATCHERS=$watcherIndex $(Get-Date -Format o)"
if ($sessionEndingError) { $initialStatus += " SESSION_ENDING_ERROR=$sessionEndingError" }
[System.IO.File]::WriteAllText($statusPath, $initialStatus)

$pendingPaths = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
$lastProcessSignature = Get-TopLevelCliProcessSignature
$processSetChanged = -not [string]::IsNullOrWhiteSpace($lastProcessSignature)
$autoSaveDue = if ($processSetChanged) { (Get-Date).AddSeconds(2) } else { $null }
$nextProcessPoll = (Get-Date).AddSeconds(15)
$nextSafetySave = (Get-Date).AddSeconds($SafetySaveIntervalSeconds)
try {
    while ($true) {
        $event = Wait-Event -Timeout 1
        if ($event) {
            Remove-Event -EventIdentifier $event.EventIdentifier -ErrorAction SilentlyContinue
            if ($event.SourceIdentifier -eq 'CliSessionEnding') {
                try {
                    Invoke-ListenerSave -Shutdown
                    [System.IO.File]::WriteAllText($statusPath, "ACTIVE PID=$PID WATCHERS=$watcherIndex SHUTDOWN_SAVED=$(Get-Date -Format o)")
                } catch {
                    [System.IO.File]::WriteAllText($statusPath, "ACTIVE PID=$PID WATCHERS=$watcherIndex SHUTDOWN_SAVE_ERROR=$($_.Exception.Message) $(Get-Date -Format o)")
                }
                $autoSaveDue = $null
            } elseif ($event.SourceIdentifier -like 'CliTranscriptWatcherError*') {
                $processSetChanged = $true
                $autoSaveDue = (Get-Date).AddSeconds(2)
            } else {
                [void]$pendingPaths.Add([string]$event.SourceEventArgs.FullPath)
                $autoSaveDue = (Get-Date).AddSeconds(2)
            }
        }
        if ((Get-Date) -ge $nextProcessPoll) {
            try {
                $processSignature = Get-TopLevelCliProcessSignature
                if ($processSignature -ne $lastProcessSignature) {
                    $lastProcessSignature = $processSignature
                    $processSetChanged = $true
                    $autoSaveDue = (Get-Date).AddSeconds(2)
                }
            } catch {
                [System.IO.File]::WriteAllText($statusPath, "ACTIVE PID=$PID WATCHERS=$watcherIndex POLL_ERROR=$($_.Exception.Message) $(Get-Date -Format o)")
            }
            $nextProcessPoll = (Get-Date).AddSeconds(15)
        }
        $safetySaveDue = (Get-Date) -ge $nextSafetySave
        if (($autoSaveDue -and (Get-Date) -ge $autoSaveDue) -or $safetySaveDue) {
            $shouldSave = $processSetChanged -or $safetySaveDue
            $retryPaths = @()
            foreach ($path in @($pendingPaths)) {
                if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
                $tool = if ($path -match '(?i)[\\/]\.codex[\\/]sessions[\\/]') { 'codex' } elseif ($path -match '(?i)[\\/]\.claude[\\/]projects[\\/]') { 'claude' } else { $null }
                if (-not $tool -or -not (Get-CliTranscriptId $path)) { continue }
                try {
                    if ($tool -eq 'claude') {
                        $hasCwd = $false
                        foreach ($line in @(Get-Content -LiteralPath $path -TotalCount 12 -ErrorAction Stop)) {
                            try { $record = $line | ConvertFrom-Json } catch { continue }
                            $payload = if ($record.PSObject.Properties['payload']) { $record.payload } else { $record }
                            if ($payload.PSObject.Properties['cwd'] -and -not [string]::IsNullOrWhiteSpace([string]$payload.cwd)) { $hasCwd = $true; break }
                        }
                        if (-not $hasCwd) { throw "Claude transcript is not ready: $path" }
                    }
                    if (Test-CliTranscriptIsResumable $tool $path) { $shouldSave = $true }
                } catch {
                    $retryPaths += $path
                }
            }
            $pendingPaths.Clear()
            foreach ($path in $retryPaths) { [void]$pendingPaths.Add($path) }
            if ($shouldSave) {
                try {
                    Invoke-ListenerSave -AutoSave -VerifyWindowGroups:$safetySaveDue
                    [System.IO.File]::WriteAllText($statusPath, "ACTIVE PID=$PID WATCHERS=$watcherIndex AUTOSAVED=$(Get-Date -Format o)")
                    $processSetChanged = $false
                } catch {
                    [System.IO.File]::WriteAllText($statusPath, "ACTIVE PID=$PID WATCHERS=$watcherIndex AUTOSAVE_ERROR=$($_.Exception.Message) $(Get-Date -Format o)")
                    $processSetChanged = -not [string]::IsNullOrWhiteSpace($lastProcessSignature)
                    $autoSaveDue = if ($processSetChanged) { (Get-Date).AddSeconds($RetryDelaySeconds) } else { $null }
                }
            }
            $nextSafetySave = (Get-Date).AddSeconds($SafetySaveIntervalSeconds)
            if (-not $processSetChanged) {
                $autoSaveDue = if ($pendingPaths.Count -gt 0) { (Get-Date).AddSeconds(2) } else { $null }
            }
        }
    }
} finally {
    foreach ($subscription in $subscriptions) {
        if ($subscription -and $subscription.PSObject.Properties['Id'] -and $subscription.Id) {
            Unregister-Event -SubscriptionId $subscription.Id -ErrorAction SilentlyContinue
        }
    }
    foreach ($watcher in $watchers) { $watcher.Dispose() }
}
