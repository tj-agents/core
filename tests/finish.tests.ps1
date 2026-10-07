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
        # A real `cmd.exe` wraps the fake host, standing in for the interactive shell a real tab runs under
        # (register_session.py's own ancestor walk expects one): finish.ps1's R7 stop-process path stops that
        # parent shell too, which would otherwise be this test runner's own process.
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

    # --- (v) R1: a commit after the receipt makes finish refuse, and the reaper preserves a moved branch --

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

    $r1Root = Join-Path $scratch 'r1-branch-preserve'
    New-Item -ItemType Directory -Path $r1Root -Force | Out-Null
    $r1State = Join-Path $r1Root 'state'
    $r1Repo = New-TestRepo -Root $r1Root
    $r1Worktree = Add-FeatureWorktree -Primary $r1Repo.Primary -Root $r1Root -Branch 'feature'
    $r1Resolved = Get-ResolvedPath $r1Worktree
    $r1Head = (Invoke-GitOrThrow -Cwd $r1Worktree -Arguments @('rev-parse', 'HEAD')).Trim()

    # A commit lands on the branch (e.g. from elsewhere sharing the repository) after the head above was
    # proven: same tree as $r1Head, so the worktree's own files stay clean, but a different commit id.
    $r1Tree = (Invoke-GitOrThrow -Cwd $r1Repo.Primary -Arguments @('rev-parse', "$r1Head^{tree}")).Trim()
    $r1LateCommit = (Invoke-GitOrThrow -Cwd $r1Repo.Primary -Arguments @('commit-tree', $r1Tree, '-p', $r1Head, '-m', 'late commit')).Trim()
    Invoke-GitOrThrow -Cwd $r1Repo.Primary -Arguments @('update-ref', 'refs/heads/feature', $r1LateCommit) | Out-Null

    $r1Result = Join-Path $r1Root 'result.json'
    $r1DeadHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $r1DeadHost.WaitForExit(5000) | Out-Null
    $r1DeadStart = ([DateTimeOffset]($r1DeadHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

    $r1ReaperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $reaperScript,
        '-HostPid', $r1DeadHost.Id, '-HostStart', $r1DeadStart,
        '-Head', $r1Head,
        '-Primary', $r1Repo.Primary, '-Worktree', $r1Resolved,
        '-Branch', 'feature', '-Default', 'main', '-Result', $r1Result,
        '-StateDirectory', $r1State
    ) -PassThru -WindowStyle Hidden

    $r1Wrote = Wait-Condition -TimeoutSeconds 30 -Condition {
        $record = Read-JsonFile -Path $r1Result
        $null -ne $record -and $null -ne $record.status
    }
    if (-not $r1Wrote -and (Get-Process -Id $r1ReaperProcess.Id -ErrorAction SilentlyContinue)) {
        & taskkill.exe /PID $r1ReaperProcess.Id /T /F 2>$null | Out-Null
    }

    $r1Record = Read-JsonFile -Path $r1Result
    Assert-True -Actual ($null -ne $r1Record) -Message 'The branch-preserve scenario did not write a result record.'
    Assert-Equal -Expected 'branch-preserved' -Actual $r1Record.status -Message 'The reaper did not preserve a branch whose tip moved after the receipt head.'
    Assert-True -Actual (-not (Test-Path -LiteralPath $r1Worktree)) -Message 'The worktree was not removed even though only the branch should be preserved.'
    $r1BranchStillPresent = $(& git -C $r1Repo.Primary show-ref --verify --quiet refs/heads/feature; $LASTEXITCODE -eq 0)
    Assert-True -Actual $r1BranchStillPresent -Message 'The moved branch was deleted despite its tip no longer matching the receipt head.'

    Write-Output 'PASS finish.tests.ps1: R1 head-must-match-receipt'

    # --- (vi) R3: a peer registry entry in the same worktree with a different title is never chosen ------

    $r3Root = Join-Path $scratch 'r3-peer-title'
    New-Item -ItemType Directory -Path $r3Root -Force | Out-Null
    $r3State = Join-Path $r3Root 'state'
    New-Item -ItemType Directory -Path (Join-Path $r3State 'cli-sessions') -Force | Out-Null
    $r3Worktree = Join-Path $r3Root 'worktree'
    New-Item -ItemType Directory -Path $r3Worktree -Force | Out-Null
    $r3Resolved = Get-ResolvedPath $r3Worktree
    $r3DummySource = Join-Path $r3Root 'dummy-source'
    New-Item -ItemType Directory -Path $r3DummySource -Force | Out-Null

    $ownHostFake = [pscustomobject]@{ Pid = 123456; Started = 1700000000.125 }
    Write-JsonFile -Path (Join-Path $r3State 'cli-sessions\own.json') -Data @{
        session_id = 'own'; title = 'mine'; cwd = $r3Resolved; pid = $ownHostFake.Pid; pid_started_at = $ownHostFake.Started
    }
    Write-JsonFile -Path (Join-Path $r3State 'cli-sessions\peer.json') -Data @{
        session_id = 'peer'; title = 'peer-tab'; cwd = $r3Resolved; pid = 987654; pid_started_at = 1600000000.0
    }

    $previousR3State = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $r3State
    try {
        $r3Attachment = & {
            try { . $finishScript -Worktree $r3DummySource } catch { }
            Get-TitleAndAttachment -ResolvedWorktree $r3Resolved -StartingLocation $r3Resolved -OwnHost $ownHostFake
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousR3State
    }
    Assert-Equal -Expected 'mine' -Actual $r3Attachment.Title -Message "The tab title came from a peer's registry entry instead of this session's own one."
    Assert-True -Actual $r3Attachment.Attached -Message "This session's own registry entry, with a cwd under the worktree, was not recognized as attached."

    $r3OutsideState = Join-Path $r3Root 'state-outside'
    New-Item -ItemType Directory -Path (Join-Path $r3OutsideState 'cli-sessions') -Force | Out-Null
    $r3OutsideCwd = Join-Path $r3Root 'outside-cwd'
    New-Item -ItemType Directory -Path $r3OutsideCwd -Force | Out-Null
    Write-JsonFile -Path (Join-Path $r3OutsideState 'cli-sessions\own-outside.json') -Data @{
        session_id = 'own-outside'; title = 'mine-outside'; cwd = (Get-ResolvedPath $r3OutsideCwd)
        pid = $ownHostFake.Pid; pid_started_at = $ownHostFake.Started
    }
    $previousR3OutsideState = $env:AGENT_STATE_DIRECTORY
    $env:AGENT_STATE_DIRECTORY = $r3OutsideState
    try {
        $r3OutsideAttachment = & {
            try { . $finishScript -Worktree $r3DummySource } catch { }
            Get-TitleAndAttachment -ResolvedWorktree $r3Resolved -StartingLocation $r3Resolved -OwnHost $ownHostFake
        }
    }
    finally {
        $env:AGENT_STATE_DIRECTORY = $previousR3OutsideState
    }
    Assert-False -Actual $r3OutsideAttachment.Attached -Message "A self registry entry whose cwd is outside the worktree was wrongly treated as attached via `$PWD."

    Write-Output 'PASS finish.tests.ps1: R3 own-entry-only tab title'

    # --- (vii) R7: the reaper waits for the parent shell pid too, not only the host pid -------------------

    $r7Root = Join-Path $scratch 'r7-parent-wait'
    New-Item -ItemType Directory -Path $r7Root -Force | Out-Null
    $r7Repo = New-TestRepo -Root $r7Root
    $r7Worktree = Add-FeatureWorktree -Primary $r7Repo.Primary -Root $r7Root -Branch 'feature'
    $r7Resolved = Get-ResolvedPath $r7Worktree
    $r7Head = (Invoke-GitOrThrow -Cwd $r7Worktree -Arguments @('rev-parse', 'HEAD')).Trim()
    $r7Result = Join-Path $r7Root 'result.json'
    $r7State = Join-Path $r7Root 'state'

    $r7DeadHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $r7DeadHost.WaitForExit(5000) | Out-Null
    $r7DeadStart = ([DateTimeOffset]($r7DeadHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

    $r7AliveParent = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'ping -n 60 127.0.0.1 > nul' -PassThru -WindowStyle Hidden
    try {
        $r7AliveStart = ([DateTimeOffset]($r7AliveParent.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

        $previousR7ReaperTimeout = $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS
        $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS = '2'
        $r7ReaperProcess = $null
        try {
            $r7ReaperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
                '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $reaperScript,
                '-HostPid', $r7DeadHost.Id, '-HostStart', $r7DeadStart,
                '-ParentPid', $r7AliveParent.Id, '-ParentStart', $r7AliveStart,
                '-Head', $r7Head,
                '-Primary', $r7Repo.Primary, '-Worktree', $r7Resolved,
                '-Branch', 'feature', '-Default', 'main', '-Result', $r7Result,
                '-StateDirectory', $r7State
            ) -PassThru -WindowStyle Hidden

            $r7Wrote = Wait-Condition -TimeoutSeconds 30 -Condition {
                $record = Read-JsonFile -Path $r7Result
                $null -ne $record -and $null -ne $record.status
            }
            if (-not $r7Wrote -and (Get-Process -Id $r7ReaperProcess.Id -ErrorAction SilentlyContinue)) {
                & taskkill.exe /PID $r7ReaperProcess.Id /T /F 2>$null | Out-Null
            }
        }
        finally {
            $env:AGENT_FINISH_REAPER_TIMEOUT_SECONDS = $previousR7ReaperTimeout
        }
    }
    finally {
        if (Get-Process -Id $r7AliveParent.Id -ErrorAction SilentlyContinue) {
            & taskkill.exe /PID $r7AliveParent.Id /T /F 2>$null | Out-Null
        }
    }

    $r7Record = Read-JsonFile -Path $r7Result
    Assert-True -Actual ($null -ne $r7Record) -Message 'The parent-shell-wait scenario did not write a result record.'
    Assert-Equal -Expected 'timeout' -Actual $r7Record.status -Message 'The reaper did not wait for the parent shell pid before timing out.'
    Assert-True -Actual (Test-Path -LiteralPath $r7Worktree) -Message 'The worktree was removed despite the parent shell still running.'

    Write-Output 'PASS finish.tests.ps1: R7 parent-shell wait'

    # --- (viii) R8: a receipt is found when its worktree field differs only in case ------------------------

    $r8Root = Join-Path $scratch 'r8-case-insensitive-receipt'
    New-Item -ItemType Directory -Path $r8Root -Force | Out-Null
    $r8State = Join-Path $r8Root 'state'
    $r8Target = Join-Path $r8Root 'Case-Target'
    New-Item -ItemType Directory -Path $r8Target -Force | Out-Null
    $r8Resolved = Get-ResolvedPath $r8Target
    $r8DummySource = Join-Path $r8Root 'dummy-source'
    New-Item -ItemType Directory -Path $r8DummySource -Force | Out-Null

    $r8ReceiptPath = Join-Path $r8State 'merge-cleanup\receipts\mixed-case-receipt.json'
    Write-JsonFile -Path $r8ReceiptPath -Data @{
        worktree    = $r8Resolved.ToUpperInvariant()
        primary     = $scratch
        branch      = 'feature'
        head        = ('a' * 40)
        pr          = 1
        merge_oid   = ('b' * 40)
        default     = 'main'
        verdict     = 'removable'
        recorded_at = ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
    }

    $r8Found = & {
        try { . $finishScript -Worktree $r8DummySource } catch { }
        Find-ReceiptPath -StateDirectory $r8State -ResolvedWorktree $r8Resolved
    }
    Assert-Equal -Expected $r8ReceiptPath -Actual $r8Found -Message 'A receipt whose recorded worktree differs only in case was not found by Find-ReceiptPath.'

    Write-Output 'PASS finish.tests.ps1: R8 case-insensitive receipt lookup'

    # --- (ix) R12: a prefix-sharing sibling worktree does not defeat the exact registration check -----------

    $r12Root = Join-Path $scratch 'r12-prefix-sibling'
    New-Item -ItemType Directory -Path $r12Root -Force | Out-Null
    $r12State = Join-Path $r12Root 'state'
    $r12Repo = New-TestRepo -Root $r12Root
    $r12Worktree = Add-FeatureWorktree -Primary $r12Repo.Primary -Root $r12Root -Branch 'feature'
    $r12Resolved = Get-ResolvedPath $r12Worktree
    $r12Head = (Invoke-GitOrThrow -Cwd $r12Worktree -Arguments @('rev-parse', 'HEAD')).Trim()

    # A sibling worktree whose path is a superstring of the target's, so a substring match on porcelain
    # output would misread the target as still registered after it is actually removed.
    Invoke-GitOrThrow -Cwd $r12Repo.Primary -Arguments @('branch', 'feature-sibling', 'main') | Out-Null
    $r12SiblingWorktree = $r12Worktree + '-sibling'
    Invoke-GitOrThrow -Cwd $r12Repo.Primary -Arguments @('worktree', 'add', '-q', $r12SiblingWorktree, 'feature-sibling') | Out-Null

    $r12Result = Join-Path $r12Root 'result.json'
    $r12DeadHost = Start-Process -FilePath $env:ComSpec -ArgumentList '/c', 'exit 0' -PassThru -WindowStyle Hidden
    $r12DeadHost.WaitForExit(5000) | Out-Null
    $r12DeadStart = ([DateTimeOffset]($r12DeadHost.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0

    $r12ReaperProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $reaperScript,
        '-HostPid', $r12DeadHost.Id, '-HostStart', $r12DeadStart,
        '-Head', $r12Head,
        '-Primary', $r12Repo.Primary, '-Worktree', $r12Resolved,
        '-Branch', 'feature', '-Default', 'main', '-Result', $r12Result,
        '-StateDirectory', $r12State
    ) -PassThru -WindowStyle Hidden

    $r12Wrote = Wait-Condition -TimeoutSeconds 60 -Condition {
        $record = Read-JsonFile -Path $r12Result
        $null -ne $record -and $null -ne $record.status
    }
    if (-not $r12Wrote -and (Get-Process -Id $r12ReaperProcess.Id -ErrorAction SilentlyContinue)) {
        & taskkill.exe /PID $r12ReaperProcess.Id /T /F 2>$null | Out-Null
    }

    $r12Record = Read-JsonFile -Path $r12Result
    Assert-True -Actual ($null -ne $r12Record) -Message 'The prefix-sibling scenario did not write a result record.'
    Assert-Equal -Expected 'succeeded' -Actual $r12Record.status -Message 'A prefix-sharing sibling worktree made the registration check misread the removed target as still registered.'

    Write-Output 'PASS finish.tests.ps1: R12 exact registration check'
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
