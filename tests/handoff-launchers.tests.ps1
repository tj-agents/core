$ErrorActionPreference = 'Stop'

# End-to-end validation of the generated PowerShell handoff launcher, per PACKAGING.md: it must not
# require a machine-local file this plugin does not ship. handoff-claude's own Python launcher has its
# own tests in test_launch_claude.py; this file covers launch-codex.ps1 and the terminal claude/session
# recovery entry points that still dot-source agent-cli.ps1. Runs against the actual generated package
# (plugins/machine/skills/...), from an isolated fake profile with no `.claude\routing\route.py` anywhere,
# an unrelated working directory, and paths containing spaces. Windows Terminal is stubbed so no real
# terminal window opens; a fake codex.exe is compiled so launch-codex.ps1's own version-discovery step
# (which executes candidates directly, not through the terminal) has something real to run.

$repository = Split-Path -Parent $PSScriptRoot
$pluginRoot = Join-Path $repository 'plugins\machine'
$codexLauncher = Join-Path $repository 'plugins\machine\skills\handoff-codex\scripts\launch-codex.ps1'
$packagedLaunchers = @(Get-ChildItem -LiteralPath $pluginRoot -Recurse -File -Filter '*.ps1' |
    Where-Object { (Get-Content -LiteralPath $_.FullName -Raw) -match 'agent-cli\.ps1' } |
    Select-Object -ExpandProperty FullName)
$expectedLaunchers = @(
    foreach ($tree in @('.agents\machine\utility', 'codex-skills', 'skills')) {
        Join-Path $pluginRoot "$tree\handoff-codex\scripts\launch-codex.ps1"
    }
    Join-Path $pluginRoot 'resources\machine\scripts\claude-profile.ps1'
) | Sort-Object
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
$pythonDir = Split-Path -Parent (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$gitDir = Split-Path -Parent (Get-Command git -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$originalClaudeConfig = $env:CLAUDE_CONFIG_DIR
$originalUserProfile = $env:USERPROFILE
$originalLocalAppData = $env:LOCALAPPDATA
$originalWtLog = $env:WT_STUB_LOG
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
    foreach ($dir in @($fakeProfile, $fakeLocalAppData, $binDir, $workDir, $promptDir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $moduleAnalysisCachePath) | Out-Null
    $env:PSModuleAnalysisCachePath = $moduleAnalysisCachePath

    # The confirmed defect's precondition: the old resolver is absent, and nothing here recreates it.
    $oldRouting = Join-Path $fakeProfile '.claude\routing\route.py'
    if (Test-Path -LiteralPath $oldRouting) { throw 'Test setup is broken: the old routing file should not exist.' }

    # Windows Terminal is stubbed so no real terminal window opens. WT_STUB_LOG keeps the raw argument
    # list the launcher handed it, which is what the flag assertions below read, including the escaping
    # round-trip test further down: agent-cli.ps1's ConvertTo-TerminalArgument/ConvertTo-CommandLineArgument
    # are this PowerShell implementation's own escaping and are exercised directly here. The separate Python
    # port in agent_cli.py has its own coverage in test_agent_cli.py's TerminalArgumentTests and
    # LaunchTabTests; that suite says nothing about this one.
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
        if (args.Length >= 4 && args[0] == "plugin" && args[1] == "marketplace" && args[2] == "upgrade") {
            Console.WriteLine("{\"selectedMarketplaces\":[],\"upgradedRoots\":[],\"errors\":[]}");
        } else if (args.Length >= 3 && args[0] == "plugin" && args[1] == "list") {
            Console.WriteLine("{\"installed\":[],\"available\":[]}");
        } else {
            Console.WriteLine("codex-cli 0.160.0");
        }
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
    New-Stub -ExePath (Join-Path $claudeBin 'claude.exe') -BuildScratch $scratch -CSharpSource @'
using System;
using System.IO;
class Stub {
    static void Main(string[] args) {
        File.AppendAllText(Environment.GetEnvironmentVariable("CLAUDE_STUB_LOG"), string.Join(" ", args) + "\n");
    }
}
'@

    $promptPath = Join-Path $promptDir 'draft prompt.md'
    [System.IO.File]::WriteAllText($promptPath, "Read this and continue.`n")

    $env:PATH = "$binDir;$env:SystemRoot\System32;$env:SystemRoot"
    Remove-Item Env:\CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue
    $env:USERPROFILE = $fakeProfile
    $env:LOCALAPPDATA = $fakeLocalAppData
    $env:WT_STUB_LOG = $wtLog

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

    # Every generated discovery layout must load the shipped shared library and reach the stub terminal.
    # The packaged canonical `.agents/machine/.../scripts` copy is one directory deeper than the host
    # `skills` and `codex-skills` copies; exercising all six catches a resolver that supports only one.
    foreach ($launcher in @($packagedLaunchers | Where-Object { (Split-Path -Leaf $_) -ne 'claude-profile.ps1' })) {
        if (Test-Path -LiteralPath $wtLog) { Remove-Item -LiteralPath $wtLog -Force }
        switch (Split-Path -Leaf $launcher) {
            'launch-codex.ps1' { & $launcher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'layout test' | Out-Null }
            default { throw "Unexpected generated launcher: $launcher" }
        }
        if (-not (Test-Path -LiteralPath $wtLog)) {
            throw "The generated launcher did not reach the stub terminal: $launcher"
        }
        $delivered = @([System.IO.File]::ReadAllText($wtLog) -split [char]0x1f)
        $titleIndex = [array]::IndexOf($delivered, '--title')
        $suppressionIndex = [array]::IndexOf($delivered, '--suppressApplicationTitle')
        $expectedExecutable = if ((Split-Path -Leaf $launcher) -eq 'launch-codex.ps1') {
            Join-Path $codexBin 'codex.exe'
        } else {
            Join-Path $claudeBin 'claude.exe'
        }
        if ($titleIndex -lt 0 -or $delivered[$titleIndex + 1] -cne 'layout test') {
            throw "The generated launcher did not retain the caller's title: $launcher"
        }
        if ($suppressionIndex -ne ($titleIndex + 2) -or $delivered[$suppressionIndex + 1] -cne $expectedExecutable) {
            throw "The generated launcher did not suppress application titles before the executable: $launcher"
        }
    }

    # --- the shared escaping survives a quote, a semicolon and a trailing backslash before a space ---
    # -Title is the only free-form string launch-codex.ps1 hands to Invoke-AgentTerminalTab (open-claude and
    # handoff-claude moved to Python, whose escaping test_agent_cli.py covers), so it carries these values. The
    # stub only captures what wt.exe itself would receive (one hop); the backslash-quote sequences
    # agent-cli.ps1 embeds are meant to survive Windows Terminal's own dumb re-quoting unmodified and are
    # only resolved by the final child process's own argv parsing, and a `\;` is Windows Terminal's own
    # unescape of the semicolon it split subcommands on. Both remaining hops are reproduced here so the
    # comparison is against what the user's actual agent process would see, not this one intermediate hop.
    Add-Type -Namespace StubTerminalTest -Name Argv -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("shell32.dll", SetLastError = true)]
public static extern System.IntPtr CommandLineToArgvW([System.Runtime.InteropServices.MarshalAs(System.Runtime.InteropServices.UnmanagedType.LPWStr)] string commandLine, out int count);
'@
    function ConvertFrom-StubTerminalArgument {
        param([Parameter(Mandatory)][AllowEmptyString()][string] $Value)
        $unescaped = $Value -replace '\\;', ';'
        $wrapped = if ($unescaped.Contains(' ')) { "fake.exe `"$unescaped`"" } else { "fake.exe $unescaped" }
        $count = 0
        $argv = [StubTerminalTest.Argv]::CommandLineToArgvW($wrapped, [ref] $count)
        if ($argv -eq [IntPtr]::Zero) { throw 'CommandLineToArgvW failed.' }
        return [System.Runtime.InteropServices.Marshal]::PtrToStringUni([System.Runtime.InteropServices.Marshal]::ReadIntPtr($argv, [IntPtr]::Size))
    }
    $title = 'say "hi" a;b'
    $prompt = 'C:\two\ trailing\'
    foreach ($value in @($title, $prompt)) {
        Remove-Item -LiteralPath $wtLog -Force
        & $codexLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title $value | Out-Null
        $delivered = @([System.IO.File]::ReadAllText($wtLog) -split [char]0x1f)
        $titleIndex = [array]::IndexOf($delivered, '--title') + 1
        if ($titleIndex -le 0) { throw "launch-codex.ps1 did not pass --title through for: $value" }
        # An unescaped semicolon is a split point to Windows Terminal itself (CommandLineToArgvW does not
        # treat `;` specially, so it cannot catch this): every semicolon reaching the stub must have a
        # backslash immediately before it, or a real launch would have been cut there.
        if ($delivered[$titleIndex] -cmatch '(?<!\\);') {
            throw "An unescaped semicolon would have split Windows Terminal's command line: $($delivered[$titleIndex])"
        }
        $reconstructed = ConvertFrom-StubTerminalArgument $delivered[$titleIndex]
        if ($reconstructed -cne $value) {
            throw "The title did not reach the launched process whole.`nSent:      $value`nDelivered: $($delivered[$titleIndex])`nReconstructed: $reconstructed"
        }
    }

    # --- handoff-codex: no -Model/-ReasoningEffort means the harness picks its own default ---
    $env:WT_STUB_LOG = $wtLog
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
    # Lane and frontier expectations come from the table the plugin actually ships, so a retiering there
    # can never silently disagree with what this launcher passes through. Claude's own lane and frontier
    # resolution is exercised against the real table in test_launch_claude.py, not here.
    $codexTable = Get-Content -LiteralPath (Join-Path $repository 'plugins\machine\resources\lanes\codex.json') -Raw | ConvertFrom-Json

    # --- handoff-codex: -Lane resolves both model and effort ---
    Remove-Item -LiteralPath $wtLog -Force
    $launched = & $codexLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Lane 'L4' 6>&1 | Out-String
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch [regex]::Escape($codexTable.lanes.L4.model)) { throw 'launch-codex.ps1 did not resolve -Lane L4 through the shipped table.' }
    if ($launched -notmatch [regex]::Escape("lane L4 -> $($codexTable.lanes.L4.model) at $($codexTable.lanes.L4.reasoning_effort)")) { throw 'launch-codex.ps1 did not report the lane, model and effort it launched.' }
    if ($capturedArgs -notmatch "model_reasoning_effort=$($codexTable.lanes.L4.reasoning_effort)") { throw 'launch-codex.ps1 did not resolve -Lane L4 to its effort.' }

    # --- handoff-codex: an explicit -Model survives a -Lane, which still fills the effort half ---
    Remove-Item -LiteralPath $wtLog -Force
    $launched = & $codexLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Lane 'L4' -Model 'explicitly-named-model' 6>&1 | Out-String
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($launched -notmatch [regex]::Escape("on explicitly-named-model at $($codexTable.lanes.L4.reasoning_effort)")) { throw 'launch-codex.ps1 labelled an explicit -Model as the lane model.' }
    if ($capturedArgs -notmatch 'explicitly-named-model') { throw 'launch-codex.ps1 let -Lane override an explicit -Model.' }
    if ($capturedArgs -match [regex]::Escape($codexTable.lanes.L4.model)) { throw 'launch-codex.ps1 passed the lane model alongside an explicit -Model.' }
    if ($capturedArgs -notmatch "model_reasoning_effort=$($codexTable.lanes.L4.reasoning_effort)") { throw 'launch-codex.ps1 did not fill the effort half from the lane beside an explicit -Model.' }

    # --- handoff-codex: an explicit -ReasoningEffort survives a -Lane that would have set it ---
    Remove-Item -LiteralPath $wtLog -Force
    & $codexLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Lane 'L4' -ReasoningEffort 'xhigh' | Out-Null
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch [regex]::Escape($codexTable.lanes.L4.model)) { throw 'launch-codex.ps1 dropped the lane model when effort was explicit.' }
    if ($capturedArgs -notmatch 'model_reasoning_effort=xhigh') { throw 'launch-codex.ps1 let -Lane override an explicit -ReasoningEffort.' }

    # --- handoff-codex: -Frontier resolves the tier's model and effort as a pair ---
    Remove-Item -LiteralPath $wtLog -Force
    & $codexLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Frontier | Out-Null
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch [regex]::Escape($codexTable.frontier.model)) { throw 'launch-codex.ps1 did not resolve -Frontier to the frontier model.' }
    if ($capturedArgs -notmatch "model_reasoning_effort=$($codexTable.frontier.reasoning_effort)") { throw 'launch-codex.ps1 did not resolve -Frontier to its effort.' }

    # --- an out-of-ladder lane is rejected at the parameter surface, never silently defaulted ---
    foreach ($undefined in @('L0', 'L9')) {
        $rejected = $false
        try { & $codexLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Lane $undefined }
        catch { $rejected = $true }
        if (-not $rejected) { throw "launch-codex.ps1 accepted the undefined lane $undefined." }
    }

    # --- the resolver's own guard also rejects a lane its table does not price: ValidateSet reaches the
    # binder before the table lookup, so this calls the shipped shared library directly ---
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
    $env:PATH = "$binDir;$pythonDir;$gitDir;$env:SystemRoot\System32;$env:SystemRoot"
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
    $env:LOCALAPPDATA = $originalLocalAppData
    if ($null -eq $originalPSModuleAnalysisCachePath) {
        Remove-Item Env:\PSModuleAnalysisCachePath -ErrorAction SilentlyContinue
    } else {
        $env:PSModuleAnalysisCachePath = $originalPSModuleAnalysisCachePath
    }
    if ($null -ne $originalClaudeConfig) { $env:CLAUDE_CONFIG_DIR = $originalClaudeConfig }
    Remove-Item Env:\CLAUDE_STUB_LOG -ErrorAction SilentlyContinue
    if ($null -eq $originalWtLog) { Remove-Item Env:\WT_STUB_LOG -ErrorAction SilentlyContinue } else { $env:WT_STUB_LOG = $originalWtLog }
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS handoff-launchers.tests.ps1'
