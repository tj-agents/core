[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $WorkingDirectory,

    [Parameter(Mandatory)]
    [string] $PromptPath,

    [string] $Title = 'Codex handoff',

    [string] $Model,

    [ValidateSet('low', 'medium', 'high', 'xhigh', 'max', 'ultra')]
    [string] $ReasoningEffort,

    [string] $MinimumVersion = '0.154.0',

    [switch] $BypassHookTrust
)

$ErrorActionPreference = 'Stop'

$resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
$resolvedPromptPath = (Resolve-Path -LiteralPath $PromptPath -ErrorAction Stop).Path

if (-not (Test-Path -LiteralPath $resolvedWorkingDirectory -PathType Container)) {
    throw "Working directory is not a directory: $resolvedWorkingDirectory"
}

if (-not (Test-Path -LiteralPath $resolvedPromptPath -PathType Leaf)) {
    throw "Prompt path is not a file: $resolvedPromptPath"
}

$terminal = (Get-Command wt.exe -ErrorAction Stop).Source

function ConvertTo-CodexVersion([string]$text) {
    $match = [regex]::Match($text, '(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?')
    if (-not $match.Success) { return $null }
    return [pscustomobject]@{
        Core       = @([int]$match.Groups[1].Value, [int]$match.Groups[2].Value, [int]$match.Groups[3].Value)
        PreRelease = $match.Groups[4].Value
        Text       = $match.Value
    }
}

function Compare-CodexVersion($left, $right) {
    for ($i = 0; $i -lt 3; $i++) {
        if ($left.Core[$i] -ne $right.Core[$i]) { return $left.Core[$i].CompareTo($right.Core[$i]) }
    }
    # A prerelease ranks BELOW the release it precedes, so 0.151.0-alpha.7.1 loses to 0.151.0. Ranking by
    # file date instead is what silently selected a three-versions-stale alpha over the current CLI.
    $leftIsRelease = [string]::IsNullOrEmpty($left.PreRelease)
    $rightIsRelease = [string]::IsNullOrEmpty($right.PreRelease)
    if ($leftIsRelease -ne $rightIsRelease) {
        if ($leftIsRelease) { return 1 }
        return -1
    }
    if ($leftIsRelease) { return 0 }

    $leftParts = $left.PreRelease -split '\.'
    $rightParts = $right.PreRelease -split '\.'
    for ($i = 0; $i -lt [Math]::Max($leftParts.Count, $rightParts.Count); $i++) {
        if ($i -ge $leftParts.Count) { return -1 }
        if ($i -ge $rightParts.Count) { return 1 }
        $leftPart = $leftParts[$i]
        $rightPart = $rightParts[$i]
        $order = if (($leftPart -match '^\d+$') -and ($rightPart -match '^\d+$')) {
            ([int]$leftPart).CompareTo([int]$rightPart)
        } else {
            [string]::CompareOrdinal($leftPart, $rightPart)
        }
        if ($order -ne 0) { return $order }
    }
    return 0
}

$candidatePaths = [System.Collections.Generic.List[string]]::new()

# The npm package is a JavaScript entry point over a vendored native binary per platform, and the entry
# point is what lands on PATH. Launching that shim is the path that degrades the TUI to monochrome and
# non-interactive, so the vendored executable underneath it is launched instead - identical bits, without
# the node process in front.
$shim = @(Get-Command codex -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)[0]
if ($shim) {
    $packageRoot = Join-Path (Split-Path -Parent $shim.Source) 'node_modules/@openai/codex'
    if (Test-Path -LiteralPath $packageRoot) {
        foreach ($found in @(Get-ChildItem -Path (Join-Path $packageRoot 'node_modules/@openai/codex-*/vendor/*/bin/codex.exe') -ErrorAction SilentlyContinue)) {
            $candidatePaths.Add($found.FullName)
        }
    }
}

# The desktop app caches each downloaded runtime in its own hash-named directory and adds rather than
# replaces, so this folder accumulates stale payloads instead of holding only the current build.
$desktopBin = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin'
if (Test-Path -LiteralPath $desktopBin) {
    foreach ($found in @(Get-ChildItem -LiteralPath $desktopBin -Filter codex.exe -File -Recurse -ErrorAction SilentlyContinue)) {
        $candidatePaths.Add($found.FullName)
    }
}

$candidates = @()
foreach ($path in @($candidatePaths | Select-Object -Unique)) {
    $version = ConvertTo-CodexVersion ((& $path --version 2>&1) | Out-String)
    if ($null -eq $version) { continue }
    $candidates += [pscustomobject]@{ Path = $path; Version = $version }
}

if (-not $candidates) {
    throw "No native Codex executable answered --version. Looked beside the ``codex`` shim on PATH for the npm package's vendored binary, and under $desktopBin."
}

$codex = $candidates[0]
foreach ($candidate in $candidates) {
    if ((Compare-CodexVersion $candidate.Version $codex.Version) -gt 0) { $codex = $candidate }
}

$minimum = ConvertTo-CodexVersion $MinimumVersion
if ($null -eq $minimum) { throw "MinimumVersion is not a version: $MinimumVersion" }

if ((Compare-CodexVersion $codex.Version $minimum) -lt 0) {
    $inventory = (@($candidates | ForEach-Object { "  $($_.Version.Text)`t$($_.Path)" }) -join "`n")
    throw @"
The newest native Codex executable found is $($codex.Version.Text), below the required $MinimumVersion.
The model roster is gated on the CLI version, so launching this build would silently drop newer models.
Update with: npm install -g @openai/codex@latest
Found:
$inventory
"@
}

$instruction = "Read the file at $resolvedPromptPath and follow its instructions, working from the current directory."
$arguments = @(
    '--window', '0',
    'new-tab',
    '--startingDirectory', $resolvedWorkingDirectory,
    '--title', $Title,
    '--suppressApplicationTitle',
    $codex.Path,
    '--cd', $resolvedWorkingDirectory
)

if ($Model) {
    $arguments += @('--model', $Model)
}

if ($ReasoningEffort) {
    $arguments += @('--config', "model_reasoning_effort=$ReasoningEffort")
}

if ($BypassHookTrust) {
    $arguments += '--dangerously-bypass-hook-trust'
}

$arguments += $instruction

# Session state a Claude Code parent exports. NO_COLOR=1 alone makes the child black and white, and the
# CLAUDE_CODE_* set binds it to that session's messaging pipe and makes it act as a managed nested child.
# TERM is CLEARED, never forced - the opposite of handoff-claude, and not an oversight. Claude Code
# exports TERM=xterm-256color; Codex is a Rust/crossterm binary, and on native Windows an unset TERM is
# what selects the console's truecolor path. Handing it a POSIX terminfo name instead caps the palette at
# 256 colours and visibly wrecks the theme. Do not "align" this with the Claude launcher.
$clearedVariables = @(
    'NO_COLOR',
    'TERM',
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

# Only NO_COLOR has to go for colour to come back, and the binary reads it. Nothing else here is forced:
# every capability variable this launcher could set is one Windows Terminal and the console already
# negotiate correctly for a native child, and the one that was set - TERM - is what broke the theme.
$forcedVariables = @{}

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

Write-Host "Launched codex-cli $($codex.Version.Text) from $($codex.Path)"
