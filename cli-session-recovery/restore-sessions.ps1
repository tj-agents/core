[CmdletBinding()]
param(
    [string]$In,
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$vault = Join-Path $env:USERPROFILE '.cli-session-vault'
$modulePath = Join-Path $PSScriptRoot 'cli-session-vault.psm1'
$statusPath = Join-Path $vault 'last-restore.txt'

function Show-Result([string]$Message, [bool]$Failed = $false) {
    [System.IO.File]::WriteAllText($statusPath, $Message, (New-Object System.Text.UTF8Encoding($false)))
    if (-not $DryRun -and -not $Quiet) {
        $icon = if ($Failed) { 16 } else { 64 }
        (New-Object -ComObject WScript.Shell).Popup($Message, 0, 'CLI Session Restore', $icon) | Out-Null
    }
}

function Get-CliProcessInventory($RecoveryData) {
    $processes = @(Get-CimInstance Win32_Process)
    [pscustomobject]@{
        Live = Get-LiveCliSessionKeys $RecoveryData $processes
        Orphaned = @(Get-OrphanedCliProcesses $processes)
    }
}

function Get-RecoverySource {
    if (-not [string]::IsNullOrWhiteSpace($In)) {
        $explicit = Read-CliSessionJson $In
        if (-not $explicit) { throw "Recovery snapshot cannot be read: $In" }
        return [pscustomobject]@{ Path=$In; Data=$explicit; Priority=100 }
    }

    $paths = @(
        [pscustomobject]@{ Path=(Join-Path $vault 'pinned.json'); Priority=90 },
        [pscustomobject]@{ Path=(Join-Path $vault 'autosave.json'); Priority=85 },
        [pscustomobject]@{ Path=(Join-Path $vault 'active.json'); Priority=80 },
        [pscustomobject]@{ Path=(Join-Path $vault 'shutdown.json'); Priority=70 },
        [pscustomobject]@{ Path=(Join-Path $vault 'last-open.json'); Priority=60 }
    )
    $candidates = @($paths | ForEach-Object {
        [pscustomobject]@{ Path=$_.Path; Priority=$_.Priority; Data=(Read-CliSessionJson $_.Path) }
    })
    return Select-NewestCliRecoverySource $candidates
}

function Start-SavedSession($Entry) {
    $launcher = Join-Path $PSScriptRoot 'start-saved-cli.ps1'
    $arguments = Get-CliRestoreLaunchArguments $Entry $launcher
    & wt.exe @arguments | Out-Null
}

try {
    Import-Module $modulePath -Force
    $source = Get-RecoverySource
    $recordedEntries = @(Get-CliSessionsByRecency $source.Data.sessions)
    $closedKeys = Get-CliClosedSessionKeys (Read-CliSessionJson (Join-Path $vault 'closed.json'))
    $closedEntries = @($recordedEntries | Where-Object { $closedKeys.ContainsKey("$($_.tool):$($_.id.ToLowerInvariant())") })
    $closedReport = @($closedEntries | ForEach-Object { "$($_.tool):$($_.id)" }) -join "`r`n"
    $allEntries = @($recordedEntries | Where-Object { -not $closedKeys.ContainsKey("$($_.tool):$($_.id.ToLowerInvariant())") })
    $split = Split-CliRecoverySet $allEntries
    $entries = @($split.Restorable)
    $skipped = @($split.Unrestorable)
    $unsaved = @(Get-CliSnapshotUnsavedSessions $source.Data)
    $unsavedReport = $unsaved -join "`r`n"
    $skippedReport = @($skipped | ForEach-Object { "$($_.Entry.tool):$($_.Entry.id) - $($_.Problem)" }) -join "`r`n"
    if ($entries.Count -eq 0) {
        throw "No saved conversation can be restored:`r`n$skippedReport"
    }

    $inventory = Get-CliProcessInventory $source.Data
    $live = $inventory.Live
    $missing = @($entries | Where-Object { -not $live.ContainsKey("$($_.tool):$($_.id.ToLowerInvariant())") })
    if ($DryRun) {
        $missingKeys = @{}
        foreach ($entry in $missing) { $missingKeys["$($entry.tool):$($entry.id)"] = $true }
        $entries | ForEach-Object {
            [pscustomobject]@{ Status=if($missingKeys.ContainsKey("$($_.tool):$($_.id)")){'MISSING'}else{'RUNNING'}; Window=(Get-CliRestoreWindowTarget $_); Tool=$_.tool; Title=$_.title; Id=$_.id; Cwd=$_.cwd }
        } | Format-Table -AutoSize
        "Recovery source: $($source.Path)"
        $windowCount = @($entries | ForEach-Object { Get-CliRestoreWindowTarget $_ } | Sort-Object -Unique).Count
        "Saved: $($recordedEntries.Count)  Restorable: $($entries.Count)  Windows: $windowCount  Running: $($entries.Count - $missing.Count)  Missing: $($missing.Count)  Detached: $(@($inventory.Orphaned).Count)  Closed: $($closedEntries.Count)  Skipped: $($skipped.Count)  UnsavedAtCapture: $($unsaved.Count)"
        if ($closedEntries.Count -gt 0) { "Not restored because they were closed:"; $closedReport }
        if ($skipped.Count -gt 0) { "Skipped (cannot be resumed):"; $skippedReport }
        if ($unsaved.Count -gt 0) { "Not captured by the original save:"; $unsavedReport }
        return
    }

    foreach ($entry in $missing) {
        Start-SavedSession $entry
        Start-Sleep -Milliseconds 750
    }

    $deadline = (Get-Date).AddSeconds(45)
    do {
        Start-Sleep -Seconds 1
        $live = (Get-CliProcessInventory $source.Data).Live
        $remaining = @($entries | Where-Object { -not $live.ContainsKey("$($_.tool):$($_.id.ToLowerInvariant())") })
    } while ($remaining.Count -gt 0 -and (Get-Date) -lt $deadline)

    if ($remaining.Count -gt 0) {
        $failedIds = @($remaining | ForEach-Object { "$($_.tool):$($_.id)" }) -join "`r`n"
        throw "These sessions did not start:`r`n$failedIds"
    }

    $consumed = $source.Data
    $consumed | Add-Member -NotePropertyName consumedAt -NotePropertyValue (Get-Date).ToString('o') -Force
    Write-CliSessionJson $source.Path $consumed
    $windowCount = @($entries | ForEach-Object { Get-CliRestoreWindowTarget $_ } | Sort-Object -Unique).Count
    $message = if ($missing.Count -eq 0) { "All $($entries.Count) recorded CLI sessions across $windowCount window(s) are already running." } else { "Restored all $($missing.Count) missing CLI session(s). All $($entries.Count) recorded sessions across $windowCount window(s) are running." }
    if ($closedEntries.Count -gt 0) { $message += "`r`nDid not restore $($closedEntries.Count) conversation(s) that were closed:`r`n$closedReport" }
    if ($skipped.Count -gt 0) { $message += "`r`nSkipped $($skipped.Count) conversation(s) that can no longer be resumed:`r`n$skippedReport" }
    if ($unsaved.Count -gt 0) { $message += "`r`nWarning: the original save could not capture $($unsaved.Count) live conversation(s):`r`n$unsavedReport" }
    Show-Result "$message`r`nSource: $($source.Path)"
} catch {
    $message = "CLI session restore failed: $($_.Exception.Message)"
    Show-Result $message $true
    throw
}
