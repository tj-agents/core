[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $WorkingDirectory,

    [Parameter(Mandatory)]
    [string] $PromptPath,

    [string] $Title = 'Claude handoff',

    [string] $Model,

    [ValidateSet('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7')]
    [string] $Lane,

    [switch] $Frontier,

    [switch] $DangerouslySkipPermissions
)

$ErrorActionPreference = 'Stop'

# The shared launch primitives, from the authored source layout or the installed package layout.
$agentCli = @(
    (Join-Path $PSScriptRoot '../../../scripts/agent-cli.ps1'),
    (Join-Path $PSScriptRoot '../../../resources/machine/scripts/agent-cli.ps1'),
    (Join-Path $PSScriptRoot '../../../../../resources/machine/scripts/agent-cli.ps1')
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

# An explicit -Model wins, a -Lane resolves through the shipped lane table, and neither leaves claude.exe
# on its own configured default, same as an interactively launched session. The lane is never guessed here:
# a transport that inferred one from the prompt would quietly decide the cost of every handoff. -Frontier is
# the tier no lane resolves to and tolerates no competing selection beside it, so passing it alongside
# -Lane or -Model is a contradiction to reject rather than an ambiguity to rank.
if ($Frontier -and ($Lane -or $Model)) {
    throw '-Frontier rejects -Lane and -Model beside it: the frontier tier is an explicit user request, not one selection among several.'
}
$tier = ''
if ($Frontier) {
    $Model = (Resolve-AgentLaneModel -Frontier -Harness 'claude').Model
    $tier = 'frontier -> '
}
elseif (-not $Model -and $Lane) {
    $Model = (Resolve-AgentLaneModel -Lane $Lane -Harness 'claude').Model
    $tier = "lane $Lane -> "
}

if ($Model) {
    $arguments += @('--model', $Model)
}

$arguments += "Read the file at $resolvedPromptPath and follow its instructions, working from the current directory."

Sync-ClaudeStandards -WorkingDirectory $resolvedWorkingDirectory -Claude $claude

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

$selection = if ($Model) { "$tier$Model" } else { 'the CLI default model' }
Write-Host "Launched claude handoff tab '$Title' in $resolvedWorkingDirectory on $selection with prompt $resolvedPromptPath"
