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

        & $terminal @terminalArguments
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

# Lane -> model for a chosen harness, read from model-lanes.json beside this file. The table is data so a
# retiering is one edit in one shipped file; a launcher that hardcoded a model would have to be found and
# changed per harness instead. Resolution never picks the lane: a caller that supplies neither -Lane nor
# -Model gets the CLI's own configured default, because guessing a lane from a prompt is how an expensive
# model ends up serving a rename.
function Resolve-AgentLaneModel {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('L0', 'L1', 'L2', 'L3')]
        [string] $Lane,

        [Parameter(Mandatory)]
        [ValidateSet('claude', 'codex')]
        [string] $Harness
    )

    $policyPath = Join-Path $PSScriptRoot 'model-lanes.json'
    if (-not (Test-Path -LiteralPath $policyPath -PathType Leaf)) {
        throw "The lane model table was not found beside the shared library: $policyPath"
    }

    $policy = Get-Content -LiteralPath $policyPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $entry = $policy.lanes.$Lane
    if (-not $entry) { throw "Lane '$Lane' is not defined in $policyPath." }

    $harnessEntry = $entry.$Harness
    if (-not $harnessEntry -or -not $harnessEntry.model) {
        throw "Lane '$Lane' defines no $Harness model in $policyPath."
    }

    return [pscustomobject]@{
        Model  = $harnessEntry.model
        Effort = $harnessEntry.effort
    }
}
