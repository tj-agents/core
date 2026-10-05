# Shared launch primitives for the native agent CLIs. Dot-sourced by handoff-claude, handoff-codex,
# open-claude and the terminal claude launcher so the terminal invocation and the parent-session environment scrub
# have one owner: every one of them opens the same kind of Windows Terminal tab, and the differences
# between them are narrow enough to pass in. Not runnable on its own.


# Session state a Claude Code parent exports into anything it spawns. NO_COLOR=1 alone makes the child
# black and white; the CLAUDE_CODE_* set binds it to the parent's messaging pipe and makes it behave as a
# managed nested child rather than the independent session the caller asked for. CLAUDE_CODE_GIT_BASH_PATH
# is machine configuration rather than session state and is deliberately absent from this list.
$script:AgentSessionEnvironment = @(
    'NO_COLOR',
    'CLAUDECODE',
    'CLAUDE_CODE_CHILD_SESSION',
    'CLAUDE_CODE_ENTRYPOINT',
    'CLAUDE_CODE_SESSION_ID',
    'CLAUDE_CODE_MESSAGING_SOCKET',
    'CLAUDE_CODE_MESSAGING_TOKEN',
    'CLAUDE_PID',
    'WORKBOARD_LAUNCH_TOKEN',
    'WORKBOARD_WORKFLOW_TOKEN'
)

# The native executable, never the NVM/npm shim: a shim launches the TUI through an extra node process and
# degrades it to monochrome and non-interactive, the failure handoff-codex first recorded. `claude` on PATH
# resolves to that shim (claude.ps1/claude.cmd), so PATH is consulted only for a real claude.exe.
function Resolve-ClaudeExecutable {
    [CmdletBinding()]
    param()

    $claude = Join-Path $env:USERPROFILE '.local\bin\claude.exe'
    if (Test-Path -LiteralPath $claude -PathType Leaf) { return $claude }

    $claude = (Get-Command claude.exe -CommandType Application -ErrorAction SilentlyContinue).Source
    if ($claude -and (Test-Path -LiteralPath $claude -PathType Leaf)) { return $claude }

    throw "The native Claude Code executable was not found. Looked for $env:USERPROFILE\.local\bin\claude.exe and claude.exe on PATH."
}

function Sync-ClaudeStandards {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string] $WorkingDirectory,
        [string] $Claude
    )

    $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $python) {
        Write-Host 'standards: python was not found; this session loads the installed plugins'
        return
    }

    $config = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
    $plugins = if ($env:CLAUDE_CODE_PLUGIN_CACHE_DIR) { $env:CLAUDE_CODE_PLUGIN_CACHE_DIR } else { Join-Path $config 'plugins' }
    $candidates = @()
    try {
        $registry = Get-Content -LiteralPath (Join-Path $plugins 'installed_plugins.json') -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
        $candidates += @($registry.plugins.'machine@base-agents' | Where-Object { $_.scope -eq 'user' -and $_.installPath } |
            ForEach-Object { Join-Path $_.installPath 'resources\machine\scripts\claude_standards_sync.py' })
    }
    catch { }
    $candidates += Join-Path $PSScriptRoot 'claude_standards_sync.py'
    $script = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if (-not $script) {
        Write-Host 'standards: claude_standards_sync.py was not found; this session loads the installed plugins'
        return
    }

    $arguments = @('-B', $script, '--project', $WorkingDirectory)
    if ($Claude) { $arguments += @('--claude', $Claude) }
    & $python.Source @arguments | ForEach-Object { Write-Host $_ }
}

# Windows Terminal mangles argument values on the way to the tab process, and does it silently. It splits
# its own command line on `;` into subcommands, so an unescaped semicolon in a prompt truncates the prompt
# and turns the remainder into a bogus program; the tab still opens, which is what made the loss invisible.
# It then re-joins the remaining args into one child command line, quoting an arg only when that arg
# contains a space and escaping nothing inside it, and the tab process re-parses that string by
# CommandLineToArgvW rules. So a quote is eaten, and a trailing backslash in a spaced value escapes the
# closing quote and swallows the next argument whole.
function ConvertTo-EscapedArgumentText {
    param([Parameter(Mandatory)][AllowEmptyString()][string] $Value, [bool] $Quoted)

    $builder = [System.Text.StringBuilder]::new()
    $backslashes = 0
    foreach ($character in $Value.ToCharArray()) {
        if ($character -eq '\') { $backslashes++; continue }
        if ($character -eq '"') {
            [void]$builder.Append('\', (2 * $backslashes) + 1).Append('"')
        }
        else {
            [void]$builder.Append('\', $backslashes).Append($character)
        }
        $backslashes = 0
    }
    [void]$builder.Append('\', $(if ($Quoted) { 2 * $backslashes } else { $backslashes }))
    return $builder.ToString()
}

function ConvertTo-TerminalArgument {
    [CmdletBinding()]
    param([Parameter(Mandatory)][AllowEmptyString()][string] $Value)

    # Windows Terminal quotes on a space and nothing else, so a line break or tab in a value with no space
    # is dropped outright and no escape can carry it. A refused launch beats a silently shortened prompt.
    if ($Value -match '[\r\n\t]' -and -not $Value.Contains(' ')) {
        throw "Windows Terminal cannot carry a line break or tab in an argument containing no space, and would drop it: $Value"
    }

    $escaped = ConvertTo-EscapedArgumentText -Value $Value -Quoted $Value.Contains(' ')

    # Escaped last, because Windows Terminal strips exactly one backslash before a semicolon, so this must
    # be the outermost layer for a value that legitimately ends a run of backslashes at a semicolon.
    return $escaped -replace ';', '\;'
}

function ConvertTo-CommandLineArgument {
    param([Parameter(Mandatory)][AllowEmptyString()][string] $Value)

    if ($Value -and $Value -notmatch '[\s"]') { return $Value }
    return '"' + (ConvertTo-EscapedArgumentText -Value $Value -Quoted $true) + '"'
}

# Opens the CLI as a new tab in the Windows Terminal window that most recently had focus.
#
# ClearEnvironment and ForceEnvironment are the whole of the per-agent variance and are always the
# caller's to state: Claude forces FORCE_COLOR/TERM on, Codex clears TERM instead, and those two are
# mutually exclusive. Nothing is guessed here on their behalf.
function Invoke-AgentTerminalTab {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string] $WorkingDirectory,
        [Parameter(Mandatory)][string] $Executable,
        [Parameter(Mandatory)][string] $Title,
        [string[]] $Arguments = @(),
        [string[]] $ClearEnvironment = @(),
        [hashtable] $ForceEnvironment = @{}
    )

    if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
        throw "Working directory is not a directory: $WorkingDirectory"
    }

    $terminal = (Get-Command wt.exe -ErrorAction Stop).Source

    # --window 0 is WT's documented sentinel for "the window that most recently had focus". This is not
    # the same as omitting the flag: windowingBehavior is unset on this machine, so the default with no
    # flag at all is useNew - always a separate OS window. Do not simplify this away, and do not swap it
    # for --window new, which forces the opposite of what it looks like it asks for.
    $terminalArguments = @(
        '--window', '0',
        'new-tab',
        '--startingDirectory', $WorkingDirectory,
        '--title', $Title,
        '--suppressApplicationTitle',
        $Executable
    ) + $Arguments

    # The tab title is the only name for this session the user can see on screen, so the session records
    # it at SessionStart and peer-cli resolves by it.
    $ForceEnvironment = $ForceEnvironment.Clone()
    $ForceEnvironment['AGENT_CLI_TAB_TITLE'] = $Title

    $cleared = @($script:AgentSessionEnvironment + $ClearEnvironment | Select-Object -Unique)
    $previousValues = @{}
    foreach ($name in @($cleared + @($ForceEnvironment.Keys))) {
        $previousValues[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }

    try {
        foreach ($name in $cleared) {
            [Environment]::SetEnvironmentVariable($name, $null, 'Process')
        }
        foreach ($name in $ForceEnvironment.Keys) {
            [Environment]::SetEnvironmentVariable($name, $ForceEnvironment[$name], 'Process')
        }

        # Windows PowerShell 5.1 hands embedded quotes to a native program unescaped, so the command line is
        # built here rather than by `&`, which keeps what wt receives identical on both hosts.
        $commandLine = @($terminalArguments | ForEach-Object { ConvertTo-CommandLineArgument (ConvertTo-TerminalArgument $_) }) -join ' '
        $startInfo = [System.Diagnostics.ProcessStartInfo]::new($terminal, $commandLine)
        $startInfo.UseShellExecute = $false
        $process = [System.Diagnostics.Process]::Start($startInfo)
        $process.WaitForExit()
        if ($process.ExitCode -ne 0) {
            throw "Windows Terminal exited with code $($process.ExitCode)"
        }
    }
    finally {
        foreach ($name in $previousValues.Keys) {
            [Environment]::SetEnvironmentVariable($name, $previousValues[$name], 'Process')
        }
    }
}

# Lane -> model for a chosen harness, read from the canonical lane tables (.agents/lanes in the authored
# layout, resources/lanes in the packaged one -- the same relative hop from this file in both). The tables
# are the repo's only model-name owner, so a retiering is one edit there and every consumer inherits it.
# Resolution never picks the lane: a caller that supplies neither -Lane nor -Model gets the CLI's own
# configured default, because guessing a lane from a prompt is how an expensive model ends up serving a
# rename. -Frontier resolves the tier above the ladder, which no lane resolves to: its selection is the
# user's explicit request, never task shape.
function Resolve-AgentLaneModel {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('claude', 'codex')]
        [string] $Harness,

        [string] $Lane,

        [switch] $Frontier
    )

    if (-not $Lane -and -not $Frontier) { throw 'Resolve-AgentLaneModel needs a -Lane or -Frontier.' }
    if ($Lane -and $Frontier) { throw 'A lane and the frontier tier are mutually exclusive.' }

    $tablePath = Join-Path $PSScriptRoot "..\..\lanes\$Harness.json"
    if (-not (Test-Path -LiteralPath $tablePath -PathType Leaf)) {
        throw "The $Harness lane table was not found at $tablePath."
    }

    $table = Get-Content -LiteralPath $tablePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $entry = if ($Frontier) { $table.frontier } else { $table.lanes.$Lane }
    if (-not $entry -or -not $entry.model) {
        $known = @($table.lanes.PSObject.Properties.Name) -join ' '
        $asked = if ($Frontier) { 'the frontier tier' } else { "lane '$Lane'" }
        throw "The $Harness lane table at $tablePath does not price $asked; it has $known."
    }

    $effortKey = if ($table.effort_key) { $table.effort_key } else { 'effort' }
    return [pscustomobject]@{
        Model  = $entry.model
        Effort = $entry.$effortKey
    }
}
