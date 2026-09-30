[CmdletBinding()]
param(
    [string] $WorkingDirectory = (Get-Location).Path,

    [string] $Resume,

    [switch] $Continue,

    [string] $Prompt,

    [string] $PromptPath,

    [string] $Title = 'Claude',

    [string] $Model,

    [switch] $DangerouslySkipPermissions
)

$ErrorActionPreference = 'Stop'

# The shared launch primitives, from the authored source layout or the installed package layout.
$agentCli = @(
    (Join-Path $PSScriptRoot '..\..\scripts\agent-cli.ps1'),
    (Join-Path $PSScriptRoot '..\..\..\resources\machine\scripts\agent-cli.ps1'),
    (Join-Path $PSScriptRoot '..\..\..\..\resources\machine\scripts\agent-cli.ps1')
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $agentCli) { throw "The shared agent-cli.ps1 library was not found relative to $PSScriptRoot." }
. $agentCli

if ($Resume -and $Continue) {
    throw 'Pass -Resume for a specific session or -Continue for the most recent one, not both.'
}

if ($Prompt -and $PromptPath) {
    throw 'Pass -Prompt for a short instruction or -PromptPath for a prepared file, not both.'
}

# A prompt this long is no longer the short instruction -Prompt exists for, and a command line is the
# worst place to keep one: nothing on the receiving end can report a prompt that arrived damaged, and
# once the tab is gone the text is gone with it. handoff-claude takes only -PromptPath for this reason.
if ($Prompt.Length -gt 500) {
    throw "The inline -Prompt is $($Prompt.Length) characters. Write it to a file and pass -PromptPath instead; -Prompt is for a short instruction."
}

$resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path

$claude = Resolve-ClaudeExecutable

$arguments = @()

if ($Resume) { $arguments += @('--resume', $Resume) }
if ($Continue) { $arguments += '--continue' }

if ($DangerouslySkipPermissions) {
    $arguments += '--dangerously-skip-permissions'
}

if ($Model) {
    $arguments += @('--model', $Model)
}

if ($PromptPath) {
    $resolvedPromptPath = (Resolve-Path -LiteralPath $PromptPath -ErrorAction Stop).Path
    if (-not (Test-Path -LiteralPath $resolvedPromptPath -PathType Leaf)) {
        throw "Prompt path is not a file: $resolvedPromptPath"
    }
    $arguments += "Read the file at $resolvedPromptPath and follow its instructions, working from the current directory."
}
elseif ($Prompt) {
    $arguments += $Prompt
}

Sync-ClaudeStandards -WorkingDirectory $resolvedWorkingDirectory -Claude $claude

Invoke-AgentTerminalTab `
    -WorkingDirectory $resolvedWorkingDirectory `
    -Executable $claude `
    -Title $Title `
    -Arguments $arguments `
    -ForceEnvironment @{ FORCE_COLOR = '1'; TERM = 'xterm-256color' }

Write-Host "Launched claude tab '$Title' in $resolvedWorkingDirectory"
