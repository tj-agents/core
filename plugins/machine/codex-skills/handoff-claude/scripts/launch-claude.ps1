[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $WorkingDirectory,

    [Parameter(Mandatory)]
    [string] $PromptPath,

    [string] $Title = 'Claude handoff',

    [string] $Model,

    [switch] $DangerouslySkipPermissions
)

$resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
$resolvedPromptPath = (Resolve-Path -LiteralPath $PromptPath -ErrorAction Stop).Path

if (-not (Test-Path -LiteralPath $resolvedWorkingDirectory -PathType Container)) {
    throw "Working directory is not a directory: $resolvedWorkingDirectory"
}

if (-not (Test-Path -LiteralPath $resolvedPromptPath -PathType Leaf)) {
    throw "Prompt path is not a file: $resolvedPromptPath"
}

$terminal = (Get-Command wt.exe -ErrorAction Stop).Source

# The native executable, never the NVM/npm shim: a shim launches the TUI through an extra process and
# degrades it to monochrome and non-interactive, the same failure handoff-codex records.
$claude = Join-Path $env:USERPROFILE '.local\bin\claude.exe'
if (-not (Test-Path -LiteralPath $claude -PathType Leaf)) {
    $claude = (Get-Command claude.exe -ErrorAction SilentlyContinue).Source
}

if ([string]::IsNullOrWhiteSpace($claude) -or -not (Test-Path -LiteralPath $claude -PathType Leaf)) {
    throw "The native Claude Code executable was not found. Looked for $env:USERPROFILE\.local\bin\claude.exe and claude.exe on PATH."
}

$instruction = "Read the file at $resolvedPromptPath and follow its instructions, working from the current directory."
$arguments = @(
    '--window', '0',
    'new-tab',
    '--startingDirectory', $resolvedWorkingDirectory,
    '--title', $Title,
    '--suppressApplicationTitle',
    $claude
)

if ($DangerouslySkipPermissions) {
    $arguments += '--dangerously-skip-permissions'
}

# Model selection is the caller's job, not this transport's: omit -Model and claude.exe falls back to
# its own configured default, same as an interactively launched session.
if ($Model) {
    $arguments += @('--model', $Model)
}

$arguments += $instruction

# Session state the parent exports. NO_COLOR=1 alone makes the child black and white; the CLAUDE_CODE_*
# set binds it to this session's messaging pipe and makes it act as a managed nested child.
# CLAUDE_CODE_GIT_BASH_PATH is machine configuration and is deliberately left alone.
$clearedVariables = @(
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

# Forced, not merely un-cleared: an automation-spawned wt.exe/claude.exe is not the interactive shell a
# human would have launched it from, so color/terminal-capability auto-detection cannot be trusted to land
# on a good value on its own. FORCE_COLOR is the de-facto Node CLI convention (chalk/supports-color) to
# force color on outright; TERM=xterm-256color is a known-good profile Windows Terminal fully supports,
# set explicitly rather than left blank so nothing falls back to a conservative dumb-terminal default.
$forcedVariables = @{
    FORCE_COLOR = '1'
    TERM        = 'xterm-256color'
}

$previousValues = @{}

foreach ($name in $clearedVariables) {
    $previousValues[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
foreach ($name in $forcedVariables.Keys) {
    $previousValues[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

try {
    foreach ($name in $clearedVariables) {
        [Environment]::SetEnvironmentVariable($name, $null, 'Process')
    }
    foreach ($name in $forcedVariables.Keys) {
        [Environment]::SetEnvironmentVariable($name, $forcedVariables[$name], 'Process')
    }

    & $terminal @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Windows Terminal exited with code $LASTEXITCODE"
    }
}
finally {
    foreach ($name in $previousValues.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousValues[$name], 'Process')
    }
}
