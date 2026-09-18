Set-StrictMode -Version 2
$script:CliTranscriptPaths = @{}

function ConvertTo-CliTimestampText($Value) {
    if ($Value -is [datetimeoffset]) {
        return $Value.UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ss.FFFFFFFK', [Globalization.CultureInfo]::InvariantCulture)
    }
    if ($Value -is [datetime]) {
        return $Value.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.FFFFFFFK', [Globalization.CultureInfo]::InvariantCulture)
    }
    return [string]$Value
}
function Get-CliSessionBootId {
    try {
        return (Get-CimInstance Win32_OperatingSystem -OperationTimeoutSec 3 -ErrorAction Stop).LastBootUpTime.ToUniversalTime().ToString('o')
    } catch {
        return 'unknown'
    }
}

function Read-CliSessionJson([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Write-CliSessionJson([string]$Path, $Value) {
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $json = $Value | ConvertTo-Json -Depth 12
    $temporaryPath = "$Path.$PID.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        [System.IO.File]::WriteAllText($temporaryPath, $json, (New-Object System.Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
    } finally {
        if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue }
    }
}

function Remove-CliSessionStaleTemporaryFiles([string]$Vault, [int]$OlderThanMinutes = 60) {
    if (-not (Test-Path -LiteralPath $Vault -PathType Container)) { return 0 }
    $cutoff = (Get-Date).AddMinutes(-$OlderThanMinutes)
    $stale = @(Get-ChildItem -LiteralPath $Vault -Filter '*.tmp' -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff })
    foreach ($file in $stale) { Remove-Item -LiteralPath $file.FullName -Force -ErrorAction SilentlyContinue }
    return $stale.Count
}

$script:CliSessionLastLockAcquired = $false

function Get-CliSessionLastLockAcquired { return $script:CliSessionLastLockAcquired }

function Invoke-WithCliSessionLock([scriptblock]$Action, [int]$TimeoutMilliseconds = 10000, [switch]$ProceedWithoutLock, [string]$MutexName = 'Local\CliSessionVaultV3') {
    $mutex = New-Object System.Threading.Mutex($false, $MutexName)
    $acquired = $false
    try {
        try {
            $acquired = $mutex.WaitOne($TimeoutMilliseconds)
        } catch [System.Threading.AbandonedMutexException] {
            $acquired = $true
        }
        $script:CliSessionLastLockAcquired = $acquired
        if (-not $acquired -and -not $ProceedWithoutLock) { throw 'Timed out waiting for the CLI session registry lock.' }
        & $Action
    } finally {
        if ($acquired) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}

function New-CliSessionSnapshot([string]$Mode, $Sessions, [string]$BootId = $null, [string[]]$UnsavedSessions = @()) {
    if (-not $BootId) { $BootId = Get-CliSessionBootId }
    [ordered]@{
        schemaVersion = 3
        generatedAt = (Get-Date).ToString('o')
        bootId = $BootId
        mode = $Mode
        complete = $true
        unsavedSessions = @($UnsavedSessions | Sort-Object -Unique)
        sessions = @(Get-CliSessionsByRecency $Sessions)
    }
}

function Get-CliSessionsByRecency($Sessions) {
    $seen = @{}
    $ordered = @($Sessions | Where-Object { $null -ne $_ } | Sort-Object -Property @{ Expression={
        try { [datetimeoffset]$_.lastSeenAt } catch { [datetimeoffset]::MinValue }
    }; Descending=$true }, tool, id)
    return @($ordered | Where-Object {
        $key = "$($_.tool):$($_.id.ToLowerInvariant())"
        if ($seen.ContainsKey($key)) { return $false }
        $seen[$key] = $true
        return $true
    })
}

function Get-CliSessionSignature($Sessions) {
    return (@($Sessions | Sort-Object tool,id | ForEach-Object { "$($_.tool):$($_.id)" }) -join '|')
}

function Update-CliSessionSet($Sessions, [string]$HookEventName, [string]$Tool, [string]$SessionId, $Entry = $null) {
    $Sessions = @($Sessions | Where-Object { $null -ne $_ })
    $key = "$Tool`:$SessionId"
    if ($HookEventName -eq 'SessionEnd') {
        return @($Sessions | Where-Object { "$($_.tool):$($_.id)" -ne $key })
    }

    if (-not $Entry) { throw 'A session entry is required for an active event.' }
    $terminalId = [string]$Entry.terminalId
    return @($Sessions | Where-Object {
        $candidateKey = "$($_.tool):$($_.id)"
        $candidateTerminalProperty = $_.PSObject.Properties['terminalId']
        $candidateTerminalId = if ($candidateTerminalProperty) { [string]$candidateTerminalProperty.Value } else { $null }
        $candidateKey -ne $key -and -not ($terminalId -and $_.tool -eq $Tool -and $candidateTerminalId -eq $terminalId)
    }) + [pscustomobject]$Entry
}

function Update-CliSessionSetForEnd($Sessions, [string]$Tool, [string]$SessionId, $Processes, $EndingProcess = $null) {
    $Sessions = @($Sessions | Where-Object { $null -ne $_ })
    $key = "$Tool`:$($SessionId.ToLowerInvariant())"
    $existing = @($Sessions | Where-Object { "$($_.tool):$($_.id.ToLowerInvariant())" -eq $key } | Select-Object -First 1)
    if ($existing.Count -eq 0) { return @($Sessions) }

    $remainingProcesses = @($Processes | Where-Object {
        -not $EndingProcess -or [int]$_.ProcessId -ne [int]$EndingProcess.ProcessId
    })
    $recoveryData = [pscustomobject]@{ sessions = @($Sessions) }
    $processMap = Get-LiveCliSessionProcessMap $recoveryData $remainingProcesses
    if (-not $processMap.ContainsKey($key)) {
        return @(Update-CliSessionSet $Sessions 'SessionEnd' $Tool $SessionId)
    }

    $survivingProcess = $processMap[$key]
    $entry = $existing[0].PSObject.Copy()
    $entry | Add-Member -NotePropertyName processId -NotePropertyValue ([int]$survivingProcess.ProcessId) -Force
    $entry | Add-Member -NotePropertyName processStartedAt -NotePropertyValue (([datetime]$survivingProcess.CreationDate).ToUniversalTime().ToString('o')) -Force
    $entry | Add-Member -NotePropertyName lastSeenAt -NotePropertyValue ((Get-Date).ToString('o')) -Force
    return @(Update-CliSessionSet $Sessions 'SessionStart' $Tool $SessionId $entry)
}

function Update-CliClosedSessionSet($ClosedSessions, [string]$HookEventName, [string]$Tool, [string]$SessionId, [bool]$SessionStillActive, [int]$ProcessId = 0, [string]$ProcessStartedAt = $null) {
    $ClosedSessions = @($ClosedSessions | Where-Object { $null -ne $_ })
    $key = "$Tool`:$($SessionId.ToLowerInvariant())"
    $matching = @($ClosedSessions | Where-Object { "$($_.tool):$($_.id.ToLowerInvariant())" -eq $key })
    $remaining = @($ClosedSessions | Where-Object { "$($_.tool):$($_.id.ToLowerInvariant())" -ne $key })
    if ($HookEventName -eq 'SessionEnd' -and -not $SessionStillActive) {
        $remaining += [pscustomobject][ordered]@{
            tool = $Tool
            id = $SessionId.ToLowerInvariant()
            closedAt = (Get-Date).ToString('o')
            processId = $ProcessId
            processStartedAt = $ProcessStartedAt
        }
    } elseif ($HookEventName -ne 'SessionEnd' -and $ProcessId -gt 0 -and $ProcessStartedAt) {
        $sameProcess = @($matching | Where-Object {
            $_.processId -eq $ProcessId -and $_.processStartedAt -and
            [math]::Abs((([datetime]$_.processStartedAt).ToUniversalTime() - ([datetime]$ProcessStartedAt).ToUniversalTime()).TotalSeconds) -le 2
        }).Count -gt 0
        if ($sameProcess) { $remaining += $matching }
    }
    return @($remaining)
}

function Get-CliClosedSessionKeys($ClosedData) {
    $keys = @{}
    if (-not $ClosedData) { return $keys }
    $property = $ClosedData.PSObject.Properties['sessions']
    if (-not $property) { return $keys }
    foreach ($entry in @($property.Value)) {
        if ($entry -and $entry.tool -and $entry.id) { $keys["$($entry.tool):$($entry.id.ToLowerInvariant())"] = $true }
    }
    return $keys
}

function Get-OpenCliSessionProcessMap($ProcessMap, $ClosedData) {
    $closedKeys = Get-CliClosedSessionKeys $ClosedData
    $open = @{}
    foreach ($key in $ProcessMap.Keys) {
        if (-not $closedKeys.ContainsKey($key)) { $open[$key] = $ProcessMap[$key] }
    }
    return $open
}

function Get-CliProcessTool($Process) {
    if ($Process.Name -eq 'claude.exe' -and $Process.CommandLine -match '(?i)[\\/]\.local[\\/]bin[\\/]claude\.exe(?:"|\s|$)') { return 'claude' }
    if ($Process.Name -eq 'codex.exe' -and $Process.ExecutablePath -match '(?i)@openai[\\/]codex') { return 'codex' }
    return $null
}

function Initialize-CliOpenFileProbe {
    if ('CliOpenFileProbe' -as [type]) { return }
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
public static class CliOpenFileProbe {
    const int SystemExtendedHandleInformation = 64;
    const uint ProcessDuplicateHandle = 0x40;
    const uint DuplicateSameAccess = 2;
    const uint FileTypeDisk = 1;
    [DllImport("ntdll.dll")] static extern int NtQuerySystemInformation(int informationClass, IntPtr information, int length, ref int returnLength);
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access, bool inherit, int processId);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool DuplicateHandle(IntPtr source, IntPtr sourceHandle, IntPtr target, out IntPtr targetHandle, uint access, bool inherit, uint options);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll")] static extern uint GetFileType(IntPtr handle);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern uint GetFinalPathNameByHandle(IntPtr handle, StringBuilder path, uint length, uint flags);
    public static Dictionary<int, string[]> GetOpenFiles(int[] processIds) {
        var size = 1 << 20;
        var needed = 0;
        var buffer = IntPtr.Zero;
        while (true) {
            buffer = Marshal.AllocHGlobal(size);
            var status = NtQuerySystemInformation(SystemExtendedHandleInformation, buffer, size, ref needed);
            if (status == 0) break;
            Marshal.FreeHGlobal(buffer);
            buffer = IntPtr.Zero;
            if (status != unchecked((int)0xC0000004)) throw new Win32Exception(status);
            size = Math.Max(size * 2, needed);
        }
        var processes = new Dictionary<int, IntPtr>();
        var files = new Dictionary<int, HashSet<string>>();
        foreach (var processId in new HashSet<int>(processIds)) {
            var process = OpenProcess(ProcessDuplicateHandle, false, processId);
            if (process == IntPtr.Zero) continue;
            processes[processId] = process;
            files[processId] = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        }
        try {
            var count = IntPtr.Size == 8 ? Marshal.ReadInt64(buffer) : Marshal.ReadInt32(buffer);
            var offset = IntPtr.Size * 2;
            var entrySize = IntPtr.Size * 3 + 16;
            for (long index = 0; index < count; index++, offset += entrySize) {
                var owner = IntPtr.Size == 8 ? Marshal.ReadInt64(buffer, offset + IntPtr.Size) : Marshal.ReadInt32(buffer, offset + IntPtr.Size);
                IntPtr process;
                if (owner > Int32.MaxValue || !processes.TryGetValue((int)owner, out process)) continue;
                var value = IntPtr.Size == 8 ? Marshal.ReadInt64(buffer, offset + IntPtr.Size * 2) : Marshal.ReadInt32(buffer, offset + IntPtr.Size * 2);
                IntPtr duplicate;
                if (!DuplicateHandle(process, new IntPtr(value), GetCurrentProcess(), out duplicate, 0, false, DuplicateSameAccess)) continue;
                try {
                    if (GetFileType(duplicate) != FileTypeDisk) continue;
                    var path = new StringBuilder(32768);
                    if (GetFinalPathNameByHandle(duplicate, path, (uint)path.Capacity, 0) > 0) files[(int)owner].Add(path.ToString());
                } finally {
                    CloseHandle(duplicate);
                }
            }
            var output = new Dictionary<int, string[]>();
            foreach (var item in files) {
                var paths = new string[item.Value.Count];
                item.Value.CopyTo(paths);
                output[item.Key] = paths;
            }
            return output;
        } finally {
            foreach (var process in processes.Values) CloseHandle(process);
            Marshal.FreeHGlobal(buffer);
        }
    }
}
'@
}

function Invoke-CliOpenFileProbeWorker($Processes, [int]$TimeoutMilliseconds = 45000, [string]$ProbeWorkerPath = (Join-Path $PSScriptRoot 'probe-cli-open-files.ps1')) {
    if (-not (Test-Path -LiteralPath $ProbeWorkerPath -PathType Leaf)) { throw "Open-file probe worker is missing: $ProbeWorkerPath" }
    $resultPath = Join-Path ([System.IO.Path]::GetTempPath()) "cli-open-files-$PID-$([guid]::NewGuid().ToString('N')).json"
    $errorPath = "$resultPath.error"
    $ids = @($Processes | ForEach-Object { [int]$_.ProcessId })
    $quotedWorker = $ProbeWorkerPath.Replace("'", "''")
    $quotedResult = $resultPath.Replace("'", "''")
    $quotedError = $errorPath.Replace("'", "''")
    $command = "& '$quotedWorker' -ProcessId $($ids -join ',') -OutputPath '$quotedResult' -ErrorPath '$quotedError'"
    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    $worker = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-EncodedCommand',$encodedCommand) -WindowStyle Hidden -PassThru
    try {
        if (-not $worker.WaitForExit($TimeoutMilliseconds)) {
            Stop-Process -Id $worker.Id -Force -ErrorAction SilentlyContinue
            $worker.WaitForExit(5000) | Out-Null
            throw "Transcript inspection exceeded $([math]::Round($TimeoutMilliseconds / 1000)) seconds and was stopped. The previous recovery set was preserved."
        }
        if ($worker.ExitCode -ne 0) {
            $detail = if (Test-Path -LiteralPath $errorPath -PathType Leaf) { (Get-Content -LiteralPath $errorPath -Raw).Trim() } else { '' }
            if (-not $detail) { $detail = "worker exited $($worker.ExitCode)" }
            throw "Transcript inspection failed: $detail"
        }
        if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) { throw 'Transcript inspection produced no result.' }
        $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
        $map = @{}
        foreach ($property in @($result.PSObject.Properties)) { $map[[int]$property.Name] = @($property.Value) }
        return $map
    } finally {
        Remove-Item -LiteralPath $resultPath,$errorPath -Force -ErrorAction SilentlyContinue
        if ($worker) { $worker.Dispose() }
    }
}

function Get-CliTranscriptId([string]$Path) {
    if ([System.IO.Path]::GetFileNameWithoutExtension($Path) -match '(?i)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$') {
        return $Matches[1].ToLowerInvariant()
    }
    return $null
}

function Invoke-WithCliSessionSaveLock([scriptblock]$Action, [int]$TimeoutMilliseconds = 0, [string]$MutexName = 'Local\CliSessionSaveV3') {
    $mutex = New-Object System.Threading.Mutex($false, $MutexName)
    $acquired = $false
    try {
        try {
            $acquired = $mutex.WaitOne($TimeoutMilliseconds)
        } catch [System.Threading.AbandonedMutexException] {
            $acquired = $true
        }
        if (-not $acquired) { throw 'Another CLI session save is already running.' }
        & $Action
    } finally {
        if ($acquired) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}

function Test-CliTranscriptIsResumable([string]$Tool, [string]$Path) {
    if ($Tool -eq 'claude') {
        return $Path -match '(?i)[\\/]\.claude[\\/]projects[\\/]' -and $Path -notmatch '(?i)[\\/]subagents[\\/]'
    }
    if ($Tool -ne 'codex' -or $Path -notmatch '(?i)[\\/]\.codex[\\/]sessions[\\/]') { return $false }

    foreach ($line in @(Get-Content -LiteralPath $Path -TotalCount 12 -ErrorAction Stop)) {
        try { $record = $line | ConvertFrom-Json } catch { continue }
        if ([string]$record.type -ne 'session_meta' -or -not $record.PSObject.Properties['payload']) { continue }
        $sourceProperty = $record.payload.PSObject.Properties['source']
        if (-not $sourceProperty) { return $false }
        return $sourceProperty.Value -is [string] -and [string]$sourceProperty.Value -eq 'cli'
    }
    throw "Cannot verify Codex transcript metadata: $Path"
}

function Get-CliProcessArgumentSessionId($Process) {
    if ($Process.CommandLine -match '(?i)(?:resume|--resume|-r|--session-id)\s+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})') {
        return $Matches[1].ToLowerInvariant()
    }
    return $null
}

function Get-CliClaudeRegisteredTranscript($Process, [string]$ClaudeRoot = (Join-Path $env:USERPROFILE '.claude')) {
    $registrationPath = Join-Path (Join-Path $ClaudeRoot 'sessions') "$($Process.ProcessId).json"
    if (-not (Test-Path -LiteralPath $registrationPath -PathType Leaf)) { return $null }
    try {
        $registration = Get-Content -LiteralPath $registrationPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
    } catch {
        throw "Cannot read Claude session registration for process $($Process.ProcessId): $($_.Exception.Message)"
    }
    if ([int]$registration.pid -ne [int]$Process.ProcessId) {
        throw "Claude session registration PID does not match live process $($Process.ProcessId)."
    }
    $registeredStart = try { [datetime]::FromFileTimeUtc([long]$registration.procStart) } catch { $null }
    $processStart = ([datetime]$Process.CreationDate).ToUniversalTime()
    if (-not $registeredStart -or [math]::Abs(($registeredStart - $processStart).TotalSeconds) -gt 2) {
        throw "Claude session registration is stale for live process $($Process.ProcessId)."
    }
    $sessionId = [string]$registration.sessionId
    if ($sessionId -notmatch '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$') {
        throw "Claude session registration has no valid session ID for live process $($Process.ProcessId)."
    }
    $cwd = [string]$registration.cwd
    if (-not $cwd) { throw "Claude session registration has no working directory for live process $($Process.ProcessId)." }
    $projectDirectory = Join-Path (Join-Path $ClaudeRoot 'projects') ($cwd -replace '[:\\/]', '-')
    $transcriptPath = Join-Path $projectDirectory "$($sessionId.ToLowerInvariant()).jsonl"
    if (-not (Test-Path -LiteralPath $transcriptPath -PathType Leaf)) {
        throw "Claude session registration transcript does not exist for live process $($Process.ProcessId): $transcriptPath"
    }
    if (-not (Test-CliTranscriptIsResumable claude $transcriptPath)) {
        throw "Claude session registration does not identify a top-level transcript for live process $($Process.ProcessId)."
    }
    return Get-Item -LiteralPath $transcriptPath
}

function Get-CliTranscriptWriterMatches($Processes, [scriptblock]$OpenFileResolver = $null, [scriptblock]$BatchOpenFileResolver = $null, [scriptblock]$ClaudeTranscriptResolver = $null) {
    $cliProcesses = @($Processes | Where-Object { Get-CliProcessTool $_ })
    if ($cliProcesses.Count -eq 0) { return @{} }
    $openFilesByProcess = $null
    if (-not $OpenFileResolver) {
        $handleProcesses = @($cliProcesses | Where-Object { (Get-CliProcessTool $_) -eq 'codex' })
        try {
            $openFilesByProcess = if ($handleProcesses.Count -eq 0) {
                @{}
            } elseif ($BatchOpenFileResolver) {
                & $BatchOpenFileResolver $handleProcesses
            } else {
                Invoke-CliOpenFileProbeWorker $handleProcesses
            }
        } catch {
            if (@($handleProcesses | Where-Object { Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }).Count -gt 0) {
                throw "Cannot inspect transcript handles for live CLI processes: $($_.Exception.Message)"
            }
            return @{}
        }
    }
    $writerMap = @{}
    foreach ($process in $cliProcesses) {
        $tool = Get-CliProcessTool $process
        if ($tool -eq 'claude') {
            $transcript = if ($ClaudeTranscriptResolver) {
                & $ClaudeTranscriptResolver $process @()
            } else {
                Get-CliClaudeRegisteredTranscript $process
            }
            if (-not $transcript -and (Get-CliProcessArgumentSessionId $process)) { continue }
            if (-not $transcript) { throw "Cannot identify the exact Claude session for live process $($process.ProcessId)." }
            $path = if ($transcript -is [System.IO.FileInfo]) { $transcript.FullName } else { [string]$transcript }
            if (-not (Get-CliTranscriptId $path) -or -not (Test-CliTranscriptIsResumable claude $path)) {
                throw "Claude session discovery returned an invalid transcript for live process $($process.ProcessId): $path"
            }
            $writerMap[[int]$process.ProcessId] = @($path)
            continue
        }
        if ($OpenFileResolver) {
            try {
                $openFiles = @(& $OpenFileResolver $process)
            } catch {
                if (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue) {
                    throw "Cannot inspect transcript handles for live $tool process $($process.ProcessId): $($_.Exception.Message)"
                }
                continue
            }
        } elseif (-not $openFilesByProcess.ContainsKey([int]$process.ProcessId)) {
            if (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue) {
                throw "Cannot inspect transcript handles for live $tool process $($process.ProcessId)."
            }
            continue
        } else {
            $openFiles = @($openFilesByProcess[[int]$process.ProcessId])
        }
        $paths = @($openFiles | ForEach-Object { $_ -replace '^\\\\\?\\', '' } | Where-Object {
            $_ -match '(?i)\.jsonl$' -and (Get-CliTranscriptId $_) -and (Test-CliTranscriptIsResumable $tool $_)
        })
        if ($paths.Count -gt 0) { $writerMap[[int]$process.ProcessId] = $paths }
    }
    return $writerMap
}

function Find-CliTranscript([string]$Tool, [string]$Id) {
    $key = "$Tool`:$($Id.ToLowerInvariant())"
    if ($script:CliTranscriptPaths.ContainsKey($key)) {
        $cachedPath = [string]$script:CliTranscriptPaths[$key]
        if (Test-Path -LiteralPath $cachedPath -PathType Leaf) { return Get-Item -LiteralPath $cachedPath }
    }
    $root = if ($Tool -eq 'codex') { Join-Path $env:USERPROFILE '.codex\sessions' } else { Join-Path $env:USERPROFILE '.claude\projects' }
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { return $null }
    return Get-ChildItem -LiteralPath $root -Recurse -File -Filter "*$Id*.jsonl" -ErrorAction SilentlyContinue | Where-Object {
        Test-CliTranscriptIsResumable $Tool $_.FullName
    } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

function New-CliSessionEntryFromTranscript([string]$Tool, [string]$Id, $Transcript, $Process) {
    if (-not $Transcript) { return $null }
    $cwd = $null
    $startedAt = $null
    foreach ($line in @(Get-Content -LiteralPath $Transcript.FullName -TotalCount 12 -ErrorAction SilentlyContinue)) {
        try { $record = $line | ConvertFrom-Json } catch { continue }
        $payload = if ($record.PSObject.Properties['payload']) { $record.payload } else { $record }
        if (-not $cwd -and $payload.PSObject.Properties['cwd']) { $cwd = [string]$payload.cwd }
        if (-not $startedAt -and $record.PSObject.Properties['timestamp']) { $startedAt = ConvertTo-CliTimestampText $record.timestamp }
        if (-not $startedAt -and $payload.PSObject.Properties['timestamp']) { $startedAt = ConvertTo-CliTimestampText $payload.timestamp }
        if ($cwd -and $startedAt) { break }
    }
    if (-not $cwd -or -not (Test-Path -LiteralPath $cwd -PathType Container)) { return $null }
    $lastSeenAt = $null
    $tail = @(Get-Content -LiteralPath $Transcript.FullName -Tail 20 -ErrorAction SilentlyContinue)
    [array]::Reverse($tail)
    foreach ($line in $tail) {
        try { $record = $line | ConvertFrom-Json } catch { continue }
        if ($record.PSObject.Properties['timestamp']) { $lastSeenAt = ConvertTo-CliTimestampText $record.timestamp; break }
    }
    if (-not $startedAt) { $startedAt = $Transcript.CreationTimeUtc.ToString('o') }
    if (-not $lastSeenAt) { $lastSeenAt = $Transcript.LastWriteTimeUtc.ToString('o') }
    $titlePath = $cwd
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'SilentlyContinue'
        $worktreeRoot = & git -C $cwd rev-parse --show-toplevel 2>$null
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($LASTEXITCODE -eq 0 -and $worktreeRoot) { $titlePath = [string]($worktreeRoot | Select-Object -First 1) }
    $processStartedAt = ([datetime]$Process.CreationDate).ToUniversalTime()
    return [pscustomobject][ordered]@{
        tool = $Tool
        id = $Id.ToLowerInvariant()
        cwd = $cwd
        title = Split-Path $titlePath -Leaf
        transcriptPath = $Transcript.FullName
        terminalId = "writer-process:$Tool`:$($Process.ProcessId):$($processStartedAt.Ticks)"
        processId = [int]$Process.ProcessId
        processStartedAt = $processStartedAt.ToString('o')
        startedAt = $startedAt
        lastSeenAt = $lastSeenAt
        source = 'transcript-writer'
    }
}

function New-CliProcessIndex($Processes) {
    $index = @{}
    foreach ($process in @($Processes)) { $index[[int]$process.ProcessId] = $process }
    return $index
}

function Test-CliProcessHasTerminalAncestor($Process, $ProcessIndex) {
    $current = $Process
    $visited = @{}
    for ($depth = 0; $depth -lt 32; $depth++) {
        $parentId = [int]$current.ParentProcessId
        if ($parentId -le 0 -or $visited.ContainsKey($parentId) -or -not $ProcessIndex.ContainsKey($parentId)) { return $false }
        $visited[$parentId] = $true
        $parent = $ProcessIndex[$parentId]
        $childCreated = ([datetime]$current.CreationDate).ToUniversalTime()
        $parentCreated = ([datetime]$parent.CreationDate).ToUniversalTime()
        if ($parentCreated -gt $childCreated.AddSeconds(2)) { return $false }
        if ($parent.Name -eq 'WindowsTerminal.exe') { return $true }
        $current = $parent
    }
    return $false
}

function Get-OrphanedCliProcesses($Processes) {
    $processIndex = New-CliProcessIndex $Processes
    return @($Processes | Where-Object {
        (Get-CliProcessTool $_) -and -not (Test-CliProcessHasTerminalAncestor $_ $processIndex)
    })
}

function Get-LiveCliSessionProcessMap($RecoveryData, $Processes, $TranscriptWriterMatches = $null) {
    $script:CliTranscriptPaths = @{}
    $map = @{}
    $ownedKeys = @{}
    $processIndex = New-CliProcessIndex $Processes
    foreach ($process in @($Processes)) {
        $tool = Get-CliProcessTool $process
        if (-not $tool -or -not (Test-CliProcessHasTerminalAncestor $process $processIndex)) { continue }

        $startedAt = ([datetime]$process.CreationDate).ToUniversalTime()
        $recoverySessions = if ($RecoveryData -and $RecoveryData.PSObject.Properties['sessions']) { @($RecoveryData.sessions) } else { @() }
        $owned = @($recoverySessions | Where-Object {
            $_.tool -eq $tool -and
            $_.processId -eq $process.ProcessId -and
            $_.processStartedAt -and
            [math]::Abs((([datetime]$_.processStartedAt).ToUniversalTime() - $startedAt).TotalSeconds) -le 2
        } | Sort-Object -Property @{ Expression={ [datetimeoffset]$_.lastSeenAt }; Descending=$true })

        if ($owned.Count -gt 0) {
            $key = "$tool`:$($owned[0].id.ToLowerInvariant())"
            $map[$key] = $process
            $ownedKeys[$key] = $true
        } elseif ($argumentSessionId = Get-CliProcessArgumentSessionId $process) {
            $key = "$tool`:$argumentSessionId"
            if (-not $ownedKeys.ContainsKey($key)) { $map[$key] = $process }
        }
    }
    $writerProcesses = @($Processes | Where-Object {
        (Get-CliProcessTool $_) -and (Test-CliProcessHasTerminalAncestor $_ $processIndex)
    })
    if ($null -eq $TranscriptWriterMatches) { $TranscriptWriterMatches = Get-CliTranscriptWriterMatches $writerProcesses }
    foreach ($process in $writerProcesses) {
        $processId = [int]$process.ProcessId
        if (-not $TranscriptWriterMatches.ContainsKey($processId)) { continue }
        $tool = Get-CliProcessTool $process
        foreach ($key in @($map.Keys | Where-Object { [int]$map[$_].ProcessId -eq $processId })) {
            $map.Remove($key)
        }
        foreach ($path in @($TranscriptWriterMatches[$processId])) {
            $id = Get-CliTranscriptId $path
            if ($id) {
                $key = "$tool`:$id"
                $map[$key] = $process
                $script:CliTranscriptPaths[$key] = [string]$path
            }
        }
    }
    return $map
}

function Get-LiveCliSessionKeys($RecoveryData, $Processes, $TranscriptWriterMatches = $null) {
    $keys = @{}
    $map = Get-LiveCliSessionProcessMap $RecoveryData $Processes $TranscriptWriterMatches
    foreach ($key in $map.Keys) { $keys[$key] = $true }
    return $keys
}

function Select-LiveCliSessionEntries($RecoveryData, $ProcessMap) {
    $entriesByKey = @{}
    foreach ($entry in @($RecoveryData.sessions | Sort-Object -Property @{ Expression={ [datetimeoffset]$_.lastSeenAt }; Descending=$true })) {
        $key = "$($entry.tool):$($entry.id.ToLowerInvariant())"
        if (-not $entriesByKey.ContainsKey($key)) { $entriesByKey[$key] = $entry }
    }
    $missing = @($ProcessMap.Keys | Where-Object { -not $entriesByKey.ContainsKey($_) } | Sort-Object)
    if ($missing.Count -gt 0) { throw "Live CLI sessions are missing from the registry: $($missing -join ', ')" }
    return @($ProcessMap.Keys | Sort-Object | ForEach-Object { $entriesByKey[$_] })
}

function Resolve-LiveCliSessionEntries($RecoverySets, $ProcessMap, [scriptblock]$TranscriptResolver = $null) {
    $entriesByKey = @{}
    $sourceIndexes = @{}
    $sourceIndex = 0
    foreach ($recoveryData in @($RecoverySets)) {
        if ($recoveryData) {
            foreach ($entry in @($recoveryData.sessions | Sort-Object -Property @{ Expression={ [datetimeoffset]$_.lastSeenAt }; Descending=$true })) {
                if (-not $entry -or -not $entry.PSObject.Properties['tool'] -or -not $entry.PSObject.Properties['id']) { continue }
                $tool = [string]$entry.tool
                $id = [string]$entry.id
                if ([string]::IsNullOrWhiteSpace($tool) -or [string]::IsNullOrWhiteSpace($id)) { continue }
                $key = "$tool`:$($id.ToLowerInvariant())"
                if (-not $entriesByKey.ContainsKey($key)) {
                    $entriesByKey[$key] = $entry
                    $sourceIndexes[$key] = $sourceIndex
                }
            }
        }
        $sourceIndex++
    }

    foreach ($key in @($ProcessMap.Keys | Where-Object { -not $entriesByKey.ContainsKey($_) })) {
        $parts = $key.Split(':', 2)
        $transcript = if ($TranscriptResolver) { & $TranscriptResolver $parts[0] $parts[1] } else { Find-CliTranscript $parts[0] $parts[1] }
        $entry = New-CliSessionEntryFromTranscript $parts[0] $parts[1] $transcript $ProcessMap[$key]
        if ($entry) {
            $process = $ProcessMap[$key]
            $processStartedAt = ([datetime]$process.CreationDate).ToUniversalTime()
            $windowSource = @($entriesByKey.Values | Where-Object {
                $_.tool -eq $parts[0] -and $_.processId -eq $process.ProcessId -and $_.processStartedAt -and
                [math]::Abs((([datetime]$_.processStartedAt).ToUniversalTime() - $processStartedAt).TotalSeconds) -le 2 -and
                (Get-CliSessionWindowGroup $_)
            } | Sort-Object -Property @{ Expression={ [datetimeoffset]$_.lastSeenAt }; Descending=$true } | Select-Object -First 1)
            if ($windowSource.Count -gt 0) {
                Set-CliSessionWindowGroup $entry (Get-CliSessionWindowGroup $windowSource[0]) | Out-Null
            }
            $entriesByKey[$key] = $entry
            $sourceIndexes[$key] = -1
        }
    }
    $matchedKeys = @($ProcessMap.Keys | Where-Object { $entriesByKey.ContainsKey($_) })
    [pscustomobject]@{
        Entries = @(Get-CliSessionsByRecency @($matchedKeys | ForEach-Object { $entriesByKey[$_] }))
        RecoveredKeys = @($matchedKeys | Where-Object { $sourceIndexes[$_] -ne 0 } | Sort-Object)
        MissingKeys = @($ProcessMap.Keys | Where-Object { -not $entriesByKey.ContainsKey($_) } | Sort-Object)
    }
}

function Get-CliSnapshotUnsavedSessions($RecoveryData) {
    if (-not $RecoveryData) { return @() }
    if ($RecoveryData -is [System.Collections.IDictionary]) {
        if (-not $RecoveryData.Contains('unsavedSessions')) { return @() }
        $value = $RecoveryData['unsavedSessions']
    } else {
        $property = $RecoveryData.PSObject.Properties['unsavedSessions']
        if (-not $property) { return @() }
        $value = $property.Value
    }
    return @($value | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Sort-Object -Unique)
}

function Get-CliSessionWindowGroup($Entry) {
    $property = $Entry.PSObject.Properties['windowGroup']
    if ($property -and -not [string]::IsNullOrWhiteSpace([string]$property.Value)) { return [string]$property.Value }
    return $null
}

function Set-CliSessionWindowGroup($Entry, [string]$WindowGroup) {
    $Entry | Add-Member -NotePropertyName windowGroup -NotePropertyValue $WindowGroup -Force
    return $Entry
}

function Initialize-CliSessionConsoleProbe {
    if ('CliSessionConsoleProbe' -as [type]) { return }
    Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class CliSessionConsoleProbe {
    [DllImport("kernel32.dll", SetLastError=true)] public static extern bool FreeConsole();
    [DllImport("kernel32.dll", SetLastError=true)] public static extern bool AttachConsole(uint pid);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern uint GetConsoleTitle(StringBuilder title, uint size);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern bool SetConsoleTitle(string title);
}
'@
}

function Get-WindowsTerminalTitleWindowMap {
    $map = @{}
    try {
        Add-Type -AssemblyName UIAutomationClient
        Add-Type -AssemblyName UIAutomationTypes
        $root = [System.Windows.Automation.AutomationElement]::RootElement
        $tabCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::TabItem)
        foreach ($terminalProcess in @(Get-Process WindowsTerminal -ErrorAction SilentlyContinue)) {
            $windowCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $terminalProcess.Id)
            $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $windowCondition)
            foreach ($window in $windows) {
                $windowGroup = "windows-terminal-window:$($window.Current.NativeWindowHandle)"
                $tabs = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $tabCondition)
                foreach ($tab in $tabs) {
                    $title = [string]$tab.Current.Name
                    if ([string]::IsNullOrWhiteSpace($title)) { continue }
                    $map[$title] = @(@($map[$title]) + $windowGroup | Sort-Object -Unique)
                }
            }
        }
    } catch {
        return @{}
    }
    return $map
}

function Invoke-CliSessionConsoleWindowProbe($Process, [switch]$Detailed) {
    $originalTitle = $null
    $attached = $false
    $result = [pscustomobject]@{ Succeeded=$false; WindowGroup=$null }
    try {
        Initialize-CliSessionConsoleProbe
        Add-Type -AssemblyName UIAutomationClient
        Add-Type -AssemblyName UIAutomationTypes
        [CliSessionConsoleProbe]::FreeConsole() | Out-Null
        $attached = [CliSessionConsoleProbe]::AttachConsole([uint32]$Process.ProcessId)
        if (-not $attached) { throw "Cannot attach to console process $($Process.ProcessId)." }
        $buffer = New-Object System.Text.StringBuilder 1024
        [CliSessionConsoleProbe]::GetConsoleTitle($buffer, [uint32]$buffer.Capacity) | Out-Null
        $originalTitle = $buffer.ToString()
        $token = "__CLI_SESSION_PROBE_$([guid]::NewGuid().ToString('N'))__"
        if (-not [CliSessionConsoleProbe]::SetConsoleTitle($token)) { throw "Cannot set the console title for process $($Process.ProcessId)." }
        Start-Sleep -Milliseconds 175
        $root = [System.Windows.Automation.AutomationElement]::RootElement
        $tabCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::TabItem)
        $matches = @()
        foreach ($terminalProcess in @(Get-Process WindowsTerminal -ErrorAction SilentlyContinue)) {
            $windowCondition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $terminalProcess.Id)
            $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $windowCondition)
            foreach ($window in $windows) {
                $tabs = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $tabCondition)
                foreach ($tab in $tabs) {
                    if ([string]$tab.Current.Name -eq $token) { $matches += "windows-terminal-window:$($window.Current.NativeWindowHandle)" }
                }
            }
        }
        $currentBuffer = New-Object System.Text.StringBuilder 1024
        [CliSessionConsoleProbe]::GetConsoleTitle($currentBuffer, [uint32]$currentBuffer.Capacity) | Out-Null
        $tokenStillSet = $currentBuffer.ToString() -eq $token
        if ($matches.Count -eq 1 -or ($matches.Count -eq 0 -and $tokenStillSet)) {
            $result.Succeeded = $true
            if ($matches.Count -eq 1) { $result.WindowGroup = $matches[0] }
        }
    } catch {
    } finally {
        if ($attached -and $null -ne $originalTitle) {
            [CliSessionConsoleProbe]::SetConsoleTitle($originalTitle) | Out-Null
            Start-Sleep -Milliseconds 50
        }
        if ('CliSessionConsoleProbe' -as [type]) {
            [CliSessionConsoleProbe]::FreeConsole() | Out-Null
        }
    }
    if ($Detailed) { return $result }
    return $result.WindowGroup
}

function Test-CliSessionWindowProbeComplete($RequestedProcessIds, $ProbedProcessIds, $FailedProcessIds) {
    if (@($FailedProcessIds).Count -gt 0) { return $false }
    $requested = @($RequestedProcessIds | ForEach-Object { [int]$_ } | Sort-Object -Unique)
    $probed = @($ProbedProcessIds | ForEach-Object { [int]$_ } | Sort-Object -Unique)
    return ($requested -join ',') -eq ($probed -join ',')
}

function Test-WindowsTerminalResponding {
    $terminals = @(Get-Process WindowsTerminal -ErrorAction SilentlyContinue)
    if ($terminals.Count -eq 0) { return $false }
    return @($terminals | Where-Object { -not $_.Responding }).Count -eq 0
}

function Get-WindowsTerminalWindowGroupsForProcesses($Processes, [int]$TimeoutSeconds = 60, [switch]$Detailed) {
    $result = [pscustomobject]@{ TitleMap=@{}; WindowGroups=@{}; ProbedProcessIds=@(); Complete=$false }
    $processIds = @()
    $seen = @{}
    foreach ($item in @($Processes)) {
        $id = if ($item -is [int]) { [int]$item } else { [int]$item.ProcessId }
        if (-not $seen.ContainsKey($id)) { $seen[$id] = $true; $processIds += $id }
    }
    if ($processIds.Count -eq 0) {
        $result.Complete = $true
        if ($Detailed) { return $result }
        return @{}
    }
    if (-not (Test-WindowsTerminalResponding)) {
        if ($Detailed) { return $result }
        return @{}
    }
    $probeScript = Join-Path $PSScriptRoot 'probe-cli-window.ps1'
    if (-not (Test-Path -LiteralPath $probeScript -PathType Leaf)) {
        if ($Detailed) { return $result }
        return @{}
    }
    $resultPath = Join-Path ([System.IO.Path]::GetTempPath()) "cli-session-window-$([guid]::NewGuid().ToString('N')).txt"
    try {
        $arguments = @(
            '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
            '-File', "`"$probeScript`"",
            '-ProcessIds', ($processIds -join ','),
            '-Out', "`"$resultPath`"",
            '-DeadlineSeconds', [math]::Max(1, $TimeoutSeconds - 3)
        )
        $probe = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -PassThru -WindowStyle Hidden
        $finished = $probe.WaitForExit($TimeoutSeconds * 1000)
        if (-not $finished) {
            Stop-Process -Id $probe.Id -Force -ErrorAction SilentlyContinue
            $probe.WaitForExit(2000) | Out-Null
        }
        if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
            if ($Detailed) { return $result }
            return @{}
        }
        $text = [System.IO.File]::ReadAllText($resultPath)
        if ([string]::IsNullOrWhiteSpace($text)) {
            if ($Detailed) { return $result }
            return @{}
        }
        $data = $text | ConvertFrom-Json
        $map = @{}
        $titleMap = @{}
        $titleMapProperty = $data.PSObject.Properties['titleMap']
        if ($titleMapProperty) {
            foreach ($property in $titleMapProperty.Value.PSObject.Properties) { $titleMap[$property.Name] = @($property.Value) }
        }
        $windowGroupsProperty = $data.PSObject.Properties['windowGroups']
        if ($windowGroupsProperty) {
            foreach ($property in $windowGroupsProperty.Value.PSObject.Properties) { $map[$property.Name] = [string]$property.Value }
            $result.ProbedProcessIds = @($data.probedProcessIds | ForEach-Object { [int]$_ })
            $result.Complete = $finished -and $probe.ExitCode -eq 0 -and [bool]$data.complete
        } else {
            foreach ($property in $data.PSObject.Properties) { $map[$property.Name] = [string]$property.Value }
        }
        $result.TitleMap = $titleMap
        $result.WindowGroups = $map
        if ($Detailed) { return $result }
        return $map
    } catch {
        if ($Detailed) { return $result }
        return @{}
    } finally {
        Remove-Item -LiteralPath $resultPath -Force -ErrorAction SilentlyContinue
    }
}

function Get-WindowsTerminalWindowGroupForProcess($Process) {
    $map = Get-WindowsTerminalWindowGroupsForProcesses @($Process)
    return $map[[string]$Process.ProcessId]
}

function Get-CliSessionWindowProbeOrder($ProcessMap, $Entries, [switch]$UnknownOnly) {
    $entriesByKey = @{}
    foreach ($entry in @($Entries)) {
        if ($null -eq $entry -or -not $entry.PSObject.Properties['tool'] -or -not $entry.PSObject.Properties['id']) { continue }
        $entriesByKey["$($entry.tool):$($entry.id.ToLowerInvariant())"] = $entry
    }
    $unknown = @()
    $known = @()
    foreach ($key in @($ProcessMap.Keys | Sort-Object)) {
        $processId = [int]$ProcessMap[$key].ProcessId
        if ($entriesByKey.ContainsKey($key) -and (Get-CliSessionWindowGroup $entriesByKey[$key])) {
            $known += $processId
        } else {
            $unknown += $processId
        }
    }
    if ($UnknownOnly) { return @($unknown) }
    return @($unknown + $known)
}

function Get-CliSessionWindowDiscovery($ProcessMap, $Entries = $null, [switch]$VerifyKnownWindowGroups) {
    $discovery = @{ TitleMap=@{}; ProcessWindowGroups=@{}; TerminalResponding=$false; ProbeComplete=$false; ProbedProcessIds=@() }
    $unknown = @(Get-CliSessionWindowProbeOrder $ProcessMap $Entries -UnknownOnly)
    if (-not $VerifyKnownWindowGroups -and $unknown.Count -eq 0) { return $discovery }
    if (-not (Test-WindowsTerminalResponding)) { return $discovery }
    $discovery.TerminalResponding = $true
    $targets = if ($VerifyKnownWindowGroups) { @(Get-CliSessionWindowProbeOrder $ProcessMap $Entries) } else { $unknown }
    $probe = Get-WindowsTerminalWindowGroupsForProcesses $targets -Detailed
    $discovery.TitleMap = $probe.TitleMap
    $discovery.ProcessWindowGroups = $probe.WindowGroups
    $discovery.ProbedProcessIds = @($probe.ProbedProcessIds)
    $discovery.ProbeComplete = [bool]$probe.Complete
    return $discovery
}

function Select-CliSessionProcessMapByWindowEvidence($ProcessMap, $Discovery) {
    if (-not $Discovery -or -not $Discovery.TerminalResponding -or -not $Discovery.ProbeComplete) { return $ProcessMap }
    $verifiedProcessIds = @{}
    foreach ($processId in $Discovery.ProcessWindowGroups.Keys) { $verifiedProcessIds[[int]$processId] = $true }
    $filtered = @{}
    foreach ($key in $ProcessMap.Keys) {
        if ($verifiedProcessIds.ContainsKey([int]$ProcessMap[$key].ProcessId)) { $filtered[$key] = $ProcessMap[$key] }
    }
    return $filtered
}

function Set-CliSessionWindowGroups($Entries, $ProcessMap, $Discovery = $null) {
    if ($null -eq $Entries) { return @() }
    if (@($Entries).Count -eq 0) { return @() }
    if (-not $Discovery) { $Discovery = Get-CliSessionWindowDiscovery $ProcessMap $Entries }
    $titleMap = $Discovery.TitleMap
    $processWindowGroups = $Discovery.ProcessWindowGroups
    foreach ($entry in @($Entries)) {
        if ($null -eq $entry) { throw 'A null CLI session entry was passed to window grouping.' }
        if (-not $entry.PSObject.Properties['tool'] -or -not $entry.PSObject.Properties['id']) {
            throw "Invalid CLI session entry passed to window grouping: $($entry.GetType().FullName) $($entry | ConvertTo-Json -Compress -Depth 3)"
        }
        $key = "$($entry.tool):$($entry.id.ToLowerInvariant())"
        $processId = if ($ProcessMap.ContainsKey($key)) { [string]$ProcessMap[$key].ProcessId } else { $null }
        $windowGroup = if ($processId -and $processWindowGroups.ContainsKey($processId)) { $processWindowGroups[$processId] } else { $null }
        if (-not $windowGroup) { $windowGroup = Get-CliSessionWindowGroup $entry }
        if (-not $windowGroup -and $titleMap.ContainsKey([string]$entry.title) -and @($titleMap[[string]$entry.title]).Count -eq 1) {
            $windowGroup = @($titleMap[[string]$entry.title])[0]
        }
        if (-not $windowGroup) { $windowGroup = "terminal-title:$($entry.title)" }
        Set-CliSessionWindowGroup $entry $windowGroup
    }
}

function Get-CliRestoreWindowTarget($Entry) {
    $windowGroup = Get-CliSessionWindowGroup $Entry
    if (-not $windowGroup) { $windowGroup = "terminal-title:$($Entry.title)" }
    if ($windowGroup -match '^cli-recovery-[0-9a-f]{16}$') { return $windowGroup }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($windowGroup))
    } finally {
        $sha.Dispose()
    }
    return "cli-recovery-$([System.BitConverter]::ToString($hash).Replace('-', '').Substring(0, 16).ToLowerInvariant())"
}

function Get-CliRestoreLaunchArguments($Entry, [string]$Launcher) {
    $windowTarget = Get-CliRestoreWindowTarget $Entry
    $displayTitle = "$($Entry.title) [$($Entry.id.Substring(0, 8))]"
    return @('-w', $windowTarget, 'new-tab', '--profile', '{61c54bbd-c2c6-5271-96e7-009a87ff44bf}', '--title', $displayTitle, '-d', $Entry.cwd, 'powershell.exe', '-NoLogo', '-ExecutionPolicy', 'Bypass', '-File', $Launcher, '-Tool', $Entry.tool, '-SessionId', $Entry.id, '-WindowGroup', $windowTarget)
}

function Get-CliSessionEntryProblem($Entry) {
    if ($Entry.tool -notin @('codex','claude')) { return "unsupported tool '$($Entry.tool)'" }
    if ([string]$Entry.id -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') { return 'invalid session id' }
    if (-not (Test-Path -LiteralPath $Entry.cwd -PathType Container)) { return "working directory does not exist: $($Entry.cwd)" }
    $transcriptProperty = $Entry.PSObject.Properties['transcriptPath']
    $transcriptPath = if ($transcriptProperty) { [string]$transcriptProperty.Value } else { $null }
    if ($transcriptPath -and -not (Test-Path -LiteralPath $transcriptPath -PathType Leaf)) { return "transcript no longer exists: $transcriptPath" }
    if ($transcriptPath) {
        try {
            if (-not (Test-CliTranscriptIsResumable $Entry.tool $transcriptPath)) { return "transcript is not a top-level resumable $($Entry.tool) conversation" }
        } catch {
            return "transcript metadata cannot be verified: $transcriptPath"
        }
    }
    return $null
}

function Split-CliRecoverySet($Entries) {
    $restorable = @()
    $unrestorable = @()
    foreach ($entry in @($Entries)) {
        $problem = Get-CliSessionEntryProblem $entry
        if ($problem) {
            $unrestorable += [pscustomobject]@{ Entry = $entry; Problem = $problem }
        } else {
            $restorable += $entry
        }
    }
    return [pscustomobject]@{ Restorable = @($restorable); Unrestorable = @($unrestorable) }
}

function Select-NewestCliRecoverySource($Candidates) {
    $eligible = foreach ($candidate in @($Candidates)) {
        $data = $candidate.Data
        if ($data -and $data.complete -and @($data.sessions).Count -gt 0) {
            $generatedAt = try { [datetimeoffset]$data.generatedAt } catch { [datetimeoffset]::MinValue }
            [pscustomobject]@{ Path=$candidate.Path; Data=$data; Priority=$candidate.Priority; GeneratedAt=$generatedAt }
        }
    }
    if (-not $eligible) { throw 'No non-empty exact recovery set exists.' }
    $unconsumedManual = @($eligible | Where-Object {
        $_.Priority -ge 90 -and $_.Data.mode -eq 'manual' -and -not $_.Data.PSObject.Properties['consumedAt']
    })
    if ($unconsumedManual.Count -gt 0) {
        return $unconsumedManual | Sort-Object -Property @{ Expression={ $_.GeneratedAt }; Descending=$true } | Select-Object -First 1
    }
    return $eligible | Sort-Object -Property @{ Expression={ $_.GeneratedAt }; Descending=$true }, @{ Expression={ $_.Priority }; Descending=$true } | Select-Object -First 1
}

Export-ModuleMember -Function Get-CliSessionBootId,Read-CliSessionJson,Write-CliSessionJson,Remove-CliSessionStaleTemporaryFiles,Invoke-WithCliSessionLock,Invoke-WithCliSessionSaveLock,Get-CliSessionLastLockAcquired,Test-WindowsTerminalResponding,Get-CliSessionWindowDiscovery,Get-CliSessionWindowProbeOrder,Select-CliSessionProcessMapByWindowEvidence,Test-CliSessionWindowProbeComplete,New-CliSessionSnapshot,Get-CliSessionsByRecency,Get-CliSnapshotUnsavedSessions,Get-CliSessionSignature,Update-CliSessionSet,Update-CliSessionSetForEnd,Update-CliClosedSessionSet,Get-CliClosedSessionKeys,Get-OpenCliSessionProcessMap,Get-CliProcessTool,Get-CliTranscriptId,Test-CliTranscriptIsResumable,Get-CliTranscriptWriterMatches,New-CliProcessIndex,Test-CliProcessHasTerminalAncestor,Get-OrphanedCliProcesses,Get-LiveCliSessionProcessMap,Get-LiveCliSessionKeys,Select-LiveCliSessionEntries,Resolve-LiveCliSessionEntries,Get-CliSessionWindowGroup,Set-CliSessionWindowGroup,Invoke-CliSessionConsoleWindowProbe,Get-WindowsTerminalWindowGroupForProcess,Set-CliSessionWindowGroups,Get-CliRestoreWindowTarget,Get-CliRestoreLaunchArguments,Get-CliSessionEntryProblem,Split-CliRecoverySet,Select-NewestCliRecoverySource
