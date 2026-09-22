# Shared launch primitives for the native agent CLIs. Dot-sourced by handoff-claude, handoff-codex and
# open-claude so the terminal invocation and the parent-session environment scrub have one owner: every
# one of them opens the same kind of Windows Terminal tab, and the differences between them are narrow
# enough to pass in. Not runnable on its own.


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

# Windows Terminal mangles argument values on the way to the tab process, and does it silently. It splits
# its own command line on `;` into subcommands, so an unescaped semicolon in a prompt truncates the prompt
# and turns the remainder into a bogus program; the tab still opens, which is what made the loss invisible.
# It then re-joins the remaining args into one child command line, quoting an arg only when that arg
# contains a space and escaping nothing inside it, and the tab process re-parses that string by
# CommandLineToArgvW rules. So a quote is eaten, and a trailing backslash in a spaced value escapes the
# closing quote and swallows the next argument whole.
function ConvertTo-TerminalArgument {
    [CmdletBinding()]
    param([Parameter(Mandatory)][AllowEmptyString()][string] $Value)

    # Windows Terminal quotes on a space and nothing else, so a line break or tab in a value with no space
    # is dropped outright and no escape can carry it. A refused launch beats a silently shortened prompt.
    if ($Value -match '[\r\n\t]' -and -not $Value.Contains(' ')) {
        throw "Windows Terminal cannot carry a line break or tab in an argument containing no space, and would drop it: $Value"
    }

    $quoted = $Value.Contains(' ')
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
    [void]$builder.Append('\', $(if ($quoted) { 2 * $backslashes } else { $backslashes }))

    # Escaped last, because Windows Terminal strips exactly one backslash before a semicolon, so this must
    # be the outermost layer for a value that legitimately ends a run of backslashes at a semicolon.
    return $builder.ToString() -replace ';', '\;'
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

        & $terminal @($terminalArguments | ForEach-Object { ConvertTo-TerminalArgument $_ })
        if ($LASTEXITCODE -ne 0) {
            throw "Windows Terminal exited with code $LASTEXITCODE"
        }
    }
    finally {
        foreach ($name in $previousValues.Keys) {
            [Environment]::SetEnvironmentVariable($name, $previousValues[$name], 'Process')
        }
    }
}
