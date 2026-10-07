$ErrorActionPreference = 'Stop'

$repository = Split-Path -Parent $PSScriptRoot
$scriptsDirectory = Join-Path $repository '.agents\machine\utility\peer-cli\scripts'
$finishScript = Join-Path $scriptsDirectory 'finish.ps1'
$reaperScript = Join-Path $scriptsDirectory 'finish_reaper.ps1'
$cleanupProofScript = Join-Path $repository '.agents\engineering\workflow\merge\scripts\cleanup_proof.py'
$scratch = Join-Path ([IO.Path]::GetTempPath()) "finish-tests-$([guid]::NewGuid().ToString('N'))"

$originalState = $env:AGENT_STATE_DIRECTORY
$originalHostNames = $env:AGENT_CLI_HOST_NAMES
$originalCloseMode = $env:AGENT_FINISH_CLOSE_MODE
$originalReaperTimeout = $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS
$originalFixture = $env:CLEANUP_PROOF_FORGE_FIXTURE

# Never let any invocation in this file resolve a real claude/codex ancestor: this test process itself
# may run under a real Claude or Codex session, and matching it would close or kill the real session.
$env:AGENT_CLI_HOST_NAMES = 'codex'

function Stop-TestProcessTree {
    param([int] $Id)

    try { & taskkill.exe /PID $Id /T /F 2>$null | Out-Null } catch { }
}

function Assert-True {
    param([object] $Actual, [string] $Message)
    if ($Actual -ne $true) { throw "$Message Actual: $Actual" }
}

function Assert-False {
    param([object] $Actual, [string] $Message)
    if ($Actual -ne $false) { throw "$Message Actual: $Actual" }
}

function Assert-Equal {
    param([object] $Expected, [object] $Actual, [string] $Message)
    if ($Expected -ne $Actual) { throw "$Message Expected: $Expected Actual: $Actual" }
}

function Assert-Contains {
    param([string] $Actual, [string] $Expected, [string] $Message)
    if (-not $Actual.Contains($Expected)) { throw "$Message Output: $Actual" }
}

function Get-EntryProperty {
    param($Entry, [string] $Name)
    if ($null -eq $Entry) { return $null }
    $property = $Entry.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-Sha256Hex {
    param([string] $Text)
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try { $hashBytes = $sha256.ComputeHash($bytes) } finally { $sha256.Dispose() }
    return -join ($hashBytes | ForEach-Object { $_.ToString('x2') })
}

function Get-ResolvedPath {
    param([string] $Path)
    return (Get-Item -LiteralPath $Path).FullName.TrimEnd('\')
}

function Get-WorktreeDigest {
    param([string] $ResolvedWorktree)
    return Get-Sha256Hex -Text ($ResolvedWorktree -replace '\\', '/')
}

function Get-ReceiptPath {
    param([string] $StateDirectory, [string] $ResolvedWorktree)
    return Join-Path $StateDirectory ("merge-cleanup\receipts\" + (Get-WorktreeDigest $ResolvedWorktree) + '.json')
}

function Get-ResultRecordPath {
    param([string] $StateDirectory, [string] $ResolvedWorktree)
    return Join-Path $StateDirectory ("merge-cleanup\results\" + (Get-WorktreeDigest $ResolvedWorktree) + '.json')
}

function Get-ObligationRecordPath {
    param([string] $StateDirectory, [string] $ResolvedWorktree)
    return Join-Path $StateDirectory ("merge-cleanup\obligations\" + (Get-WorktreeDigest $ResolvedWorktree) + '.json')
}

function Write-JsonFile {
    param([string] $Path, [object] $Data)
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    [IO.File]::WriteAllText($Path, ($Data | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding $false))
}

function Read-JsonFile {
    param([string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

function Wait-Condition {
    param([scriptblock] $Condition, [int] $TimeoutSeconds = 30, [int] $IntervalMilliseconds = 200)
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (& $Condition) { return $true }
        Start-Sleep -Milliseconds $IntervalMilliseconds
    }
    return (& $Condition)
}

function Invoke-GitOrThrow {
    param([string] $Cwd, [string[]] $Arguments)
    $output = & git -C $Cwd @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "git $($Arguments -join ' ') failed: $output" }
    return ($output -join "`n")
}

function New-TestRepo {
    param([string] $Root)
    $bare = Join-Path $Root 'origin.git'
    $primary = Join-Path $Root 'primary'
    & git init --bare -q -b main $bare | Out-Null
    & git clone -q $bare $primary | Out-Null
    Invoke-GitOrThrow -Cwd $primary -Arguments @('config', 'user.email', 't@example.com') | Out-Null
    Invoke-GitOrThrow -Cwd $primary -Arguments @('config', 'user.name', 't') | Out-Null
    Set-Content -LiteralPath (Join-Path $primary 'README.md') -Value 'base' -Encoding UTF8
    Invoke-GitOrThrow -Cwd $primary -Arguments @('add', 'README.md') | Out-Null
    Invoke-GitOrThrow -Cwd $primary -Arguments @('commit', '-q', '-m', 'base') | Out-Null
    Invoke-GitOrThrow -Cwd $primary -Arguments @('push', '-q', '-u', 'origin', 'main') | Out-Null
    Invoke-GitOrThrow -Cwd $primary -Arguments @('remote', 'set-head', 'origin', 'main') | Out-Null
    [pscustomobject]@{ Bare = $bare; Primary = $primary }
}

function Add-FeatureWorktree {
    param([string] $Primary, [string] $Root, [string] $Branch, [string] $BaseRef = 'main')
    Invoke-GitOrThrow -Cwd $Primary -Arguments @('branch', $Branch, $BaseRef) | Out-Null
    $worktree = Join-Path $Root ($Branch + '-wt')
    Invoke-GitOrThrow -Cwd $Primary -Arguments @('worktree', 'add', '-q', $worktree, $Branch) | Out-Null
    Set-Content -LiteralPath (Join-Path $worktree 'feature.txt') -Value 'change' -Encoding UTF8
    Invoke-GitOrThrow -Cwd $worktree -Arguments @('add', '.') | Out-Null
    Invoke-GitOrThrow -Cwd $worktree -Arguments @('commit', '-q', '-m', 'feature commit') | Out-Null
    Invoke-GitOrThrow -Cwd $worktree -Arguments @('push', '-q', '-u', 'origin', $Branch) | Out-Null
    return $worktree
}

function Invoke-SquashMerge {
    param([string] $Primary, [string] $Branch)
    Invoke-GitOrThrow -Cwd $Primary -Arguments @('checkout', '-q', 'main') | Out-Null
    Invoke-GitOrThrow -Cwd $Primary -Arguments @('merge', '-q', '--squash', $Branch) | Out-Null
    Invoke-GitOrThrow -Cwd $Primary -Arguments @('commit', '-q', '-m', "squash merge $Branch") | Out-Null
    $oid = (Invoke-GitOrThrow -Cwd $Primary -Arguments @('rev-parse', 'HEAD')).Trim()
    Invoke-GitOrThrow -Cwd $Primary -Arguments @('push', '-q', 'origin', 'main') | Out-Null
    return $oid
}

function Write-ForgeFixture {
    param([string] $Path, [string] $State, [string] $HeadRefOid, [string] $MergeOid, [array] $OpenPrs = @())
    Write-JsonFile -Path $Path -Data @{
        pr_view  = @{ state = $State; headRefOid = $HeadRefOid; mergeCommit = @{ oid = $MergeOid } }
        open_prs = $OpenPrs
    }
}

function Invoke-CleanupProof {
    param([string] $Primary, [string] $Worktree, [string] $Branch, [string] $Head, [int] $Pr, [string] $StateDirectory, [string] $Fixture)
    $previousState = $env:AGENT_STATE_DIRECTORY
    $previousFixture = $env:CLEANUP_PROOF_FORGE_FIXTURE
    $env:AGENT_STATE_DIRECTORY = $StateDirectory
    $env:CLEANUP_PROOF_FORGE_FIXTURE = $Fixture
    Push-Location -LiteralPath $Primary
    try {
        $output = & python -B $cleanupProofScript --worktree $Worktree --branch $Branch --head $Head --pr $Pr --default main 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
        $env:AGENT_STATE_DIRECTORY = $previousState
        $env:CLEANUP_PROOF_FORGE_FIXTURE = $previousFixture
    }
    [pscustomobject]@{ ExitCode = $exitCode; Output = ($output -join "`n") }
}

function Invoke-FinishProcess {
    param([string] $Worktree, [hashtable] $Environment = @{}, [int] $TimeoutSeconds = 30)
    $stdout = [IO.Path]::GetTempFileName()
    $stderr = [IO.Path]::GetTempFileName()
    $previous = @{}
    foreach ($key in $Environment.Keys) {
        $previous[$key] = [Environment]::GetEnvironmentVariable($key)
        [Environment]::SetEnvironmentVariable($key, [string] $Environment[$key])
    }
    try {
        $process = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $finishScript, '-Worktree', $Worktree
        ) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            Stop-TestProcessTree $process.Id
            throw "finish.ps1 did not exit within $TimeoutSeconds seconds for '$Worktree'."
        }
        [pscustomobject]@{
            ExitCode = $process.ExitCode
            StdOut   = (Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue)
            StdErr   = (Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue)
        }
    }
    finally {
        foreach ($key in $Environment.Keys) {
            [Environment]::SetEnvironmentVariable($key, $previous[$key])
        }
        Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
    }
}

$jobObjectSource = @'
using System;
using System.Runtime.InteropServices;

public class FinishTestJobObject : IDisposable
{
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string lpName);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool SetInformationJobObject(IntPtr hJob, int JobObjectInfoClass, IntPtr lpJobObjectInfo, uint cbJobObjectInfoLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool TerminateJobObject(IntPtr hJob, uint uExitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool CloseHandle(IntPtr hObject);

    [StructLayout(LayoutKind.Sequential)]
    struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct IO_COUNTERS
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    const int JobObjectExtendedLimitInformation = 9;
    const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000;

    IntPtr handle;

    public FinishTestJobObject()
    {
        handle = CreateJobObject(IntPtr.Zero, null);
        var info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        int length = Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION));
        IntPtr ptr = Marshal.AllocHGlobal(length);
        try
        {
            Marshal.StructureToPtr(info, ptr, false);
            SetInformationJobObject(handle, JobObjectExtendedLimitInformation, ptr, (uint)length);
        }
        finally
        {
            Marshal.FreeHGlobal(ptr);
        }
    }

    public bool AssignProcess(IntPtr processHandle)
    {
        return AssignProcessToJobObject(handle, processHandle);
    }

    public void Terminate()
    {
        TerminateJobObject(handle, 1);
    }

    public void Dispose()
    {
        if (handle != IntPtr.Zero)
        {
            CloseHandle(handle);
            handle = IntPtr.Zero;
        }
    }
}
'@

try {
    New-Item -ItemType Directory -Path $scratch -Force | Out-Null
    Add-Type -TypeDefinition $jobObjectSource -Language CSharp


    $preflightState = Join-Path $scratch 'preflight-state'
    New-Item -ItemType Directory -Path $preflightState -Force | Out-Null

    $noReceiptTarget = Join-Path $scratch 'no-receipt-target'
    New-Item -ItemType Directory -Path $noReceiptTarget -Force | Out-Null
    $noReceiptResult = Invoke-FinishProcess -Worktree $noReceiptTarget -Environment @{ AGENT_STATE_DIRECTORY = $preflightState }
    Assert-False -Actual ($noReceiptResult.ExitCode -eq 0) -Message 'finish.ps1 did not refuse a worktree with no receipt.'
    Assert-Contains -Actual $noReceiptResult.StdErr -Expected 'no cleanup_proof.py receipt' -Message 'The no-receipt refusal did not name the missing receipt.'
    Assert-False -Actual (Test-Path -LiteralPath (Get-ResultRecordPath -StateDirectory $preflightState -ResolvedWorktree (Get-ResolvedPath $noReceiptTarget))) -Message 'A result record was written despite the preflight refusal.'

    $staleTarget = Join-Path $scratch 'stale-receipt-target'
    New-Item -ItemType Directory -Path $staleTarget -Force | Out-Null
    $staleResolved = Get-ResolvedPath $staleTarget
    Write-JsonFile -Path (Get-ReceiptPath -StateDirectory $preflightState -ResolvedWorktree $staleResolved) -Data @{
        worktree = $staleResolved; primary = $scratch; branch = 'feature'; head = ('a' * 40); pr = 1
        merge_oid = ('b' * 40); default = 'main'; verdict = 'removable'
        recorded_at = ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - 7200)
    }
    $staleResult = Invoke-FinishProcess -Worktree $staleTarget -Environment @{ AGENT_STATE_DIRECTORY = $preflightState }
    Assert-False -Actual ($staleResult.ExitCode -eq 0) -Message 'finish.ps1 did not refuse a stale receipt.'
    Assert-Contains -Actual $staleResult.StdErr -Expected 'stale' -Message 'The stale-receipt refusal did not say so.'

    $unattachedTarget = Join-Path $scratch 'unattached-target'
    New-Item -ItemType Directory -Path $unattachedTarget -Force | Out-Null
    Invoke-GitOrThrow -Cwd $unattachedTarget -Arguments @('init', '-q', '-b', 'feature') | Out-Null
    Invoke-GitOrThrow -Cwd $unattachedTarget -Arguments @('config', 'user.email', 't@example.com') | Out-Null
    Invoke-GitOrThrow -Cwd $unattachedTarget -Arguments @('config', 'user.name', 't') | Out-Null
    Set-Content -LiteralPath (Join-Path $unattachedTarget 'file.txt') -Value 'content' -Encoding UTF8
    Invoke-GitOrThrow -Cwd $unattachedTarget -Arguments @('add', '.') | Out-Null
    Invoke-GitOrThrow -Cwd $unattachedTarget -Arguments @('commit', '-q', '-m', 'init') | Out-Null
    $unattachedHead = (Invoke-GitOrThrow -Cwd $unattachedTarget -Arguments @('rev-parse', 'HEAD')).Trim()
    $unattachedResolved = Get-ResolvedPath $unattachedTarget
    Write-JsonFile -Path (Get-ReceiptPath -StateDirectory $preflightState -ResolvedWorktree $unattachedResolved) -Data @{
        worktree = $unattachedResolved; primary = $scratch; branch = 'feature'; head = $unattachedHead; pr = 1
        merge_oid = ('b' * 40); default = 'main'; verdict = 'removable'
        recorded_at = ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
    }
    $unattachedFakeHostDirectory = Join-Path $scratch 'unattached-fake-host'
    New-Item -ItemType Directory -Path $unattachedFakeHostDirectory -Force | Out-Null
    $unattachedFakeHost = Join-Path $unattachedFakeHostDirectory 'codex.exe'
    Copy-Item -LiteralPath $env:ComSpec -Destination $unattachedFakeHost
    $unattachedStdOut = Join-Path $scratch 'unattached.stdout.log'
    $unattachedStdErr = Join-Path $scratch 'unattached.stderr.log'
    $previousUnattachedState = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $preflightState
    $unattachedProcess = $null
    try {
        $innerCommand = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$finishScript`" -Worktree `"$unattachedTarget`""
        $unattachedProcess = Start-Process -FilePath $unattachedFakeHost -ArgumentList @('/c', $innerCommand) `
            -WorkingDirectory $scratch -RedirectStandardOutput $unattachedStdOut -RedirectStandardError $unattachedStdErr -PassThru -WindowStyle Hidden
        if (-not $unattachedProcess.WaitForExit(60000)) {
            Stop-TestProcessTree $unattachedProcess.Id
            throw 'The unattached-worktree scenario did not exit in time.'
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousUnattachedState
    }
    Assert-False -Actual ($unattachedProcess.ExitCode -eq 0) -Message 'finish.ps1 did not refuse a worktree that is not its own attachment.'
    $unattachedStdErrText = Get-Content -LiteralPath $unattachedStdErr -Raw -ErrorAction SilentlyContinue
    Assert-Contains -Actual $unattachedStdErrText -Expected "not this session's own attachment" -Message 'The unattached-worktree refusal did not name the attachment check.'

    Write-Output 'PASS finish.tests.ps1: preflight refusals'


    $breakawayRoot = Join-Path $scratch 'breakaway'
    New-Item -ItemType Directory -Path $breakawayRoot -Force | Out-Null
    $dummyPrimary = Join-Path $breakawayRoot 'not-a-repo'
    $dummyWorktree = Join-Path $breakawayRoot 'dummy-worktree'
    New-Item -ItemType Directory -Path $dummyPrimary, $dummyWorktree -Force | Out-Null
    $breakawayState = Join-Path $breakawayRoot 'state'
    $breakawayResult = Join-Path $breakawayRoot 'result.json'
    $readyFile = Join-Path $breakawayRoot 'ready.flag'

    $deadHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $deadHost.WaitForExit(5000) | Out-Null
    $deadPid = $deadHost.Id
    $deadStart = ([DateTimeOffset]($deadHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

    $childScriptPath = Join-Path $breakawayRoot 'child.ps1'
    @'
param(
    [string] $Ready,
    [string] $Finish,
    [string] $Reaper,
    [string] $DummyWorktree,
    [int] $DeadPid,
    [double] $DeadStart,
    [string] $DummyPrimary,
    [string] $ResultPath,
    [string] $StateDirectory
)

$ErrorActionPreference = 'Stop'
try { . $Finish -Worktree $DummyWorktree } catch { }

while (-not (Test-Path -LiteralPath $Ready)) { Start-Sleep -Milliseconds 50 }

$commandLine = Format-CommandLine -Parts @(
    'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $Reaper,
    '-HostPid', $DeadPid, '-HostStart', $DeadStart, '-Head', ('a' * 40), '-Primary', $DummyPrimary, '-Worktree', $DummyWorktree,
    '-Branch', 'dummy', '-Default', 'main', '-Result', $ResultPath, '-StateDirectory', $StateDirectory
)
Start-DetachedReaper -CommandLine $commandLine | Out-Null
Start-Sleep -Seconds 20
'@ | Set-Content -LiteralPath $childScriptPath -Encoding UTF8

    $job = New-Object FinishTestJobObject
    $childProcess = $null
    try {
        $childProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $childScriptPath,
            '-Ready', $readyFile, '-Finish', $finishScript, '-Reaper', $reaperScript,
            '-DummyWorktree', $dummyWorktree, '-DeadPid', $deadPid, '-DeadStart', $deadStart,
            '-DummyPrimary', $dummyPrimary, '-ResultPath', $breakawayResult, '-StateDirectory', $breakawayState
        ) -PassThru -WindowStyle Hidden

        $assigned = $job.AssignProcess($childProcess.Handle)
        Assert-True -Actual $assigned -Message 'Could not assign the test child process to the kill-on-close job object.'

        New-Item -ItemType File -Path $readyFile -Force | Out-Null

        $spawned = Wait-Condition -TimeoutSeconds 30 -Condition {
            $record = Read-JsonFile -Path $breakawayResult
            $null -ne $record -and $null -ne (Get-EntryProperty -Entry $record -Name 'started')
        }
        if (-not $spawned) {
            $record = Read-JsonFile -Path $breakawayResult
            Assert-True -Actual ($null -ne $record -and $null -ne $record.started) -Message 'The reaper never wrote a started stamp before the job was terminated.'
        }

        $job.Terminate()
        $job.Dispose()

        Start-Sleep -Milliseconds 500
        Assert-True -Actual ($null -eq (Get-Process -Id $childProcess.Id -ErrorAction SilentlyContinue)) `
            -Message 'The job-contained child process survived job termination; the test setup is not proving breakaway.'

        $wroteTerminalStatus = Wait-Condition -TimeoutSeconds 30 -Condition {
            $record = Read-JsonFile -Path $breakawayResult
            $null -ne $record -and $null -ne $record.status
        }
        Assert-True -Actual $wroteTerminalStatus -Message 'The reaper did not keep running and write a terminal status after its job-contained parent was killed.'
    }
    finally {
        if ($childProcess -and (Get-Process -Id $childProcess.Id -ErrorAction SilentlyContinue)) {
            Stop-TestProcessTree $childProcess.Id
        }
        Get-Process -Name 'powershell' -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -and $_.Path -eq (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') } |
            Where-Object {
                try { (Get-CimInstance -ClassName Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like "*$reaperScript*" } catch { $false }
            } | ForEach-Object {
                try { Stop-TestProcessTree $_.Id } catch { }
            }
    }

    Write-Output 'PASS finish.tests.ps1: job-breakaway proof'


    $e2eRoot = Join-Path $scratch 'end-to-end'
    New-Item -ItemType Directory -Path $e2eRoot -Force | Out-Null
    $e2eState = Join-Path $e2eRoot 'state'
    New-Item -ItemType Directory -Path $e2eState -Force | Out-Null

    $repo = New-TestRepo -Root $e2eRoot
    $worktree = Add-FeatureWorktree -Primary $repo.Primary -Root $e2eRoot -Branch 'feature'
    $head = (Invoke-GitOrThrow -Cwd $worktree -Arguments @('rev-parse', 'HEAD')).Trim()
    $mergeOid = Invoke-SquashMerge -Primary $repo.Primary -Branch 'feature'

    $fixturePath = Join-Path $e2eRoot 'fixture.json'
    Write-ForgeFixture -Path $fixturePath -State 'MERGED' -HeadRefOid $head -MergeOid $mergeOid

    $proof = Invoke-CleanupProof -Primary $repo.Primary -Worktree $worktree -Branch 'feature' -Head $head -Pr 1 -StateDirectory $e2eState -Fixture $fixturePath
    Assert-Equal -Expected 0 -Actual $proof.ExitCode -Message "cleanup_proof.py did not approve the squash merge: $($proof.Output)"
    Assert-Contains -Actual $proof.Output -Expected 'removable' -Message 'cleanup_proof.py did not print removable.'

    $worktreeResolved = Get-ResolvedPath $worktree
    $obligationPath = Get-ObligationRecordPath -StateDirectory $e2eState -ResolvedWorktree $worktreeResolved
    Write-JsonFile -Path $obligationPath -Data @{ session_id = 'test'; worktree = $worktreeResolved; branch = 'feature'; pr = 1 }

    $fakeCodex = Join-Path $e2eRoot 'codex.exe'
    Copy-Item -LiteralPath $env:ComSpec -Destination $fakeCodex

    $previousE2eState = $env:AGENT_STATE_DIRECTORY
    $previousCloseMode = $env:AGENT_FINISH_CLOSE_MODE
    $env:AGENT_STATE_DIRECTORY = $e2eState
    $env:AGENT_FINISH_CLOSE_MODE = 'process'
    $fakeHostProcess = $null
    try {
        $innerCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File $finishScript"
        $hostCommand = "`"$fakeCodex`" /c $innerCommand"
        $fakeHostProcess = Start-Process -FilePath $env:ComSpec -ArgumentList @('/c', $hostCommand) `
            -WorkingDirectory $worktree -PassThru -WindowStyle Hidden

        $succeeded = Wait-Condition -TimeoutSeconds 60 -Condition {
            $resultsDirectory = Join-Path $e2eState 'merge-cleanup\results'
            if (-not (Test-Path -LiteralPath $resultsDirectory)) { return $false }
            foreach ($file in (Get-ChildItem -LiteralPath $resultsDirectory -Filter '*.json' -File)) {
                $record = Read-JsonFile -Path $file.FullName
                if ($record -and $record.worktree -eq $worktreeResolved -and $record.status -eq 'succeeded') { return $true }
            }
            return $false
        }
        if (-not $succeeded) {
            throw 'The end-to-end cleanup did not reach a succeeded result record in time.'
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousE2eState
        $env:AGENT_FINISH_CLOSE_MODE = $previousCloseMode
        if ($fakeHostProcess -and (Get-Process -Id $fakeHostProcess.Id -ErrorAction SilentlyContinue)) {
            Stop-TestProcessTree $fakeHostProcess.Id
        }
    }

    Assert-False -Actual (Test-Path -LiteralPath $worktree) -Message 'The worktree directory still exists after end-to-end cleanup.'
    $porcelainAfter = Invoke-GitOrThrow -Cwd $repo.Primary -Arguments @('worktree', 'list', '--porcelain')
    Assert-False -Actual ($porcelainAfter.Contains($worktreeResolved)) -Message 'The worktree is still registered after end-to-end cleanup.'
    $branchStillPresent = $(& git -C $repo.Primary show-ref --verify --quiet refs/heads/feature; $LASTEXITCODE -eq 0)
    Assert-False -Actual $branchStillPresent -Message 'The feature branch still exists after end-to-end cleanup.'
    $obligationCleared = Wait-Condition -TimeoutSeconds 10 -Condition { -not (Test-Path -LiteralPath $obligationPath) }
    Assert-True -Actual $obligationCleared -Message 'The merge-cleanup obligation was not cleared after a successful cleanup.'

    Write-Output 'PASS finish.tests.ps1: end-to-end squash-merge cleanup'


    $timeoutRoot = Join-Path $scratch 'timeout'
    New-Item -ItemType Directory -Path $timeoutRoot -Force | Out-Null
    $timeoutRepo = New-TestRepo -Root $timeoutRoot
    $timeoutWorktree = Add-FeatureWorktree -Primary $timeoutRepo.Primary -Root $timeoutRoot -Branch 'feature'
    $timeoutResolved = Get-ResolvedPath $timeoutWorktree
    $timeoutHead = (Invoke-GitOrThrow -Cwd $timeoutWorktree -Arguments @('rev-parse', 'HEAD')).Trim()
    $timeoutResult = Join-Path $timeoutRoot 'result.json'
    $timeoutState = Join-Path $timeoutRoot 'state'

    $aliveHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'ping -n 60 127.0.0.1 > nul' -PassThru -WindowStyle Hidden
    try {
        $aliveStart = ([DateTimeOffset]($aliveHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

        $previousTimeoutState = $env:AGENT_STATE_DIRECTORY
        $previousReaperTimeout = $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS
        $env:AGENT_STATE_DIRECTORY = $timeoutState
        $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS = '2'
        $reaperProcess = $null
        try {
            $reaperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
                '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $reaperScript,
                '-HostPid', $aliveHost.Id, '-HostStart', $aliveStart,
                '-Head', $timeoutHead,
                '-Primary', $timeoutRepo.Primary, '-Worktree', $timeoutResolved,
                '-Branch', 'feature', '-Default', 'main', '-Result', $timeoutResult,
                '-StateDirectory', $timeoutState
            ) -PassThru -WindowStyle Hidden

            $wroteTimeoutRecord = Wait-Condition -TimeoutSeconds 60 -Condition {
                $record = Read-JsonFile -Path $timeoutResult
                $null -ne $record -and $null -ne $record.status
            }
            if (-not $wroteTimeoutRecord -and (Get-Process -Id $reaperProcess.Id -ErrorAction SilentlyContinue)) {
                Stop-TestProcessTree $reaperProcess.Id
            }
        }
        finally {
            $env:AGENT_STATE_DIRECTORY = $previousTimeoutState
            $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS = $previousReaperTimeout
        }

        $timeoutRecord = Read-JsonFile -Path $timeoutResult
        Assert-True -Actual ($null -ne $timeoutRecord) -Message 'The timeout scenario did not write a result record.'
        Assert-Equal -Expected 'timeout' -Actual $timeoutRecord.status -Message 'The timeout scenario did not record a timeout status.'
        Assert-True -Actual (Test-Path -LiteralPath $timeoutWorktree) -Message 'The worktree was touched despite the host never exiting.'
        $timeoutBranchPresent = $(& git -C $timeoutRepo.Primary show-ref --verify --quiet refs/heads/feature; $LASTEXITCODE -eq 0)
        Assert-True -Actual $timeoutBranchPresent -Message 'The feature branch was removed despite the host never exiting.'
    }
    finally {
        if (Get-Process -Id $aliveHost.Id -ErrorAction SilentlyContinue) {
            Stop-TestProcessTree $aliveHost.Id
        }
    }

    Write-Output 'PASS finish.tests.ps1: reaper timeout path'


    $r1aRoot = Join-Path $scratch 'r1-preflight-moved-head'
    New-Item -ItemType Directory -Path $r1aRoot -Force | Out-Null
    $r1aState = Join-Path $r1aRoot 'state'
    New-Item -ItemType Directory -Path $r1aState -Force | Out-Null
    $r1aRepo = New-TestRepo -Root $r1aRoot
    $r1aWorktree = Add-FeatureWorktree -Primary $r1aRepo.Primary -Root $r1aRoot -Branch 'feature'
    $r1aHead = (Invoke-GitOrThrow -Cwd $r1aWorktree -Arguments @('rev-parse', 'HEAD')).Trim()
    $r1aMergeOid = Invoke-SquashMerge -Primary $r1aRepo.Primary -Branch 'feature'
    $r1aFixture = Join-Path $r1aRoot 'fixture.json'
    Write-ForgeFixture -Path $r1aFixture -State 'MERGED' -HeadRefOid $r1aHead -MergeOid $r1aMergeOid
    $r1aProof = Invoke-CleanupProof -Primary $r1aRepo.Primary -Worktree $r1aWorktree -Branch 'feature' -Head $r1aHead -Pr 1 -StateDirectory $r1aState -Fixture $r1aFixture
    Assert-Equal -Expected 0 -Actual $r1aProof.ExitCode -Message "cleanup_proof.py did not approve the worktree before the post-receipt commit: $($r1aProof.Output)"

    Set-Content -LiteralPath (Join-Path $r1aWorktree 'late.txt') -Value 'late change' -Encoding UTF8
    Invoke-GitOrThrow -Cwd $r1aWorktree -Arguments @('add', '.') | Out-Null
    Invoke-GitOrThrow -Cwd $r1aWorktree -Arguments @('commit', '-q', '-m', 'late commit') | Out-Null

    $r1aResult = Invoke-FinishProcess -Worktree $r1aWorktree -Environment @{ AGENT_STATE_DIRECTORY = $r1aState }
    Assert-False -Actual ($r1aResult.ExitCode -eq 0) -Message 'finish.ps1 did not refuse a worktree whose HEAD moved after the receipt was recorded.'
    Assert-Contains -Actual $r1aResult.StdErr -Expected 'cleanup_proof.py again' -Message 'The moved-HEAD refusal did not tell the agent to re-run cleanup_proof.py.'
    Assert-True -Actual (Test-Path -LiteralPath $r1aWorktree) -Message 'The worktree was removed despite the moved-HEAD refusal.'

    $movedHeadRoot = Join-Path $scratch 'r1-branch-preserve'
    New-Item -ItemType Directory -Path $movedHeadRoot -Force | Out-Null
    $movedHeadState = Join-Path $movedHeadRoot 'state'
    $movedHeadRepo = New-TestRepo -Root $movedHeadRoot
    $movedHeadWorktree = Add-FeatureWorktree -Primary $movedHeadRepo.Primary -Root $movedHeadRoot -Branch 'feature'
    $movedHeadResolved = Get-ResolvedPath $movedHeadWorktree
    $movedHeadHead = (Invoke-GitOrThrow -Cwd $movedHeadWorktree -Arguments @('rev-parse', 'HEAD')).Trim()

    $movedHeadTree = (Invoke-GitOrThrow -Cwd $movedHeadRepo.Primary -Arguments @('rev-parse', "$movedHeadHead^{tree}")).Trim()
    $movedHeadLateCommit = (Invoke-GitOrThrow -Cwd $movedHeadRepo.Primary -Arguments @('commit-tree', $movedHeadTree, '-p', $movedHeadHead, '-m', 'late commit')).Trim()
    Invoke-GitOrThrow -Cwd $movedHeadRepo.Primary -Arguments @('update-ref', 'refs/heads/feature', $movedHeadLateCommit) | Out-Null

    $movedHeadResult = Join-Path $movedHeadRoot 'result.json'
    $movedHeadDeadHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $movedHeadDeadHost.WaitForExit(5000) | Out-Null
    $movedHeadDeadStart = ([DateTimeOffset]($movedHeadDeadHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

    $movedHeadReaperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $reaperScript,
        '-HostPid', $movedHeadDeadHost.Id, '-HostStart', $movedHeadDeadStart,
        '-Head', $movedHeadHead,
        '-Primary', $movedHeadRepo.Primary, '-Worktree', $movedHeadResolved,
        '-Branch', 'feature', '-Default', 'main', '-Result', $movedHeadResult,
        '-StateDirectory', $movedHeadState
    ) -PassThru -WindowStyle Hidden

    $movedHeadWrote = Wait-Condition -TimeoutSeconds 30 -Condition {
        $record = Read-JsonFile -Path $movedHeadResult
        $null -ne $record -and $null -ne $record.status
    }
    if (-not $movedHeadWrote -and (Get-Process -Id $movedHeadReaperProcess.Id -ErrorAction SilentlyContinue)) {
        Stop-TestProcessTree $movedHeadReaperProcess.Id
    }

    $movedHeadRecord = Read-JsonFile -Path $movedHeadResult
    Assert-True -Actual ($null -ne $movedHeadRecord) -Message 'The branch-preserve scenario did not write a result record.'
    Assert-Equal -Expected 'branch-preserved' -Actual $movedHeadRecord.status -Message 'The reaper did not preserve a branch whose tip moved after the receipt head.'
    Assert-True -Actual (-not (Test-Path -LiteralPath $movedHeadWorktree)) -Message 'The worktree was not removed even though only the branch should be preserved.'
    $movedHeadBranchStillPresent = $(& git -C $movedHeadRepo.Primary show-ref --verify --quiet refs/heads/feature; $LASTEXITCODE -eq 0)
    Assert-True -Actual $movedHeadBranchStillPresent -Message 'The moved branch was deleted despite its tip no longer matching the receipt head.'

    Write-Output 'PASS finish.tests.ps1: preflight refuses a moved HEAD; reaper preserves a moved branch'


    $ownEntryRoot = Join-Path $scratch 'r3-peer-title'
    New-Item -ItemType Directory -Path $ownEntryRoot -Force | Out-Null
    $ownEntryState = Join-Path $ownEntryRoot 'state'
    New-Item -ItemType Directory -Path (Join-Path $ownEntryState 'cli-sessions') -Force | Out-Null
    $ownEntryWorktree = Join-Path $ownEntryRoot 'worktree'
    New-Item -ItemType Directory -Path $ownEntryWorktree -Force | Out-Null
    $ownEntryResolved = Get-ResolvedPath $ownEntryWorktree
    $ownEntryDummySource = Join-Path $ownEntryRoot 'dummy-source'
    New-Item -ItemType Directory -Path $ownEntryDummySource -Force | Out-Null

    $ownHostFake = [pscustomobject]@{ Pid = 123456; Started = 1700000000.125 }
    Write-JsonFile -Path (Join-Path $ownEntryState 'cli-sessions\own.json') -Data @{
        session_id = 'own'; title = 'mine'; cwd = $ownEntryResolved; pid = $ownHostFake.Pid; pid_started_at = $ownHostFake.Started
    }
    Write-JsonFile -Path (Join-Path $ownEntryState 'cli-sessions\peer.json') -Data @{
        session_id = 'peer'; title = 'peer-tab'; cwd = $ownEntryResolved; pid = 987654; pid_started_at = 1600000000.0
    }

    $previousR3State = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $ownEntryState
    try {
        $ownEntryAttachment = & {
            try { . $finishScript -Worktree $ownEntryDummySource } catch { }
            Get-TitleAndAttachment -ResolvedWorktree $ownEntryResolved -StartingLocation $ownEntryResolved -OwnHost $ownHostFake
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousR3State
    }
    Assert-Equal -Expected 'mine' -Actual $ownEntryAttachment.Title -Message "The tab title came from a peer's registry entry instead of this session's own one."
    Assert-True -Actual $ownEntryAttachment.Attached -Message "This session's own registry entry, with a cwd under the worktree, was not recognized as attached."

    $ownEntryOutsideState = Join-Path $ownEntryRoot 'state-outside'
    New-Item -ItemType Directory -Path (Join-Path $ownEntryOutsideState 'cli-sessions') -Force | Out-Null
    $ownEntryOutsideCwd = Join-Path $ownEntryRoot 'outside-cwd'
    New-Item -ItemType Directory -Path $ownEntryOutsideCwd -Force | Out-Null
    Write-JsonFile -Path (Join-Path $ownEntryOutsideState 'cli-sessions\own-outside.json') -Data @{
        session_id = 'own-outside'; title = 'mine-outside'; cwd = (Get-ResolvedPath $ownEntryOutsideCwd)
        pid = $ownHostFake.Pid; pid_started_at = $ownHostFake.Started
    }
    $ownEntryOutsideResolved = Get-ResolvedPath $ownEntryOutsideCwd
    $previousR3OutsideState = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $ownEntryOutsideState
    try {
        $ownEntryOutsideNotAttached = & {
            try { . $finishScript -Worktree $ownEntryDummySource } catch { }
            Get-TitleAndAttachment -ResolvedWorktree $ownEntryResolved -StartingLocation $ownEntryOutsideResolved -OwnHost $ownHostFake
        }
        $ownEntryAttachedViaPwd = & {
            try { . $finishScript -Worktree $ownEntryDummySource } catch { }
            Get-TitleAndAttachment -ResolvedWorktree $ownEntryResolved -StartingLocation $ownEntryResolved -OwnHost $ownHostFake
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousR3OutsideState
    }
    Assert-False -Actual $ownEntryOutsideNotAttached.Attached -Message 'A self entry outside the worktree, with a starting location also outside it, was wrongly treated as attached.'
    Assert-True -Actual $ownEntryAttachedViaPwd.Attached -Message "A session running from inside the worktree was not recognized as attached even though its self entry's cwd is elsewhere."

    Write-Output 'PASS finish.tests.ps1: own registry entry provides the tab title; attachment follows the PWD or the self entry cwd'


    $parentWaitRoot = Join-Path $scratch 'r7-parent-wait'
    New-Item -ItemType Directory -Path $parentWaitRoot -Force | Out-Null
    $parentWaitRepo = New-TestRepo -Root $parentWaitRoot
    $parentWaitWorktree = Add-FeatureWorktree -Primary $parentWaitRepo.Primary -Root $parentWaitRoot -Branch 'feature'
    $parentWaitResolved = Get-ResolvedPath $parentWaitWorktree
    $parentWaitHead = (Invoke-GitOrThrow -Cwd $parentWaitWorktree -Arguments @('rev-parse', 'HEAD')).Trim()
    $parentWaitResult = Join-Path $parentWaitRoot 'result.json'
    $parentWaitState = Join-Path $parentWaitRoot 'state'

    $parentWaitDeadHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $parentWaitDeadHost.WaitForExit(5000) | Out-Null
    $parentWaitDeadStart = ([DateTimeOffset]($parentWaitDeadHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

    $parentWaitAliveParent = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'ping -n 60 127.0.0.1 > nul' -PassThru -WindowStyle Hidden
    try {
        $parentWaitAliveStart = ([DateTimeOffset]($parentWaitAliveParent.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

        $previousR7ReaperTimeout = $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS
        $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS = '2'
        $parentWaitReaperProcess = $null
        try {
            $parentWaitReaperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
                '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $reaperScript,
                '-HostPid', $parentWaitDeadHost.Id, '-HostStart', $parentWaitDeadStart,
                '-ParentPid', $parentWaitAliveParent.Id, '-ParentStart', $parentWaitAliveStart,
                '-Head', $parentWaitHead,
                '-Primary', $parentWaitRepo.Primary, '-Worktree', $parentWaitResolved,
                '-Branch', 'feature', '-Default', 'main', '-Result', $parentWaitResult,
                '-StateDirectory', $parentWaitState
            ) -PassThru -WindowStyle Hidden

            $parentWaitWrote = Wait-Condition -TimeoutSeconds 30 -Condition {
                $record = Read-JsonFile -Path $parentWaitResult
                $null -ne $record -and $null -ne $record.status
            }
            if (-not $parentWaitWrote -and (Get-Process -Id $parentWaitReaperProcess.Id -ErrorAction SilentlyContinue)) {
                Stop-TestProcessTree $parentWaitReaperProcess.Id
            }
        }
        finally {
            $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS = $previousR7ReaperTimeout
        }
    }
    finally {
        if (Get-Process -Id $parentWaitAliveParent.Id -ErrorAction SilentlyContinue) {
            Stop-TestProcessTree $parentWaitAliveParent.Id
        }
    }

    $parentWaitRecord = Read-JsonFile -Path $parentWaitResult
    Assert-True -Actual ($null -ne $parentWaitRecord) -Message 'The parent-shell-wait scenario did not write a result record.'
    Assert-Equal -Expected 'timeout' -Actual $parentWaitRecord.status -Message 'The reaper did not wait for the parent shell pid before timing out.'
    Assert-True -Actual (Test-Path -LiteralPath $parentWaitWorktree) -Message 'The worktree was removed despite the parent shell still running.'

    Write-Output 'PASS finish.tests.ps1: reaper waits for the parent shell pid too'


    $caseLookupRoot = Join-Path $scratch 'r8-case-insensitive-receipt'
    New-Item -ItemType Directory -Path $caseLookupRoot -Force | Out-Null
    $caseLookupState = Join-Path $caseLookupRoot 'state'
    $caseLookupTarget = Join-Path $caseLookupRoot 'Case-Target'
    New-Item -ItemType Directory -Path $caseLookupTarget -Force | Out-Null
    $caseLookupResolved = Get-ResolvedPath $caseLookupTarget
    $caseLookupDummySource = Join-Path $caseLookupRoot 'dummy-source'
    New-Item -ItemType Directory -Path $caseLookupDummySource -Force | Out-Null

    $caseLookupReceiptPath = Join-Path $caseLookupState 'merge-cleanup\receipts\mixed-case-receipt.json'
    Write-JsonFile -Path $caseLookupReceiptPath -Data @{
        worktree    = $caseLookupResolved.ToUpperInvariant()
        primary     = $scratch
        branch      = 'feature'
        head        = ('a' * 40)
        pr          = 1
        merge_oid   = ('b' * 40)
        default     = 'main'
        verdict     = 'removable'
        recorded_at = ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
    }

    $caseLookupFound = & {
        try { . $finishScript -Worktree $caseLookupDummySource } catch { }
        Find-ReceiptPath -StateDirectory $caseLookupState -ResolvedWorktree $caseLookupResolved
    }
    Assert-Equal -Expected $caseLookupReceiptPath -Actual $caseLookupFound -Message 'A receipt whose recorded worktree differs only in case was not found by Find-ReceiptPath.'

    Write-Output 'PASS finish.tests.ps1: case-insensitive receipt lookup'


    $siblingRoot = Join-Path $scratch 'r12-prefix-sibling'
    New-Item -ItemType Directory -Path $siblingRoot -Force | Out-Null
    $siblingState = Join-Path $siblingRoot 'state'
    $siblingRepo = New-TestRepo -Root $siblingRoot
    $siblingWorktree = Add-FeatureWorktree -Primary $siblingRepo.Primary -Root $siblingRoot -Branch 'feature'
    $siblingResolved = Get-ResolvedPath $siblingWorktree
    $siblingHead = (Invoke-GitOrThrow -Cwd $siblingWorktree -Arguments @('rev-parse', 'HEAD')).Trim()

    Invoke-GitOrThrow -Cwd $siblingRepo.Primary -Arguments @('branch', 'feature-sibling', 'main') | Out-Null
    $siblingSiblingWorktree = $siblingWorktree + '-sibling'
    Invoke-GitOrThrow -Cwd $siblingRepo.Primary -Arguments @('worktree', 'add', '-q', $siblingSiblingWorktree, 'feature-sibling') | Out-Null

    $siblingResult = Join-Path $siblingRoot 'result.json'
    $siblingDeadHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $siblingDeadHost.WaitForExit(5000) | Out-Null
    $siblingDeadStart = ([DateTimeOffset]($siblingDeadHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

    $siblingReaperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $reaperScript,
        '-HostPid', $siblingDeadHost.Id, '-HostStart', $siblingDeadStart,
        '-Head', $siblingHead,
        '-Primary', $siblingRepo.Primary, '-Worktree', $siblingResolved,
        '-Branch', 'feature', '-Default', 'main', '-Result', $siblingResult,
        '-StateDirectory', $siblingState
    ) -PassThru -WindowStyle Hidden

    $siblingWrote = Wait-Condition -TimeoutSeconds 60 -Condition {
        $record = Read-JsonFile -Path $siblingResult
        $null -ne $record -and $null -ne $record.status
    }
    if (-not $siblingWrote -and (Get-Process -Id $siblingReaperProcess.Id -ErrorAction SilentlyContinue)) {
        Stop-TestProcessTree $siblingReaperProcess.Id
    }

    $siblingRecord = Read-JsonFile -Path $siblingResult
    Assert-True -Actual ($null -ne $siblingRecord) -Message 'The prefix-sibling scenario did not write a result record.'
    Assert-Equal -Expected 'succeeded' -Actual $siblingRecord.status -Message 'A prefix-sharing sibling worktree made the registration check misread the removed target as still registered.'

    Write-Output 'PASS finish.tests.ps1: exact worktree registration check ignores a prefix-sharing sibling'


    $tabJsonRoot = Join-Path $scratch 'r14-tab-json-parse'
    New-Item -ItemType Directory -Path $tabJsonRoot -Force | Out-Null
    $tabJsonState = Join-Path $tabJsonRoot 'state'
    $tabJsonDummySource = Join-Path $tabJsonRoot 'dummy-source'
    New-Item -ItemType Directory -Path $tabJsonDummySource -Force | Out-Null

    $tabJsonSampleJson = (ConvertTo-Json -InputObject @(
        [pscustomobject]@{ title = 'mine'; live = $true; terminalId = 111 },
        [pscustomobject]@{ title = 'peer-tab'; live = $true; terminalId = 222 }
    ) -Depth 4)
    $tabJsonDuplicateJson = (ConvertTo-Json -InputObject @(
        [pscustomobject]@{ title = 'mine'; live = $true; terminalId = 111 },
        [pscustomobject]@{ title = 'mine'; live = $true; terminalId = 333 }
    ) -Depth 4)

    $previousR14State = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $tabJsonState
    try {
        $tabJsonSingleMatch = & {
            try { . $finishScript -Worktree $tabJsonDummySource } catch { }
            Test-SingleLiveTabInListing -Tabs (ConvertFrom-TabListingJson -Text $tabJsonSampleJson) -Title 'mine'
        }
        $tabJsonNoMatch = & {
            try { . $finishScript -Worktree $tabJsonDummySource } catch { }
            Test-SingleLiveTabInListing -Tabs (ConvertFrom-TabListingJson -Text $tabJsonSampleJson) -Title 'missing'
        }
        $tabJsonDuplicateMatch = & {
            try { . $finishScript -Worktree $tabJsonDummySource } catch { }
            Test-SingleLiveTabInListing -Tabs (ConvertFrom-TabListingJson -Text $tabJsonDuplicateJson) -Title 'mine'
        }
        $tabJsonEmptyCount = & {
            try { . $finishScript -Worktree $tabJsonDummySource } catch { }
            @(ConvertFrom-TabListingJson -Text '[]').Count
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousR14State
    }
    Assert-True -Actual $tabJsonSingleMatch -Message 'A title appearing exactly once in sample close-tab.ps1 -Json output was not recognized as a single live tab.'
    Assert-False -Actual $tabJsonNoMatch -Message 'A title absent from sample close-tab.ps1 -Json output was wrongly recognized as a single live tab.'
    Assert-False -Actual $tabJsonDuplicateMatch -Message 'A title appearing twice in sample close-tab.ps1 -Json output was wrongly recognized as a single live tab.'
    Assert-Equal -Expected 0 -Actual $tabJsonEmptyCount -Message 'An empty close-tab.ps1 -Json array did not parse to zero tabs.'

    Write-Output 'PASS finish.tests.ps1: tab-uniqueness check parses close-tab.ps1 -Json output'


    $wrapperRoot = Join-Path $scratch 'r15-wrapper-shell'
    New-Item -ItemType Directory -Path $wrapperRoot -Force | Out-Null
    $wrapperState = Join-Path $wrapperRoot 'state'
    $wrapperDummySource = Join-Path $wrapperRoot 'dummy-source'
    New-Item -ItemType Directory -Path $wrapperDummySource -Force | Out-Null

    $wrapperHostPid = 61001
    $wrapperParentPid = 61002
    $wrapperOtherChildPid = 61003
    $wrapperHostCreation = (Get-Date).ToUniversalTime()
    $wrapperOwnHostFake = [pscustomobject]@{ Pid = $wrapperHostPid; Started = ([DateTimeOffset] $wrapperHostCreation).ToUnixTimeMilliseconds() / 1000.0 }

    $previousR15State = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $wrapperState
    try {
        $wrapperSecondChildResult = & {
            try { . $finishScript -Worktree $wrapperDummySource } catch { }
            $hostProcess = [pscustomobject]@{ ProcessId = $wrapperHostPid; ParentProcessId = $wrapperParentPid; Name = 'codex.exe'; CreationDate = $wrapperHostCreation }
            $parentProcess = [pscustomobject]@{ ProcessId = $wrapperParentPid; ParentProcessId = 1; Name = 'cmd.exe'; CreationDate = $wrapperHostCreation.AddSeconds(-2) }
            $children = @(
                [pscustomobject]@{ ProcessId = $wrapperHostPid; ParentProcessId = $wrapperParentPid; Name = 'codex.exe' },
                [pscustomobject]@{ ProcessId = $wrapperOtherChildPid; ParentProcessId = $wrapperParentPid; Name = 'notepad.exe' }
            )
            function Get-CimInstance {
                param([string] $ClassName, [string] $Filter, $ErrorAction)
                if ($Filter -match 'ParentProcessId\s*=\s*(\d+)') {
                    if ([int] $Matches[1] -eq $parentProcess.ProcessId) { return $children }
                    return @()
                }
                if ($Filter -match 'ProcessId\s*=\s*(\d+)') {
                    $target = [int] $Matches[1]
                    if ($target -eq $hostProcess.ProcessId) { return $hostProcess }
                    if ($target -eq $parentProcess.ProcessId) { return $parentProcess }
                    return $null
                }
                return $null
            }
            Get-ParentShellHost -OwnHost $wrapperOwnHostFake
        }

        $wrapperStaleTimingResult = & {
            try { . $finishScript -Worktree $wrapperDummySource } catch { }
            $hostProcess = [pscustomobject]@{ ProcessId = $wrapperHostPid; ParentProcessId = $wrapperParentPid; Name = 'codex.exe'; CreationDate = $wrapperHostCreation }
            $parentProcess = [pscustomobject]@{ ProcessId = $wrapperParentPid; ParentProcessId = 1; Name = 'cmd.exe'; CreationDate = $wrapperHostCreation.AddSeconds(-15) }
            $children = @([pscustomobject]@{ ProcessId = $wrapperHostPid; ParentProcessId = $wrapperParentPid; Name = 'codex.exe' })
            function Get-CimInstance {
                param([string] $ClassName, [string] $Filter, $ErrorAction)
                if ($Filter -match 'ParentProcessId\s*=\s*(\d+)') {
                    if ([int] $Matches[1] -eq $parentProcess.ProcessId) { return $children }
                    return @()
                }
                if ($Filter -match 'ProcessId\s*=\s*(\d+)') {
                    $target = [int] $Matches[1]
                    if ($target -eq $hostProcess.ProcessId) { return $hostProcess }
                    if ($target -eq $parentProcess.ProcessId) { return $parentProcess }
                    return $null
                }
                return $null
            }
            Get-ParentShellHost -OwnHost $wrapperOwnHostFake
        }

        $wrapperQualifiedResult = & {
            try { . $finishScript -Worktree $wrapperDummySource } catch { }
            $hostProcess = [pscustomobject]@{ ProcessId = $wrapperHostPid; ParentProcessId = $wrapperParentPid; Name = 'codex.exe'; CreationDate = $wrapperHostCreation }
            $parentProcess = [pscustomobject]@{ ProcessId = $wrapperParentPid; ParentProcessId = 1; Name = 'cmd.exe'; CreationDate = $wrapperHostCreation.AddSeconds(-2) }
            $children = @(
                [pscustomobject]@{ ProcessId = $wrapperHostPid; ParentProcessId = $wrapperParentPid; Name = 'codex.exe' },
                [pscustomobject]@{ ProcessId = ($wrapperHostPid + 1); ParentProcessId = $wrapperParentPid; Name = 'conhost.exe' }
            )
            function Get-CimInstance {
                param([string] $ClassName, [string] $Filter, $ErrorAction)
                if ($Filter -match 'ParentProcessId\s*=\s*(\d+)') {
                    if ([int] $Matches[1] -eq $parentProcess.ProcessId) { return $children }
                    return @()
                }
                if ($Filter -match 'ProcessId\s*=\s*(\d+)') {
                    $target = [int] $Matches[1]
                    if ($target -eq $hostProcess.ProcessId) { return $hostProcess }
                    if ($target -eq $parentProcess.ProcessId) { return $parentProcess }
                    return $null
                }
                return $null
            }
            Get-ParentShellHost -OwnHost $wrapperOwnHostFake
        }

        $wrapperStopOrder = & {
            try { . $finishScript -Worktree $wrapperDummySource } catch { }
            $order = New-Object System.Collections.Generic.List[int]
            function Stop-VerifiedProcess {
                param([pscustomobject] $Target)
                $order.Add($Target.Pid)
            }
            Stop-WrapperThenHost -OwnHost ([pscustomobject]@{ Pid = 71001; Started = 1700001000.0 }) `
                -ParentShell ([pscustomobject]@{ Pid = 71002; Started = 1700000998.0 })
            $order
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousR15State
    }

    Assert-True -Actual ($null -eq $wrapperSecondChildResult) -Message 'A shell with a second unrelated live child was wrongly selected as the wrapper shell.'
    Assert-True -Actual ($null -eq $wrapperStaleTimingResult) -Message 'A shell that started more than 10 seconds before the host was wrongly selected as the wrapper shell.'
    Assert-True -Actual ($null -ne $wrapperQualifiedResult) -Message 'A shell started shortly before the host, with no other live children, was not selected as the wrapper shell.'
    Assert-Equal -Expected $wrapperParentPid -Actual $wrapperQualifiedResult.Pid -Message 'The selected wrapper shell did not carry the parent pid.'
    Assert-Equal -Expected 2 -Actual (@($wrapperStopOrder).Count) -Message 'Stop-WrapperThenHost did not stop exactly two processes.'
    Assert-Equal -Expected 71002 -Actual (@($wrapperStopOrder))[0] -Message 'Stop-WrapperThenHost did not stop the wrapper shell before the host.'
    Assert-Equal -Expected 71001 -Actual (@($wrapperStopOrder))[1] -Message 'Stop-WrapperThenHost did not stop the host after the wrapper shell.'

    Write-Output 'PASS finish.tests.ps1: wrapper shell qualification requires timing and exclusive children; stops before the host'


    $claimRoot = Join-Path $scratch 'r19-other-live-claim'
    New-Item -ItemType Directory -Path $claimRoot -Force | Out-Null
    $claimState = Join-Path $claimRoot 'state'
    New-Item -ItemType Directory -Path (Join-Path $claimState 'cli-sessions') -Force | Out-Null
    $claimWorktree = Join-Path $claimRoot 'worktree'
    New-Item -ItemType Directory -Path $claimWorktree -Force | Out-Null
    $claimResolved = Get-ResolvedPath $claimWorktree
    $claimDummySource = Join-Path $claimRoot 'dummy-source'
    New-Item -ItemType Directory -Path $claimDummySource -Force | Out-Null
    $claimOwnHostFake = [pscustomobject]@{ Pid = 345678; Started = 1700000900.0 }

    $claimOtherProcess = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'ping -n 60 127.0.0.1 > nul' -PassThru -WindowStyle Hidden
    try {
        $claimOtherStart = ([DateTimeOffset]($claimOtherProcess.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0
        Write-JsonFile -Path (Join-Path $claimState 'cli-sessions\other-live.json') -Data @{
            session_id = 'other-live'; title = 'other'; cwd = $claimResolved
            pid = $claimOtherProcess.Id; pid_started_at = $claimOtherStart
        }

        $previousR19State = $env:AGENT_STATE_DIRECTORY
        $env:AGENT_STATE_DIRECTORY = $claimState
        try {
            $claimClaimed = & {
                try { . $finishScript -Worktree $claimDummySource } catch { }
                Test-OtherLiveSessionClaimsWorktree -ResolvedWorktree $claimResolved -OwnHost $claimOwnHostFake
            }
        }
        finally {
            $env:AGENT_STATE_DIRECTORY = $previousR19State
        }
        Assert-True -Actual $claimClaimed -Message 'A verified-live other registered session with a cwd under the worktree did not block the self-close.'
    }
    finally {
        if (Get-Process -Id $claimOtherProcess.Id -ErrorAction SilentlyContinue) {
            Stop-TestProcessTree $claimOtherProcess.Id
        }
    }

    $claimDeadOtherProcess = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $claimDeadOtherProcess.WaitForExit(5000) | Out-Null
    $claimDeadOtherStart = ([DateTimeOffset]($claimDeadOtherProcess.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0
    Write-JsonFile -Path (Join-Path $claimState 'cli-sessions\other-dead.json') -Data @{
        session_id = 'other-dead'; title = 'other-dead'; cwd = $claimResolved
        pid = $claimDeadOtherProcess.Id; pid_started_at = $claimDeadOtherStart
    }
    Remove-Item -LiteralPath (Join-Path $claimState 'cli-sessions\other-live.json') -Force -ErrorAction SilentlyContinue
    $previousR19DeadState = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $claimState
    try {
        $claimNotClaimed = & {
            try { . $finishScript -Worktree $claimDummySource } catch { }
            Test-OtherLiveSessionClaimsWorktree -ResolvedWorktree $claimResolved -OwnHost $claimOwnHostFake
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousR19DeadState
    }
    Assert-False -Actual $claimNotClaimed -Message 'A registered session whose process has exited still blocked the self-close.'

    Write-Output 'PASS finish.tests.ps1: refuses when another live registered session claims the worktree'


    $duplicateRoot = Join-Path $scratch 'r21-duplicate-obligations'
    New-Item -ItemType Directory -Path $duplicateRoot -Force | Out-Null
    $duplicateState = Join-Path $duplicateRoot 'state'
    $duplicateRepo = New-TestRepo -Root $duplicateRoot
    $duplicateWorktree = Add-FeatureWorktree -Primary $duplicateRepo.Primary -Root $duplicateRoot -Branch 'feature'
    $duplicateResolved = Get-ResolvedPath $duplicateWorktree
    $duplicateHead = (Invoke-GitOrThrow -Cwd $duplicateWorktree -Arguments @('rev-parse', 'HEAD')).Trim()

    $duplicateObligationsDirectory = Join-Path $duplicateState 'merge-cleanup\obligations'
    New-Item -ItemType Directory -Path $duplicateObligationsDirectory -Force | Out-Null
    $duplicateObligationA = Join-Path $duplicateObligationsDirectory 'a.json'
    $duplicateObligationB = Join-Path $duplicateObligationsDirectory 'b.json'
    Write-JsonFile -Path $duplicateObligationA -Data @{ session_id = 'a'; worktree = $duplicateResolved; branch = 'feature'; pr = 1 }
    Write-JsonFile -Path $duplicateObligationB -Data @{ session_id = 'b'; worktree = $duplicateResolved.ToUpperInvariant(); branch = 'feature'; pr = 1 }

    $duplicateResult = Join-Path $duplicateRoot 'result.json'
    $duplicateDeadHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $duplicateDeadHost.WaitForExit(5000) | Out-Null
    $duplicateDeadStart = ([DateTimeOffset]($duplicateDeadHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

    $duplicateReaperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $reaperScript,
        '-HostPid', $duplicateDeadHost.Id, '-HostStart', $duplicateDeadStart,
        '-Head', $duplicateHead,
        '-Primary', $duplicateRepo.Primary, '-Worktree', $duplicateResolved,
        '-Branch', 'feature', '-Default', 'main', '-Result', $duplicateResult,
        '-StateDirectory', $duplicateState
    ) -PassThru -WindowStyle Hidden

    $duplicateWrote = Wait-Condition -TimeoutSeconds 60 -Condition {
        $record = Read-JsonFile -Path $duplicateResult
        $null -ne $record -and $null -ne $record.status
    }
    if (-not $duplicateWrote -and (Get-Process -Id $duplicateReaperProcess.Id -ErrorAction SilentlyContinue)) {
        Stop-TestProcessTree $duplicateReaperProcess.Id
    }

    $duplicateRecord = Read-JsonFile -Path $duplicateResult
    Assert-True -Actual ($null -ne $duplicateRecord) -Message 'The duplicate-obligations scenario did not write a result record.'
    Assert-Equal -Expected 'succeeded' -Actual $duplicateRecord.status -Message 'The duplicate-obligations cleanup did not succeed.'
    $duplicateClearedA = Wait-Condition -TimeoutSeconds 10 -Condition { -not (Test-Path -LiteralPath $duplicateObligationA) }
    $duplicateClearedB = Wait-Condition -TimeoutSeconds 10 -Condition { -not (Test-Path -LiteralPath $duplicateObligationB) }
    Assert-True -Actual $duplicateClearedA -Message 'The reaper left the first matching obligation file in place.'
    Assert-True -Actual $duplicateClearedB -Message 'The reaper left a duplicate matching obligation file (under another path spelling) in place.'

    Write-Output 'PASS finish.tests.ps1: reaper removes every matching obligation file'
}
finally {
    $env:AGENT_STATE_DIRECTORY = $originalState
    $env:AGENT_CLI_HOST_NAMES = $originalHostNames
    $env:AGENT_FINISH_CLOSE_MODE = $originalCloseMode
    $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS = $originalReaperTimeout
    $env:CLEANUP_PROOF_FORGE_FIXTURE = $originalFixture
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force -ErrorAction SilentlyContinue }
}

Write-Output 'PASS finish.tests.ps1'
