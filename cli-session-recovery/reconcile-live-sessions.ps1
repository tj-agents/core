[CmdletBinding()]
param(
    [string]$Vault = "$env:USERPROFILE\.cli-session-vault",
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$modulePath = Join-Path $PSScriptRoot 'cli-session-vault.psm1'
Import-Module $modulePath -Force

function Get-Transcript([string]$Tool, [string]$Id) {
    $root = if ($Tool -eq 'claude') { Join-Path $env:USERPROFILE '.claude\projects' } else { Join-Path $env:USERPROFILE '.codex\sessions' }
    return Get-ChildItem -LiteralPath $root -Recurse -File -Filter "*$Id*.jsonl" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

function Get-TranscriptCwd([string]$Path) {
    $match = Select-String -LiteralPath $Path -Pattern '"cwd":"[^"]+"' | Select-Object -First 1
    if (-not $match) { return $null }
    $data = $match.Line | ConvertFrom-Json
    if ($data.cwd) { return [string]$data.cwd }
    if ($data.payload -and $data.payload.cwd) { return [string]$data.payload.cwd }
    return $null
}

function New-ReconciledEntry([string]$Key, $Processes) {
    $parts = $Key.Split(':', 2)
    $tool = $parts[0]
    $id = $parts[1]
    $process = @($Processes | Where-Object {
        $processTool = if ($_.Name -eq 'claude.exe') { 'claude' } elseif ($_.Name -eq 'node.exe' -and $_.CommandLine -match '(?i)@openai[\\/]codex') { 'codex' } else { $null }
        $processTool -eq $tool -and $_.CommandLine -match [regex]::Escape($id)
    } | Select-Object -First 1)
    if ($process.Count -eq 0) { throw "Cannot associate live session $Key with a process." }

    $transcript = Get-Transcript $tool $id
    if (-not $transcript) { throw "Cannot find the transcript for live session $Key." }
    $cwd = Get-TranscriptCwd $transcript.FullName
    if (-not $cwd -or -not (Test-Path -LiteralPath $cwd -PathType Container)) { throw "Cannot recover the working directory for live session $Key." }

    $titlePath = $cwd
    $worktreeRoot = & git -C $cwd rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $worktreeRoot) { $titlePath = [string]($worktreeRoot | Select-Object -First 1) }
    $processStartedAt = ([datetime]$process[0].CreationDate).ToUniversalTime()
    return [pscustomobject][ordered]@{
        tool = $tool
        id = $id
        cwd = $cwd
        title = Split-Path $titlePath -Leaf
        transcriptPath = $transcript.FullName
        terminalId = "reconciled-process:$tool`:$($process[0].ProcessId):$($processStartedAt.Ticks)"
        processId = [int]$process[0].ProcessId
        processStartedAt = $processStartedAt.ToString('o')
        startedAt = $transcript.CreationTimeUtc.ToString('o')
        lastSeenAt = (Get-Date).ToString('o')
        source = 'live-reconciliation'
    }
}

$activePath = Join-Path $Vault 'active.json'
$active = Read-CliSessionJson $activePath
if (-not $active -or -not $active.complete) { throw 'The active session registry is unavailable or incomplete.' }
$activeGeneratedAt = [string]$active.generatedAt
$processes = @(Get-CimInstance Win32_Process)
$closedData = Read-CliSessionJson (Join-Path $Vault 'closed.json')
$processMap = Get-OpenCliSessionProcessMap (Get-LiveCliSessionProcessMap $active $processes) $closedData
$liveKeys = @{}
foreach ($key in $processMap.Keys) { $liveKeys[$key] = $true }
$activeByKey = @{}
foreach ($entry in @($active.sessions | Sort-Object -Property @{ Expression={ [datetimeoffset]$_.lastSeenAt }; Descending=$true })) {
    $key = "$($entry.tool):$($entry.id.ToLowerInvariant())"
    if (-not $activeByKey.ContainsKey($key)) { $activeByKey[$key] = $entry }
}

$clean = foreach ($key in @($liveKeys.Keys | Sort-Object)) {
    if ($activeByKey.ContainsKey($key)) { $activeByKey[$key] } else { New-ReconciledEntry $key $processes }
}
$clean = @(Set-CliSessionWindowGroups -Entries $clean -ProcessMap $processMap)
$extra = @($activeByKey.Keys | Where-Object { -not $liveKeys.ContainsKey($_) } | Sort-Object)
$added = @($liveKeys.Keys | Where-Object { -not $activeByKey.ContainsKey($_) } | Sort-Object)

Write-Output "Active records: $($activeByKey.Count)"
Write-Output "Live logical sessions: $($liveKeys.Count)"
Write-Output "Remove from active recovery: $($extra.Count)"
$extra | ForEach-Object { Write-Output "  - $_" }
Write-Output "Add to active recovery: $($added.Count)"
$added | ForEach-Object { Write-Output "  + $_" }

if (-not $Apply) {
    Write-Output 'Dry run only. No recovery data was changed.'
    exit 0
}
if (@($clean).Count -ne $liveKeys.Count) { throw 'The reconciled set does not match the live logical session count.' }

Invoke-WithCliSessionLock {
    $currentActive = Read-CliSessionJson $activePath
    if (-not $currentActive -or [string]$currentActive.generatedAt -ne $activeGeneratedAt) {
        throw 'The active registry changed during reconciliation. Nothing was written; run reconciliation again.'
    }
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $backupDirectory = Join-Path $Vault "reconciliation-backups\$timestamp"
    New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
    foreach ($name in @('active.json','closed.json','pinned.json','observed.json','shutdown.json','last-open.json')) {
        $source = Join-Path $Vault $name
        if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $backupDirectory $name) }
    }
    Write-CliSessionJson $activePath (New-CliSessionSnapshot 'active' $clean)
    Write-CliSessionJson (Join-Path $Vault 'pinned.json') (New-CliSessionSnapshot 'manual' $clean)
    Write-Output "Reconciled recovery set written with $(@($clean).Count) logical sessions."
    Write-Output "Previous recovery files preserved at $backupDirectory"
}
