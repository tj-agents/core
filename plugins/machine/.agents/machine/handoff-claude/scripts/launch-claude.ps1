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

$ErrorActionPreference = 'Stop'

# The shared launch primitives, from the authored source layout or the installed package layout.
$agentCli = @(
    (Join-Path $PSScriptRoot '..\..\scripts\agent-cli.ps1'),
    (Join-Path $PSScriptRoot '..\..\..\resources\machine\utility\scripts\agent-cli.ps1')
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $agentCli) { throw "The shared agent-cli.ps1 library was not found relative to $PSScriptRoot." }
. $agentCli

$resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
$resolvedPromptPath = (Resolve-Path -LiteralPath $PromptPath -ErrorAction Stop).Path

if (-not (Test-Path -LiteralPath $resolvedPromptPath -PathType Leaf)) {
    throw "Prompt path is not a file: $resolvedPromptPath"
}

$claude = Resolve-ClaudeExecutable

$arguments = @()

if ($DangerouslySkipPermissions) {
    $arguments += '--dangerously-skip-permissions'
}

# Model selection is the caller's job, not this transport's: omit -Model and claude.exe falls back to
# its own configured default, same as an interactively launched session.
if ($Model) {
    $arguments += @('--model', $Model)
}

$arguments += "Read the file at $resolvedPromptPath and follow its instructions, working from the current directory."

# Forced, not merely un-cleared: an automation-spawned wt.exe/claude.exe is not the interactive shell a
# human would have launched it from, so colour/terminal-capability auto-detection cannot be trusted to land
# on a good value on its own. FORCE_COLOR is the de-facto Node CLI convention (chalk/supports-color) to
# force colour on outright; TERM=xterm-256color is a known-good profile Windows Terminal fully supports,
# set explicitly rather than left blank so nothing falls back to a conservative dumb-terminal default.
Invoke-AgentTerminalTab `
    -WorkingDirectory $resolvedWorkingDirectory `
    -Executable $claude `
    -Title $Title `
    -Arguments $arguments `
    -ForceEnvironment @{ FORCE_COLOR = '1'; TERM = 'xterm-256color' }
