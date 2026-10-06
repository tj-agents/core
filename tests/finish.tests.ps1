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
            & taskkill.exe /PID $process.Id /T /F 2>$null | Out-Null
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

    # --- (iv) Preflight refusals -------------------------------------------------------------------

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
    $unattachedResolved = Get-ResolvedPath $unattachedTarget
    Write-JsonFile -Path (Get-ReceiptPath -StateDirectory $preflightState -ResolvedWorktree $unattachedResolved) -Data @{
        worktree = $unattachedResolved; primary = $scratch; branch = 'feature'; head = ('a' * 40); pr = 1
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
            & taskkill.exe /PID $unattachedProcess.Id /T /F 2>$null | Out-Null
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

    # --- (i) Job-breakaway proof ---------------------------------------------------------------------

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
    '-HostPid', $DeadPid, '-HostStart', $DeadStart, '-Primary', $DummyPrimary, '-Worktree', $DummyWorktree,
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
            & taskkill.exe /PID $childProcess.Id /T /F 2>$null | Out-Null
        }
        Get-Process -Name 'powershell' -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -and $_.Path -eq (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') } |
            Where-Object {
                try { (Get-CimInstance -ClassName Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like "*$reaperScript*" } catch { $false }
            } | ForEach-Object {
                try { & taskkill.exe /PID $_.Id /T /F 2>$null | Out-Null } catch { }
            }
    }

    Write-Output 'PASS finish.tests.ps1: job-breakaway proof'

    # --- (ii) End-to-end squash-merge cleanup --------------------------------------------------------

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
        # The documented invocation: no arguments, run from inside the worktree, so the target comes from
        # `git rev-parse --show-toplevel` against the fake host's working directory, exactly as Step 5 runs it.
        $innerCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File $finishScript"
        $fakeHostProcess = Start-Process -FilePath $fakeCodex -ArgumentList @('/c', $innerCommand) `
            -WorkingDirectory $worktree -PassThru -WindowStyle Hidden

        $resultPath = Get-ResultRecordPath -StateDirectory $e2eState -ResolvedWorktree $worktreeResolved
        $succeeded = Wait-Condition -TimeoutSeconds 60 -Condition {
            $record = Read-JsonFile -Path $resultPath
            $null -ne $record -and $record.status -eq 'succeeded'
        }
        if (-not $succeeded) {
            $record = Read-JsonFile -Path $resultPath
            $detail = if ($record) { ($record | ConvertTo-Json -Compress) } else { '<no result file>' }
            throw "The end-to-end cleanup did not reach 'succeeded' in time. Last record: $detail"
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousE2eState
        $env:AGENT_FINISH_CLOSE_MODE = $previousCloseMode
        if ($fakeHostProcess -and (Get-Process -Id $fakeHostProcess.Id -ErrorAction SilentlyContinue)) {
            & taskkill.exe /PID $fakeHostProcess.Id /T /F 2>$null | Out-Null
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

    # --- (iii) Reaper timeout path --------------------------------------------------------------------

    $timeoutRoot = Join-Path $scratch 'timeout'
    New-Item -ItemType Directory -Path $timeoutRoot -Force | Out-Null
    $timeoutRepo = New-TestRepo -Root $timeoutRoot
    $timeoutWorktree = Add-FeatureWorktree -Primary $timeoutRepo.Primary -Root $timeoutRoot -Branch 'feature'
    $timeoutResolved = Get-ResolvedPath $timeoutWorktree
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
                '-Primary', $timeoutRepo.Primary, '-Worktree', $timeoutResolved,
                '-Branch', 'feature', '-Default', 'main', '-Result', $timeoutResult,
                '-StateDirectory', $timeoutState
            ) -PassThru -WindowStyle Hidden

            $wroteTimeoutRecord = Wait-Condition -TimeoutSeconds 60 -Condition {
                $record = Read-JsonFile -Path $timeoutResult
                $null -ne $record -and $null -ne $record.status
            }
            if (-not $wroteTimeoutRecord -and (Get-Process -Id $reaperProcess.Id -ErrorAction SilentlyContinue)) {
                & taskkill.exe /PID $reaperProcess.Id /T /F 2>$null | Out-Null
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
            & taskkill.exe /PID $aliveHost.Id /T /F 2>$null | Out-Null
        }
    }

    Write-Output 'PASS finish.tests.ps1: reaper timeout path'
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
