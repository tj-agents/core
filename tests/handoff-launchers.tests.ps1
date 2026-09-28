$ErrorActionPreference = 'Stop'

# End-to-end validation of the generated handoff launchers, per PACKAGING.md: neither must require a
# machine-local file this plugin does not ship. Runs against the actual generated package
# (plugins/machine/skills/...), from an isolated fake profile with no `.claude\routing\route.py` anywhere,
# an unrelated working directory, and paths containing spaces. Windows Terminal is stubbed so no real
# terminal window opens; a fake codex.exe is compiled so launch-codex.ps1's own version-discovery step
# (which executes candidates directly, not through the terminal) has something real to run.

$repository = Split-Path -Parent $PSScriptRoot
$pluginRoot = Join-Path $repository 'plugins\machine'
$claudeLauncher = Join-Path $repository 'plugins\machine\skills\handoff-claude\scripts\launch-claude.ps1'
$codexLauncher = Join-Path $repository 'plugins\machine\skills\handoff-codex\scripts\launch-codex.ps1'
$openLauncher = Join-Path $repository 'plugins\machine\skills\open-claude\scripts\open-claude.ps1'
$packagedLaunchers = @(Get-ChildItem -LiteralPath $pluginRoot -Recurse -File -Filter '*.ps1' |
    Where-Object { (Get-Content -LiteralPath $_.FullName -Raw) -match 'agent-cli\.ps1' } |
    Select-Object -ExpandProperty FullName)
$expectedLaunchers = @(
    foreach ($tree in @('.agents\machine', 'codex-skills', 'skills')) {
        Join-Path $pluginRoot "$tree\handoff-claude\scripts\launch-claude.ps1"
        Join-Path $pluginRoot "$tree\handoff-codex\scripts\launch-codex.ps1"
        Join-Path $pluginRoot "$tree\open-claude\scripts\open-claude.ps1"
    }
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

    # Windows Terminal is stubbed twice over. WT_STUB_LOG keeps the raw argument list the launcher handed
    # it, which is what the flag assertions below read. WT_STUB_DELIVERED_LOG keeps what the tab process
    # would actually receive, because Windows Terminal does not hand its arguments over untouched: it
    # splits its own command line on `;` into subcommands (unescaping `\;` to a literal `;` by dropping
    # one backslash), then re-joins the tab's command into a single string, quoting a token only when that
    # token contains a space and escaping nothing inside it, and the tab process parses that string with
    # CommandLineToArgvW. Both stages are reproduced here; each was checked against a real wt.exe.
    $wtSource = @'
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

class Stub {
    [DllImport("shell32.dll", SetLastError = true)]
    static extern IntPtr CommandLineToArgvW([MarshalAs(UnmanagedType.LPWStr)] string commandLine, out int count);

    static List<List<string>> SplitSubcommands(string[] args) {
        var commands = new List<List<string>>();
        var current = new List<string>();
        var token = new StringBuilder();
        foreach (var arg in args) {
            token.Length = 0;
            foreach (var character in arg) {
                if (character != ';') { token.Append(character); continue; }
                if (token.Length > 0 && token[token.Length - 1] == (char)92) {
                    token.Length -= 1;
                    token.Append(';');
                    continue;
                }
                if (token.Length > 0) { current.Add(token.ToString()); token.Length = 0; }
                commands.Add(current);
                current = new List<string>();
            }
            if (token.Length > 0) { current.Add(token.ToString()); }
        }
        commands.Add(current);
        return commands;
    }

    static string[] Deliver(List<string> command) {
        var start = command.IndexOf("--suppressApplicationTitle");
        if (start < 0) { return new string[0]; }

        var joined = new StringBuilder("stub.exe");
        for (var i = start + 1; i < command.Count; i++) {
            joined.Append(' ');
            if (command[i].Contains(" ")) { joined.Append('"').Append(command[i]).Append('"'); }
            else { joined.Append(command[i]); }
        }

        int count;
        var argv = CommandLineToArgvW(joined.ToString(), out count);
        if (argv == IntPtr.Zero) { throw new InvalidOperationException("CommandLineToArgvW failed."); }
        var delivered = new string[count - 1];
        for (var i = 1; i < count; i++) {
            delivered[i - 1] = Marshal.PtrToStringUni(Marshal.ReadIntPtr(argv, i * IntPtr.Size));
        }
        Marshal.FreeHGlobal(argv);
        return delivered;
    }

    static void Main(string[] args) {
        string log = Environment.GetEnvironmentVariable("WT_STUB_LOG");
        if (!string.IsNullOrEmpty(log)) {
            File.WriteAllText(log, string.Join("\u001f", args), Encoding.UTF8);
        }

        string deliveredLog = Environment.GetEnvironmentVariable("WT_STUB_DELIVERED_LOG");
        if (!string.IsNullOrEmpty(deliveredLog)) {
            var commands = SplitSubcommands(args);
            var body = new List<string> { commands.Count.ToString() };
            body.AddRange(Deliver(commands[0]));
            File.WriteAllText(deliveredLog, string.Join("\u001f", body.ToArray()), Encoding.UTF8);
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

    # Every generated discovery layout must load the shipped shared library and reach the stub terminal.
    # The packaged canonical `.agents/machine/.../scripts` copy is one directory deeper than the host
    # `skills` and `codex-skills` copies; exercising all nine catches a resolver that supports only one.
    foreach ($launcher in $packagedLaunchers) {
        if (Test-Path -LiteralPath $wtLog) { Remove-Item -LiteralPath $wtLog -Force }
        switch (Split-Path -Leaf $launcher) {
            'launch-codex.ps1' { & $launcher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'layout test' | Out-Null }
            'launch-claude.ps1' { & $launcher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'layout test' | Out-Null }
            'open-claude.ps1' { & $launcher -WorkingDirectory $workDir -Title 'layout test' | Out-Null }
            default { throw "Unexpected generated launcher: $launcher" }
        }
        if (-not (Test-Path -LiteralPath $wtLog)) {
            throw "The generated launcher did not reach the stub terminal: $launcher"
        }
    }

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
    # Lane and frontier expectations come from the tables the plugin actually ships, so a retiering there
    # can never silently disagree with what these launchers pass through.
    $claudeTable = Get-Content -LiteralPath (Join-Path $repository 'plugins\machine\resources\lanes\claude.json') -Raw | ConvertFrom-Json
    $codexTable = Get-Content -LiteralPath (Join-Path $repository 'plugins\machine\resources\lanes\codex.json') -Raw | ConvertFrom-Json

    # --- handoff-claude: -Lane resolves through the shipped lane table ---
    Remove-Item -LiteralPath $wtLog -Force
    $launched = & $claudeLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Lane 'L3' 6>&1 | Out-String
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch [regex]::Escape($claudeTable.lanes.L3.model)) { throw 'launch-claude.ps1 did not resolve -Lane L3 through the shipped table.' }
    if ($launched -notmatch [regex]::Escape("lane L3 -> $($claudeTable.lanes.L3.model)")) { throw 'launch-claude.ps1 did not report the lane and model it launched.' }

    # --- handoff-claude: an explicit -Model still beats -Lane ---
    Remove-Item -LiteralPath $wtLog -Force
    & $claudeLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Lane 'L3' -Model 'explicitly-named-model'
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch 'explicitly-named-model') { throw 'launch-claude.ps1 let -Lane override an explicit -Model.' }
    if ($capturedArgs -match [regex]::Escape($claudeTable.lanes.L3.model)) { throw 'launch-claude.ps1 passed the lane model alongside an explicit -Model.' }

    # --- handoff-claude: -Frontier resolves the tier above the ladder ---
    Remove-Item -LiteralPath $wtLog -Force
    & $claudeLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Frontier
    $capturedArgs = [System.IO.File]::ReadAllText($wtLog)
    if ($capturedArgs -notmatch [regex]::Escape($claudeTable.frontier.model)) { throw 'launch-claude.ps1 did not resolve -Frontier to the frontier model.' }

    # --- handoff-claude: -Frontier rejects a competing selection instead of ranking it ---
    foreach ($conflict in @(@{ Lane = 'L1' }, @{ Model = 'explicitly-named-model' })) {
        $rejected = $false
        try { & $claudeLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Frontier @conflict }
        catch { $rejected = $true }
        if (-not $rejected) { throw "launch-claude.ps1 accepted -Frontier together with $($conflict.Keys -join ',')." }
    }

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
        try { & $claudeLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test handoff' -Lane $undefined }
        catch { $rejected = $true }
        if (-not $rejected) { throw "launch-claude.ps1 accepted the undefined lane $undefined." }
    }

    # --- the resolver's own guard also rejects a lane its table does not price: ValidateSet reaches the
    # binder before the table lookup, so this calls the shipped shared library directly ---
    . (Join-Path $repository 'plugins\machine\resources\machine\scripts\agent-cli.ps1')
    $rejected = $false
    try { Resolve-AgentLaneModel -Harness 'claude' -Lane 'L9' | Out-Null }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'Resolve-AgentLaneModel accepted a lane its table does not price.' }

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

    # --- open-claude: a prompt survives Windows Terminal's command line intact ---
    # The defect this covers: an unescaped semicolon ended the tab's command there and turned the rest of
    # the prompt into a second wt subcommand, so a 914-character handoff arrived as its first 265
    # characters and nothing anywhere reported the loss.
    Remove-Item -LiteralPath $wtLog -Force
    $deliveredLog = Join-Path $scratch 'wt-delivered.log'
    $env:WT_STUB_DELIVERED_LOG = $deliveredLog
    $prompt = "Phase one: migrate Auth; then Search.`nPhase two: verify `"end to end`"; report back."
    & $openLauncher -WorkingDirectory $workDir -Title 'test open' -Prompt $prompt
    if (-not (Test-Path -LiteralPath $deliveredLog)) { throw 'The stubbed terminal recorded no delivered command line.' }
    $delivered = [System.IO.File]::ReadAllText($deliveredLog) -split "`u{001f}"
    if ($delivered[0] -ne '1') {
        throw "The prompt's semicolons split the terminal command line into $($delivered[0]) subcommands; the tab would have run only the first."
    }
    if ($delivered[-1] -cne $prompt) {
        throw "The prompt did not reach the launched process whole.`nSent:      $prompt`nDelivered: $($delivered[-1])"
    }
    if ($delivered[1] -cne (Join-Path $claudeBin 'claude.exe')) {
        throw 'The spaced executable path did not reach the launched process whole.'
    }
    Remove-Item Env:\WT_STUB_DELIVERED_LOG

    # --- open-claude: a long prompt belongs in a file, not on a command line ---
    $rejected = $false
    try { & $openLauncher -WorkingDirectory $workDir -Title 'test open' -Prompt ('x' * 501) }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'open-claude.ps1 accepted an inline -Prompt too long to belong on a command line.' }

    # --- open-claude: -Resume and -Continue are mutually exclusive ---
    $rejected = $false
    try { & $openLauncher -WorkingDirectory $workDir -Resume 'abc' -Continue }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'open-claude.ps1 accepted -Resume together with -Continue.' }

    # --- every Claude session start checks the registered standards first and still opens when that fails ---
    $fakePlugins = Join-Path $fakeProfile '.claude\plugins'
    New-Item -ItemType Directory -Force -Path $fakePlugins | Out-Null
    [System.IO.File]::WriteAllText((Join-Path $fakeProfile '.claude\settings.json'), '{"enabledPlugins":{"base@core":true}}')
    [System.IO.File]::WriteAllText((Join-Path $fakePlugins 'known_marketplaces.json'), (ConvertTo-Json -Depth 5 @{
        core = @{ source = @{ source = 'git'; url = (Join-Path $scratch 'missing remote.git') }; installLocation = (Join-Path $fakePlugins 'marketplaces\core') }
    }))
    [System.IO.File]::WriteAllText((Join-Path $fakePlugins 'installed_plugins.json'), (ConvertTo-Json -Depth 6 @{
        version = 2
        plugins = @{ 'base@core' = @(@{ scope = 'user'; version = '0123456789ab'; installPath = (Join-Path $fakePlugins 'cache\core\base\0123456789ab') }) }
    }))
    $env:PATH = "$binDir;$pythonDir;$gitDir;$env:SystemRoot\System32;$env:SystemRoot"
    foreach ($start in @(
            { & $claudeLauncher -WorkingDirectory $workDir -PromptPath $promptPath -Title 'test sync' },
            { & $openLauncher -WorkingDirectory $workDir -Title 'test sync' })) {
        if (Test-Path -LiteralPath $wtLog) { Remove-Item -LiteralPath $wtLog -Force }
        $output = & $start 6>&1 | Out-String
        if ($output -notmatch 'standards: could not check core .*this session loads base 0123456789ab') {
            throw "A Claude launcher did not report the unreachable standards before launching:`n$output"
        }
        if (-not (Test-Path -LiteralPath $wtLog)) { throw 'A failed standards check stopped a Claude launch.' }
    }

    $claudeStubLog = Join-Path $scratch 'claude-stub.log'
    $env:CLAUDE_STUB_LOG = $claudeStubLog
    $env:PATH = "$claudeBin;$env:PATH"
    $shellAgents = Join-Path $repository 'shell\agents.ps1'
    . $shellAgents
    $output = claude plugin list 6>&1 | Out-String
    if ($output -match 'standards:') { throw "The shell claude function checked standards for a plain subcommand:`n$output" }
    $output = claude --resume a2bcd5c4-bf6d-4087-95e3-d7ba7f711875 6>&1 | Out-String
    if ($output -notmatch 'standards: could not check core') { throw "The shell claude function did not check standards before a session:`n$output" }

    $restore = Join-Path $repository 'cli-session-recovery\start-saved-cli.ps1'
    $windowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $output = & $windowsPowerShell -NoProfile -ExecutionPolicy Bypass -Command "& { . '$shellAgents'; & '$restore' -Tool claude -SessionId 'b2bcd5c4-bf6d-4087-95e3-d7ba7f711875' -WindowGroup test }" 2>&1 | Out-String
    if ($output -notmatch 'standards: could not check core') { throw "Session recovery did not check standards before resuming:`n$output" }

    $stubCalls = [System.IO.File]::ReadAllLines($claudeStubLog)
    $expectedCalls = 'plugin list|--resume a2bcd5c4-bf6d-4087-95e3-d7ba7f711875|--resume b2bcd5c4-bf6d-4087-95e3-d7ba7f711875'
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
    if ($null -ne $originalClaudeConfig) { $env:CLAUDE_CONFIG_DIR = $originalClaudeConfig }
    Remove-Item Env:\CLAUDE_STUB_LOG -ErrorAction SilentlyContinue
    if ($null -eq $originalWtLog) { Remove-Item Env:\WT_STUB_LOG -ErrorAction SilentlyContinue } else { $env:WT_STUB_LOG = $originalWtLog }
    Remove-Item Env:\WT_STUB_DELIVERED_LOG -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS handoff-launchers.tests.ps1'
