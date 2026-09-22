$ErrorActionPreference = 'Stop'

# End-to-end validation of the generated handoff launchers, per PACKAGING.md: neither must require a
# machine-local file this plugin does not ship. Runs against the actual generated package
# (plugins/machine/skills/...), from an isolated fake profile with no `.claude\routing\route.py` anywhere,
# an unrelated working directory, and paths containing spaces. Windows Terminal is stubbed so no real
# terminal window opens; a fake codex.exe is compiled so launch-codex.ps1's own version-discovery step
# (which executes candidates directly, not through the terminal) has something real to run.

$repository = Split-Path -Parent $PSScriptRoot
$claudeLauncher = Join-Path $repository 'plugins\machine\skills\handoff-claude\scripts\launch-claude.ps1'
$codexLauncher = Join-Path $repository 'plugins\machine\skills\handoff-codex\scripts\launch-codex.ps1'
$openLauncher = Join-Path $repository 'plugins\machine\skills\open-claude\scripts\open-claude.ps1'
$packagedLaunchers = @(Get-ChildItem -LiteralPath (Join-Path $repository 'plugins\machine\skills') -Recurse -File -Filter '*.ps1' |
    Where-Object { (Get-Content -LiteralPath $_.FullName -Raw) -match 'agent-cli\.ps1' } |
    Select-Object -ExpandProperty FullName)
$expectedLaunchers = @($claudeLauncher, $codexLauncher, $openLauncher) | Sort-Object
if (Compare-Object $expectedLaunchers ($packagedLaunchers | Sort-Object)) {
    throw 'The generated launcher dependency inventory changed; every agent-cli.ps1 consumer must be exercised or resolved here.'
}
foreach ($launcher in $packagedLaunchers) {
    if (-not (Test-Path -LiteralPath $launcher)) {
        throw "Generated launcher missing: $launcher. Run pwsh .agents/sync-generated.ps1."
    }
}

$scratch = Join-Path ([System.IO.Path]::GetTempPath()) "base-agents-handoff-$([guid]::NewGuid().ToString('N'))"
$fakeProfile = Join-Path $scratch 'fake profile'
$fakeLocalAppData = Join-Path $scratch 'fake local appdata'
$binDir = Join-Path $scratch 'stub bin'
$workDir = Join-Path $scratch 'unrelated repo (with spaces)'
$promptDir = Join-Path $scratch 'prompt files'
$wtLog = Join-Path $scratch 'wt-args.log'

$originalPath = $env:PATH
$originalUserProfile = $env:USERPROFILE
$originalLocalAppData = $env:LOCALAPPDATA
$originalWtLog = $env:WT_STUB_LOG

function New-Stub {
    param(
        [Parameter(Mandatory)][string] $CSharpSource,
        [Parameter(Mandatory)][string] $ExePath,
        [Parameter(Mandatory)][string] $BuildScratch
    )
    # pwsh's own CodeDom provider cannot emit an OutputType of ConsoleApplication ("not currently
    # supported"), so the tiny stub .exe is compiled by the Desktop CLR's Add-Type instead - the same
    # `powershell` the repo's own CI already relies on for cli-session-recovery tests.
    $sourcePath = Join-Path $BuildScratch ([System.IO.Path]::GetRandomFileName() + '.cs')
    [System.IO.File]::WriteAllText($sourcePath, $CSharpSource)
    $builder = Join-Path $BuildScratch 'build-stub.ps1'
    if (-not (Test-Path -LiteralPath $builder)) {
        [System.IO.File]::WriteAllText($builder, @'
param([Parameter(Mandatory)][string]$SourcePath, [Parameter(Mandatory)][string]$ExePath)
Add-Type -OutputType ConsoleApplication -OutputAssembly $ExePath -TypeDefinition (Get-Content -LiteralPath $SourcePath -Raw)
'@)
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $builder -SourcePath $sourcePath -ExePath $ExePath
    if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
        throw "Failed to build stub executable at $ExePath."
    }
}

try {
    foreach ($dir in @($fakeProfile, $fakeLocalAppData, $binDir, $workDir, $promptDir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    # The confirmed defect's precondition: the old resolver is absent, and nothing here recreates it.
    $oldRouting = Join-Path $fakeProfile '.claude\routing\route.py'
    if (Test-Path -LiteralPath $oldRouting) { throw 'Test setup is broken: the old routing file should not exist.' }

    $wtSource = @'
using System;
using System.IO;
using System.Text;
class Stub {
    static void Main(string[] args) {
        string log = Environment.GetEnvironmentVariable("WT_STUB_LOG");
        if (!string.IsNullOrEmpty(log)) {
            File.WriteAllText(log, string.Join("\u001f", args), Encoding.UTF8);
        }
        Environment.Exit(0);
    }
}
'@
    $codexSource = @'
using System;
class Stub {
    static void Main(string[] args) {
        Console.WriteLine("codex-cli 0.160.0");
        Environment.Exit(0);
    }
}
'@

    New-Stub -CSharpSource $wtSource -ExePath (Join-Path $binDir 'wt.exe') -BuildScratch $scratch

    $codexBin = Join-Path $fakeLocalAppData 'OpenAI\Codex\bin\stub'
    New-Item -ItemType Directory -Force -Path $codexBin | Out-Null
    New-Stub -CSharpSource $codexSource -ExePath (Join-Path $codexBin 'codex.exe') -BuildScratch $scratch

    $claudeBin = Join-Path $fakeProfile '.local\bin'
    New-Item -ItemType Directory -Force -Path $claudeBin | Out-Null
    # Never executed directly - only referenced by path in the (stubbed) wt.exe argument list.
    New-Item -ItemType File -Force -Path (Join-Path $claudeBin 'claude.exe') | Out-Null

    $promptPath = Join-Path $promptDir 'draft prompt.md'
    [System.IO.File]::WriteAllText($promptPath, "Read this and continue.`n")

    $env:PATH = "$binDir;$env:SystemRoot\System32;$env:SystemRoot"
    $env:USERPROFILE = $fakeProfile
    $env:LOCALAPPDATA = $fakeLocalAppData

    # --- handoff-claude: no -Model means the harness picks its own default ---
    $env:WT_STUB_LOG = $wtLog
    if (Test-Path -LiteralPath $wtLog) { Remove-Item -LiteralPath $wtLog -Force }
    & $claudeLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff'
    if (-not (Test-Path -LiteralPath $wtLog)) { throw 'launch-claude.ps1 did not invoke the (stubbed) terminal.' }
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -match '--model') { throw 'launch-claude.ps1 passed --model when none was given.' }
    if ($capturedArgs -notmatch [regex]::Escape($claudeBin + '\claude.exe')) {
        throw 'launch-claude.ps1 did not target the packaged/discovered claude.exe.'
    }

    # --- handoff-claude: an explicit -Model is passed straight through ---
    Remove-Item -LiteralPath $wtLog -Force
    & $claudeLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Model 'claude-sonnet-5'
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch 'claude-sonnet-5') { throw 'launch-claude.ps1 did not pass an explicit -Model through.' }

    # --- handoff-codex: no -Model/-ReasoningEffort means the harness picks its own default ---
    Remove-Item -LiteralPath $wtLog -Force
    $output = & $codexLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' 6>&1 2>&1 | Out-String
    if (-not (Test-Path -LiteralPath $wtLog)) { throw 'launch-codex.ps1 did not invoke the (stubbed) terminal.' }
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -match '--model' -or $capturedArgs -match 'model_reasoning_effort') {
        throw 'launch-codex.ps1 passed model/effort flags when none were given.'
    }
    if ($output -notmatch 'codex-cli 0\.160\.0') { throw 'launch-codex.ps1 did not report the discovered codex-cli version.' }

    # --- handoff-codex: explicit -Model/-ReasoningEffort pass straight through ---
    Remove-Item -LiteralPath $wtLog -Force
    & $codexLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Model 'gpt-5-codex' -ReasoningEffort 'high' | Out-Null
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch 'gpt-5-codex') { throw 'launch-codex.ps1 did not pass an explicit -Model through.' }
    if ($capturedArgs -notmatch 'model_reasoning_effort=high') { throw 'launch-codex.ps1 did not pass -ReasoningEffort through.' }
    # --- open-claude: no prompt, no session - just a CLI on a directory ---
    Remove-Item -LiteralPath $wtLog -Force
    & $openLauncher -WorkingDirectory $workDir -Title 'test open'
    if (-not (Test-Path -LiteralPath $wtLog)) { throw 'open-claude.ps1 did not invoke the (stubbed) terminal.' }
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch [regex]::Escape($claudeBin + '\claude.exe')) {
        throw 'open-claude.ps1 did not target the discovered claude.exe.'
    }
    if ($capturedArgs -match '--resume' -or $capturedArgs -match '--model') {
        throw 'open-claude.ps1 passed session/model flags when none were given.'
    }
    if ($capturedArgs -notmatch [regex]::Escape($workDir)) {
        throw 'open-claude.ps1 did not start the tab in the requested directory.'
    }

    # --- open-claude: -Resume reaches the CLI as --resume <id> ---
    Remove-Item -LiteralPath $wtLog -Force
    & $openLauncher -WorkingDirectory $workDir -Title 'test open' -Resume 'a2bcd5c4-bf6d-4087-95e3-d7ba7f711875'
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch '--resume') { throw 'open-claude.ps1 did not pass -Resume through.' }
    if ($capturedArgs -notmatch 'a2bcd5c4-bf6d-4087-95e3-d7ba7f711875') {
        throw 'open-claude.ps1 did not pass the session id through.'
    }

    # --- open-claude: -Resume and -Continue are mutually exclusive ---
    $rejected = $false
    try { & $openLauncher -WorkingDirectory $workDir -Resume 'abc' -Continue }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'open-claude.ps1 accepted -Resume together with -Continue.' }

    # --- every generated launcher that names the shared library can resolve the shipped dependency ---
    foreach ($launcher in $packagedLaunchers) {
        $shared = Join-Path (Split-Path -Parent $launcher) '..\..\..\resources\machine\scripts\agent-cli.ps1'
        if (-not (Test-Path -LiteralPath $shared -PathType Leaf)) {
            throw "The packaged $(Split-Path -Leaf $launcher) cannot reach the shared agent-cli.ps1."
        }
        if ((Get-Content -LiteralPath $launcher -Raw) -notmatch 'agent-cli\.ps1') {
            throw "$(Split-Path -Leaf $launcher) no longer loads the shared agent-cli.ps1."
        }
    }

} finally {
    $env:PATH = $originalPath
    $env:USERPROFILE = $originalUserProfile
    $env:LOCALAPPDATA = $originalLocalAppData
    if ($null -eq $originalWtLog) { Remove-Item Env:\WT_STUB_LOG -ErrorAction SilentlyContinue } else { $env:WT_STUB_LOG = $originalWtLog }
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS handoff-launchers.tests.ps1'
