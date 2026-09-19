[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot,
    [switch] $Apply
)

$ErrorActionPreference = 'Stop'

function Get-FileSha256([string] $Path) {
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.IO.File]::ReadAllBytes($Path)
        return [System.BitConverter]::ToString($algorithm.ComputeHash($bytes)).Replace('-', '')
    }
    finally {
        $algorithm.Dispose()
    }
}

function Assert-NotReparsePoint([string] $Path) {
    $item = Get-Item -Force -LiteralPath $Path -ErrorAction SilentlyContinue
    if ($null -ne $item -and
        ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Project-scoped install target cannot be a reparse point: $Path"
    }
}

$project = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
if (-not (Test-Path -LiteralPath (Join-Path $project '.git'))) {
    throw "ProjectRoot is not a Git checkout: $project"
}

$source =
    if ((Split-Path -Leaf $PSScriptRoot) -eq '.codex') { Join-Path $PSScriptRoot 'agents' }
    else { Join-Path (Split-Path -Parent $PSScriptRoot) 'codex-agents' }
if (-not (Test-Path -LiteralPath $source)) {
    throw "No generated role files beside this installer: $source"
}
$source = (Resolve-Path -LiteralPath $source).ProviderPath
$target = Join-Path $project '.codex/agents'
Assert-NotReparsePoint (Join-Path $project '.codex')
Assert-NotReparsePoint $target
$changes = 0
$deliveryConfig =
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'agent-delivery.json')) {
        Join-Path $PSScriptRoot 'agent-delivery.json'
    }
    else {
        Join-Path (Split-Path -Parent $PSScriptRoot) 'workflows/hosts/agent-delivery.json'
    }
if (-not (Test-Path -LiteralPath $deliveryConfig)) {
    throw "No Codex agent delivery config beside this installer: $deliveryConfig"
}
$delivery = Get-Content -Raw -LiteralPath $deliveryConfig | ConvertFrom-Json
$generatedAgentPatterns = @($delivery.generated_agent_patterns)
if (-not $generatedAgentPatterns.Count -or $generatedAgentPatterns -contains '*.toml') {
    throw 'Codex agent delivery patterns must name generated families without matching every TOML file.'
}
$formerManagedAgents = @($delivery.former_managed_agents)
foreach ($name in $formerManagedAgents) {
    if ([string]::IsNullOrWhiteSpace($name) -or
        [System.IO.Path]::GetFileName($name) -ne $name -or
        -not $name.EndsWith('.toml', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Invalid former managed Codex agent name: $name"
    }
}

$sourceFiles = @($generatedAgentPatterns |
    ForEach-Object { Get-ChildItem -LiteralPath $source -File -Filter $_ } |
    Sort-Object Name -Unique)

foreach ($file in $sourceFiles) {
    $destination = Join-Path $target $file.Name
    Assert-NotReparsePoint $destination
    $state =
        if (-not (Test-Path -LiteralPath $destination)) { 'ADD' }
        elseif ((Get-FileSha256 $file.FullName) -eq (Get-FileSha256 $destination)) { 'UNCHANGED' }
        else { 'REPLACE' }
    Write-Output "$state $destination"
    if ($state -eq 'UNCHANGED') { continue }
    $changes++
    if ($Apply) {
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    }
}

foreach ($name in $formerManagedAgents) {
    $destination = Join-Path $target $name
    Assert-NotReparsePoint $destination
    if (-not (Test-Path -LiteralPath $destination)) { continue }
    $item = Get-Item -Force -LiteralPath $destination
    if ($item.PSIsContainer) { throw "Former managed Codex agent is not a file: $destination" }
    Write-Output "REMOVE $destination"
    $changes++
    if ($Apply) { Remove-Item -LiteralPath $destination -Force }
}
if (-not $Apply) {
    Write-Output "PREVIEW ONLY: $changes change(s); rerun with -Apply to install."
}
else {
    Write-Output "INSTALLED: $changes change(s), unrelated project agents preserved."
}
