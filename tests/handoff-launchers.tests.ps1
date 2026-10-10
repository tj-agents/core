$ErrorActionPreference = 'Stop'

# End-to-end validation of what still dot-sources the generated agent-cli.ps1, per PACKAGING.md: it must
# not require a machine-local file this plugin does not ship. handoff-claude and handoff-codex both moved
# to Python (test_launch_claude.py, test_launch_codex.py); open-claude moved earlier. agent-cli.ps1's only
# remaining consumer is the terminal claude launcher (claude-profile.ps1), exercised below alongside
# session recovery, which both still check standards through it. Runs against the actual generated package
# (plugins/machine/...), from an isolated fake profile with paths containing spaces.

$repository = Split-Path -Parent $PSScriptRoot
$pluginRoot = Join-Path $repository 'plugins\machine'
$packagedLaunchers = @(Get-ChildItem -LiteralPath $pluginRoot -Recurse -File -Filter '*.ps1' |
    Where-Object { (Get-Content -LiteralPath $_.FullName -Raw) -match 'agent-cli\.ps1' } |
    Select-Object -ExpandProperty FullName)
$expectedLaunchers = @(Join-Path $pluginRoot 'resources\machine\scripts\claude-profile.ps1') | Sort-Object
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

$originalPath = $env:PATH
$pythonDir = Split-Path -Parent (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$gitDir = Split-Path -Parent (Get-Command git -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$originalClaudeConfig = $env:CLAUDE_CONFIG_DIR
$originalUserProfile = $env:USERPROFILE
$originalPSModuleAnalysisCachePath = $env:PSModuleAnalysisCachePath
$moduleAnalysisCachePath = Join-Path $scratch 'powershell cache\ModuleAnalysisCache'

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
    New-Item -ItemType Directory -Force -Path $fakeProfile | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $moduleAnalysisCachePath) | Out-Null
    $env:PSModuleAnalysisCachePath = $moduleAnalysisCachePath

    $claudeBin = Join-Path $fakeProfile '.local\bin'
    New-Item -ItemType Directory -Force -Path $claudeBin | Out-Null
    New-Stub -ExePath (Join-Path $claudeBin 'claude.exe') -BuildScratch $scratch -CSharpSource @'
using System;
using System.IO;
class Stub {
    static void Main(string[] args) {
        File.AppendAllText(Environment.GetEnvironmentVariable("CLAUDE_STUB_LOG"), string.Join(" ", args) + "\n");
    }
}
'@

    Remove-Item Env:\CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue
    $env:USERPROFILE = $fakeProfile

    $cacheProbeCwd = Join-Path $scratch "cache probe $([guid]::NewGuid().ToString('N'))"
    $cacheProbePath = Join-Path $scratch 'powershell cache\DiscoveryProbeCache'
    New-Item -ItemType Directory -Path $cacheProbeCwd | Out-Null
    $windowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $cacheProbeCommand = @'
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) {
    throw 'The module cache regression requires Windows PowerShell 5.1.'
}
Get-Module -ListAvailable | Out-Null
Get-Command * | Out-Null
$deadline = [DateTime]::UtcNow.AddSeconds(20)
while (-not (Test-Path -LiteralPath $env:PSModuleAnalysisCachePath -PathType Leaf) -and [DateTime]::UtcNow -lt $deadline) {
    Start-Sleep -Milliseconds 100
}
if (-not (Test-Path -LiteralPath $env:PSModuleAnalysisCachePath -PathType Leaf)) {
    throw 'Windows PowerShell module discovery did not create the explicit scratch cache.'
}
if ((Get-Item -LiteralPath $env:PSModuleAnalysisCachePath).Length -eq 0) {
    throw 'Windows PowerShell module discovery created an empty cache.'
}
if (Test-Path -LiteralPath (Join-Path (Get-Location).Path 'Microsoft')) {
    throw 'Windows PowerShell module discovery polluted its working directory.'
}
'@
    $cacheProbeEncoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cacheProbeCommand))
    $env:PSModuleAnalysisCachePath = $cacheProbePath
    Push-Location $cacheProbeCwd
    try {
        & $windowsPowerShell -NoProfile -ExecutionPolicy Bypass -EncodedCommand $cacheProbeEncoded
        if ($LASTEXITCODE -ne 0) { throw 'The Windows PowerShell module cache regression failed.' }
    } finally {
        Pop-Location
        $env:PSModuleAnalysisCachePath = $moduleAnalysisCachePath
    }
    if (-not (Test-Path -LiteralPath $cacheProbePath -PathType Leaf) -or (Test-Path -LiteralPath (Join-Path $cacheProbeCwd 'Microsoft'))) {
        throw 'Windows PowerShell module discovery escaped the explicit scratch cache.'
    }

    # --- agent-cli.ps1's own guard rejects a lane its table does not price: ValidateSet reaches the
    # binder before the table lookup, but Resolve-AgentLaneModel's own guard is exercised directly here,
    # since no remaining consumer calls it (claude-profile.ps1 only calls Sync-ClaudeStandards) ---
    . (Join-Path $repository 'plugins\machine\resources\machine\scripts\agent-cli.ps1')
    $rejected = $false
    try { Resolve-AgentLaneModel -Harness 'claude' -Lane 'L9' | Out-Null }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'Resolve-AgentLaneModel accepted a lane its table does not price.' }

    # --- every Claude session start checks the registered standards first and still opens when that fails ---
    $fakePlugins = Join-Path $fakeProfile '.claude\plugins'
    New-Item -ItemType Directory -Force -Path $fakePlugins | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $fakeProfile '.claude\settings.json'), '{"enabledPlugins":{"base@core":true}}')
    [System.IO.File]::WriteAllText((Join-Path $fakePlugins 'known_marketplaces.json'), (ConvertTo-Json -Depth 5 @{
        core = @{ source = @{ source = 'git'; url = (Join-Path $scratch 'missing remote.git') }; installLocation = (Join-Path $fakePlugins 'marketplaces\core') }
    }))
    [System.IO.File]::WriteAllText((Join-Path $fakePlugins 'installed_plugins.json'), (ConvertTo-Json -Depth 6 @{
        version = 2
        plugins = @{
            'base@core' = @(@{ scope = 'user'; version = '0123456789ab'; installPath = (Join-Path $fakePlugins 'cache\core\base\0123456789ab') })
            'machine@base-agents' = @(@{ scope = 'user'; version = 'generated'; installPath = $pluginRoot })
        }
    }))
    $env:PATH = "$pythonDir;$gitDir;$env:SystemRoot\System32;$env:SystemRoot"
    # handoff-claude's own standards-before-launch check moved to test_launch_claude.py with sync_claude_standards
    # mocked; the fake plugin registry set up above is exercised below by the terminal claude function and
    # session recovery instead, which still check standards through this same real claude_standards_sync.py path.

    $claudeStubLog = Join-Path $scratch 'claude-stub.log'
    $env:CLAUDE_STUB_LOG = $claudeStubLog
    $env:PATH = "$claudeBin;$env:PATH"
    $fakeDocuments = Join-Path $scratch 'fake documents'
    $hookOutput = & (Join-Path $pythonDir 'python.exe') -B (Join-Path $pluginRoot 'resources\machine\scripts\claude_terminal_profile.py') --documents $fakeDocuments | Out-String
    if ($hookOutput -notmatch 'new PowerShell terminals now refresh Claude plugins') { throw "The machine SessionStart hook did not wire the terminal profile:`n$hookOutput" }
    $pwshProfile = Join-Path $fakeDocuments 'PowerShell\Microsoft.PowerShell_profile.ps1'
    $windowsProfile = Join-Path $fakeDocuments 'WindowsPowerShell\Microsoft.PowerShell_profile.ps1'
    . $pwshProfile
    $claudeCommand = Get-Command claude -CommandType Function
    if ($claudeCommand.ScriptBlock.File -ne (Join-Path $pluginRoot 'resources\machine\scripts\claude-profile.ps1')) {
        throw "The terminal profile did not load claude from the installed machine plugin: $($claudeCommand.ScriptBlock.File)"
    }
    $output = claude plugin list 6>&1 | Out-String
    if ($output -match 'standards:') { throw "The terminal claude function checked standards for a plain subcommand:`n$output" }
    $output = claude --resume a2bcd5c4-bf6d-4087-95e3-d7ba7f711875 6>&1 | Out-String
    if ($output -notmatch 'standards: could not check core') { throw "The terminal claude function did not check standards before a session:`n$output" }

    $windowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $output = & $windowsPowerShell -NoProfile -ExecutionPolicy Bypass -Command "& { . '$windowsProfile'; claude plugin list; claude --resume c2bcd5c4-bf6d-4087-95e3-d7ba7f711875 }" 2>&1 | Out-String
    if (([regex]::Matches($output, 'standards: could not check core')).Count -ne 1) {
        throw "Windows PowerShell's claude function did not check standards exactly once, before the session:`n$output"
    }

    $restore = Join-Path $repository 'cli-session-recovery\start-saved-cli.ps1'
    $output = & $windowsPowerShell -NoProfile -ExecutionPolicy Bypass -Command "& { . '$windowsProfile'; & '$restore' -Tool claude -SessionId 'b2bcd5c4-bf6d-4087-95e3-d7ba7f711875' -WindowGroup test }" 2>&1 | Out-String
    if ($output -notmatch 'standards: could not check core') { throw "Session recovery did not check standards before resuming:`n$output" }

    $stubCalls = [System.IO.File]::ReadAllLines($claudeStubLog)
    $expectedCalls = 'plugin list|--resume a2bcd5c4-bf6d-4087-95e3-d7ba7f711875|plugin list|--resume c2bcd5c4-bf6d-4087-95e3-d7ba7f711875|--resume b2bcd5c4-bf6d-4087-95e3-d7ba7f711875'
    if (($stubCalls -join '|') -ne $expectedCalls) {
        throw "The shell and recovery launchers did not pass their arguments through: $($stubCalls -join '|')"
    }

    # --- every generated launcher still names the shared library it just resolved and executed ---
    foreach ($launcher in $packagedLaunchers) {
        if ((Get-Content -LiteralPath $launcher -Raw) -notmatch 'agent-cli\.ps1') {
            throw "$(Split-Path -Leaf $launcher) no longer loads the shared agent-cli.ps1."
        }
    }

} finally {
    $env:PATH = $originalPath
    $env:USERPROFILE = $originalUserProfile
    if ($null -eq $originalPSModuleAnalysisCachePath) {
        Remove-Item Env:\PSModuleAnalysisCachePath -ErrorAction SilentlyContinue
    } else {
        $env:PSModuleAnalysisCachePath = $originalPSModuleAnalysisCachePath
    }
    if ($null -ne $originalClaudeConfig) { $env:CLAUDE_CONFIG_DIR = $originalClaudeConfig }
    Remove-Item Env:\CLAUDE_STUB_LOG -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS handoff-launchers.tests.ps1'
