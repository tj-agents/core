[CmdletBinding()]
param(
    [string]$Vault = "$env:USERPROFILE\.cli-session-vault",
    [switch]$Quiet,
    [switch]$Pin,
    [switch]$AutoSave,
    [switch]$Shutdown,
    [switch]$DryRun,
    [switch]$VerifyWindowGroups,
    [string]$SaveMutexName = 'Local\CliSessionSaveV3'
)

$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot 'cli-session-vault.psm1'
$statusPath = Join-Path $Vault 'last-save.txt'

function Set-CliSessionSaveStage([string]$Stage) {
    if ($script:DryRun) { return }
    New-Item -ItemType Directory -Path $Vault -Force | Out-Null
    [System.IO.File]::WriteAllText($statusPath, "Saving CLI sessions: $Stage at $(Get-Date -Format HH:mm:ss). The previous recovery set remains safe.", (New-Object System.Text.UTF8Encoding($false)))
}

function Get-CliSessionSnapshotTime($Snapshot) {
    try { return [datetimeoffset]$Snapshot.generatedAt } catch { return [datetimeoffset]::MinValue }
}

function Invoke-CliSessionPin {
    param([string]$Vault, [switch]$DryRun)

    $pinnedPath = Join-Path $Vault 'pinned.json'
    $preparedCandidates = @(
        [pscustomobject]@{ Path=(Join-Path $Vault 'autosave.json'); Priority=50 },
        [pscustomobject]@{ Path=(Join-Path $Vault 'active.json'); Priority=40 },
        [pscustomobject]@{ Path=(Join-Path $Vault 'observed.json'); Priority=30 },
        [pscustomobject]@{ Path=(Join-Path $Vault 'shutdown.json'); Priority=20 },
        [pscustomobject]@{ Path=(Join-Path $Vault 'last-open.json'); Priority=10 },
        [pscustomobject]@{ Path=$pinnedPath; Priority=5 }
    ) | ForEach-Object {
        [pscustomobject]@{ Path=$_.Path; Priority=$_.Priority; Data=(Read-CliSessionJson $_.Path) }
    }
    $source = Select-NewestCliRecoverySource $preparedCandidates
    $existingPin = Read-CliSessionJson $pinnedPath
    $keepExisting = $existingPin -and $existingPin.complete -and
        $existingPin.mode -eq 'manual' -and
        -not $existingPin.PSObject.Properties['consumedAt'] -and
        @($existingPin.sessions).Count -gt 0 -and
        (Get-CliSessionSnapshotTime $existingPin) -ge (Get-CliSessionSnapshotTime $source.Data)
    $snapshot = if ($keepExisting) {
        $existingPin
    } else {
        $value = New-CliSessionSnapshot 'manual' @($source.Data.sessions) -UnsavedSessions @(Get-CliSnapshotUnsavedSessions $source.Data)
        $value['sourceGeneratedAt'] = $source.Data.generatedAt
        $value['sourceMode'] = $source.Data.mode
        $value['sourcePath'] = $source.Path
        $value
    }
    $snapshotDirectory = Join-Path $Vault 'snapshots-v3'
    $snapshotPath = Join-Path $snapshotDirectory ("{0}-manual.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
    if (-not $DryRun -and -not $keepExisting) {
        Write-CliSessionJson $snapshotPath $snapshot
        Write-CliSessionJson $pinnedPath $snapshot
    }
    $sessions = @($snapshot.sessions)
    [pscustomobject]@{
        Count = $sessions.Count
        Closed = 0
        Windows = @($sessions | ForEach-Object { Get-CliSessionWindowGroup $_ } | Sort-Object -Unique).Count
        Mode = 'manual'
        Path = $pinnedPath
        Locked = $true
        RecoveredKeys = @()
        MissingKeys = @(Get-CliSnapshotUnsavedSessions $snapshot)
        SourceGeneratedAt = if ($keepExisting) { $existingPin.generatedAt } else { $source.Data.generatedAt }
        KeptExisting = [bool]$keepExisting
    }
}

function Invoke-CliSessionSave {
    param([string]$Vault, [switch]$AutoSave, [switch]$Shutdown, [switch]$DryRun, [switch]$VerifyWindowGroups)

    $activePath = Join-Path $Vault 'active.json'
    $closedPath = Join-Path $Vault 'closed.json'
    $active = Read-CliSessionJson $activePath
    $closedData = Read-CliSessionJson $closedPath
    $registeredSessions = if ($active -and $active.complete) { @($active.sessions) } else { @() }
    $recoverySets = @($active)
    foreach ($name in @('pinned.json', 'autosave.json', 'shutdown.json', 'observed.json', 'last-open.json')) {
        $candidate = Read-CliSessionJson (Join-Path $Vault $name)
        if ($candidate -and $candidate.complete) { $recoverySets += $candidate }
    }

    Set-CliSessionSaveStage 'reading the first process inventory'
    $processes = @(Get-CimInstance Win32_Process)
    Set-CliSessionSaveStage 'matching live transcript writers'
    $processMap = Get-OpenCliSessionProcessMap (Get-LiveCliSessionProcessMap $active $processes) $closedData
    Set-CliSessionSaveStage 'resolving live conversation metadata'
    $resolution = Resolve-LiveCliSessionEntries $recoverySets $processMap
    $sessions = @($resolution.Entries)
    $verifyCurrentWindowGroups = $VerifyWindowGroups -or $Shutdown
    Set-CliSessionSaveStage 'discovering Terminal window groups'
    $discovery = Get-CliSessionWindowDiscovery $processMap $sessions -VerifyKnownWindowGroups:$verifyCurrentWindowGroups
    if ($verifyCurrentWindowGroups) {
        $processMap = Select-CliSessionProcessMapByWindowEvidence $processMap $discovery
        $resolution = Resolve-LiveCliSessionEntries $recoverySets $processMap
        $sessions = @($resolution.Entries)
    }
    $sessions = @(Set-CliSessionWindowGroups -Entries $sessions -ProcessMap $processMap -Discovery $discovery)

    Set-CliSessionSaveStage 'reading the final process inventory'
    $currentProcesses = @(Get-CimInstance Win32_Process)
    Set-CliSessionSaveStage 'confirming live transcript writers'
    $currentProcessMap = Get-OpenCliSessionProcessMap (Get-LiveCliSessionProcessMap $active $currentProcesses) $closedData
    if ((@($processMap.Keys | Sort-Object) -join '|') -ne (@($currentProcessMap.Keys | Sort-Object) -join '|')) {
        if ($verifyCurrentWindowGroups) {
            $currentResolution = Resolve-LiveCliSessionEntries $recoverySets $currentProcessMap
            $currentDiscovery = Get-CliSessionWindowDiscovery $currentProcessMap @($currentResolution.Entries) -VerifyKnownWindowGroups
            $currentProcessMap = Select-CliSessionProcessMapByWindowEvidence $currentProcessMap $currentDiscovery
            $discovery = $currentDiscovery
        }
        $processes = $currentProcesses
        $processMap = $currentProcessMap
        $resolution = Resolve-LiveCliSessionEntries $recoverySets $processMap
        $sessions = @($resolution.Entries)
        $sessions = @(Set-CliSessionWindowGroups -Entries $sessions -ProcessMap $processMap -Discovery $discovery)
    }
    if ($sessions.Count -eq 0) {
        throw 'No live registered CLI sessions are open. The previous recovery set was preserved.'
    }

    $mode = if ($Shutdown) { 'shutdown' } elseif ($AutoSave) { 'autosave' } else { 'observed' }
    $destination = if ($Shutdown) { Join-Path $Vault 'shutdown.json' } elseif ($AutoSave) { Join-Path $Vault 'autosave.json' } else { Join-Path $Vault 'observed.json' }
    $snapshotDirectory = Join-Path $Vault 'snapshots-v3'

    Set-CliSessionSaveStage 'committing the verified recovery set'
    return Invoke-WithCliSessionLock -TimeoutMilliseconds 30000 -ProceedWithoutLock {
        $latestActive = Read-CliSessionJson $activePath
        $latestClosedData = Read-CliSessionJson $closedPath
        $processMap = Get-OpenCliSessionProcessMap (Get-LiveCliSessionProcessMap $latestActive $processes) $latestClosedData
        if ($verifyCurrentWindowGroups) {
            $processMap = Select-CliSessionProcessMapByWindowEvidence $processMap $discovery
        }
        $latestRecoverySets = @($latestActive) + @($recoverySets | Select-Object -Skip 1)
        $resolution = Resolve-LiveCliSessionEntries $latestRecoverySets $processMap
        $sessions = @($resolution.Entries)
        $sessions = @(Set-CliSessionWindowGroups -Entries $sessions -ProcessMap $processMap -Discovery $discovery)
        if ($sessions.Count -eq 0) {
            throw 'No live registered CLI sessions are open. The previous recovery set was preserved.'
        }

        $snapshot = New-CliSessionSnapshot $mode $sessions -UnsavedSessions $resolution.MissingKeys
        $snapshotPath = Join-Path $snapshotDirectory ("{0}-{1}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), $mode)
        if (-not $DryRun) {
            Write-CliSessionJson $activePath (New-CliSessionSnapshot 'active' $sessions -UnsavedSessions $resolution.MissingKeys)
            Write-CliSessionJson $destination $snapshot
            Write-CliSessionJson $snapshotPath $snapshot
        }
        $closedCount = @($registeredSessions | Where-Object { -not $processMap.ContainsKey("$($_.tool):$($_.id.ToLowerInvariant())") }).Count
        $windowCount = @($sessions | ForEach-Object { Get-CliSessionWindowGroup $_ } | Sort-Object -Unique).Count
        [pscustomobject]@{
            Count = $sessions.Count
            Closed = $closedCount
            Windows = $windowCount
            Mode = $mode
            Path = $snapshotPath
            Locked = Get-CliSessionLastLockAcquired
            RecoveredKeys = @($resolution.RecoveredKeys)
            MissingKeys = @($resolution.MissingKeys)
        }
    }
}

try {
    Import-Module $modulePath -Force
    if ($Pin) {
        $result = Invoke-CliSessionPin -Vault $Vault -DryRun:$DryRun
        $prefix = if ($DryRun) { 'Would pin' } elseif ($result.KeptExisting) { 'Already protected' } else { 'Pinned' }
        $message = "$prefix $($result.Count) exact Claude/Codex CLI session(s) across $($result.Windows) Terminal window(s) from the latest completed automatic snapshot."
        if ($result.MissingKeys.Count -gt 0) { $message += "`r`nWarning: the source snapshot had $($result.MissingKeys.Count) uncaptured live session(s):`r`n$($result.MissingKeys -join "`r`n")" }
        $message += "`r`nPrepared at $($result.SourceGeneratedAt).`r`n$($result.Path)"
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $Vault -Force | Out-Null
            [System.IO.File]::WriteAllText($statusPath, $message, (New-Object System.Text.UTF8Encoding($false)))
        }
        if (-not $Quiet) { Write-Host $message -ForegroundColor Green }
        exit 0
    }

    Remove-CliSessionStaleTemporaryFiles $Vault | Out-Null
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $Vault -Force | Out-Null
        [System.IO.File]::WriteAllText($statusPath, 'Saving CLI sessions: discovering exact live conversations. This will finish or fail safely within 120 seconds.', (New-Object System.Text.UTF8Encoding($false)))
    }

    $attemptErrors = New-Object System.Collections.ArrayList
    $result = Invoke-WithCliSessionSaveLock -TimeoutMilliseconds 0 -MutexName $SaveMutexName {
        foreach ($attempt in 1..2) {
            try {
                Invoke-CliSessionSave -Vault $Vault -AutoSave:$AutoSave -Shutdown:$Shutdown -DryRun:$DryRun -VerifyWindowGroups:$VerifyWindowGroups
                break
            } catch {
                [void]$attemptErrors.Add($_.Exception.Message)
                if ($attempt -eq 2) { throw }
                Start-Sleep -Seconds 2
            }
        }
    }

    $prefix = if ($DryRun) { 'Would protect' } else { 'Protected' }
    $message = "$prefix $($result.Count) exact Claude/Codex CLI session(s) across $($result.Windows) Terminal window(s); excluded $($result.Closed) closed session(s)."
    if ($result.RecoveredKeys.Count -gt 0) { $message += "`r`nRecovered $($result.RecoveredKeys.Count) live session(s) from previous recovery data after their active registry entries were lost." }
    if ($result.MissingKeys.Count -gt 0) { $message += "`r`nWarning: could not save $($result.MissingKeys.Count) live session(s) because their recovery metadata was unavailable:`r`n$($result.MissingKeys -join "`r`n")" }
    if (-not $result.Locked) { $message += "`r`nWarning: the registry lock was busy; the save was written without it." }
    if ($attemptErrors.Count -gt 0) { $message += "`r`nRecovered after a failed attempt: $($attemptErrors -join ' | ')" }
    $message += "`r`n$($result.Path)"
    if (-not $DryRun) { [System.IO.File]::WriteAllText($statusPath, $message, (New-Object System.Text.UTF8Encoding($false))) }
    if (-not $Quiet) { Write-Host $message -ForegroundColor Green }
    exit 0
} catch {
    $message = "Session save failed at $(Get-Date -Format 'HH:mm:ss'): $($_.Exception.Message)"
    New-Item -ItemType Directory -Path $Vault -Force | Out-Null
    [System.IO.File]::WriteAllText($statusPath, $message, (New-Object System.Text.UTF8Encoding($false)))
    if (-not $Quiet) { Write-Error $message }
    exit 1
}
