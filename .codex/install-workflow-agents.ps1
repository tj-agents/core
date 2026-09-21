[CmdletBinding()]
param(
    [string] $CodexHome,
    [string[]] $MigrateProjectRoot = @(),
    [switch] $Apply,
    [switch] $Verify,
    [switch] $Uninstall
)

$ErrorActionPreference = 'Stop'

if ($Verify -and ($Apply -or $Uninstall)) {
    throw '-Verify cannot be combined with -Apply or -Uninstall.'
}
if ($Uninstall -and $MigrateProjectRoot.Count) {
    throw '-MigrateProjectRoot is available only while installing or verifying profile roles.'
}

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
        throw "Codex agent delivery path cannot be a reparse point: $Path"
    }
}

function Resolve-CodexProfile([string] $ExplicitPath) {
    $candidate = $ExplicitPath
    if ([string]::IsNullOrWhiteSpace($candidate)) { $candidate = $env:CODEX_HOME }
    if ([string]::IsNullOrWhiteSpace($candidate)) {
        $userProfile = [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)
        if ([string]::IsNullOrWhiteSpace($userProfile)) {
            throw 'Cannot resolve the Codex profile. Pass -CodexHome or set CODEX_HOME.'
        }
        $candidate = Join-Path $userProfile '.codex'
    }
    $resolved = [System.IO.Path]::GetFullPath($candidate)
    $item = Get-Item -Force -LiteralPath $resolved -ErrorAction SilentlyContinue
    if ($null -ne $item -and -not $item.PSIsContainer) {
        throw "Codex profile is not a directory: $resolved"
    }
    return $resolved
}

function Resolve-ManagedProject([string] $Path) {
    $project = (Resolve-Path -LiteralPath $Path).ProviderPath
    if (-not (Test-Path -LiteralPath (Join-Path $project '.git'))) {
        throw "MigrateProjectRoot is not a Git checkout: $project"
    }
    Assert-NotReparsePoint (Join-Path $project '.codex')
    Assert-NotReparsePoint (Join-Path $project '.codex/agents')
    return $project
}

function Assert-ProfileRoles(
    [string] $Target,
    [System.IO.FileInfo[]] $SourceFiles,
    [string[]] $FormerManagedAgents
) {
    $problems = @()
    foreach ($file in $SourceFiles) {
        $destination = Join-Path $Target $file.Name
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
            $problems += "missing $destination"
        }
        elseif ((Get-FileSha256 $file.FullName) -ne (Get-FileSha256 $destination)) {
            $problems += "drifted $destination"
        }
    }
    foreach ($name in $FormerManagedAgents) {
        $destination = Join-Path $Target $name
        if (Test-Path -LiteralPath $destination) {
            $problems += "former managed role remains $destination"
        }
    }
    if ($problems.Count) {
        throw "Profile verification failed: $($problems -join '; ')"
    }
}

function Assert-ProjectsMigrated([string[]] $Projects, [string[]] $ManagedAgentNames) {
    $problems = @()
    foreach ($project in $Projects) {
        $target = Join-Path $project '.codex/agents'
        foreach ($name in $ManagedAgentNames) {
            $destination = Join-Path $target $name
            if (Test-Path -LiteralPath $destination) {
                $problems += $destination
            }
        }
    }
    if ($problems.Count) {
        throw "Project migration verification failed; managed role copies remain: $($problems -join ', ')"
    }
}

function Assert-ManagedAgentsAbsent([string] $Target, [string[]] $ManagedAgentNames) {
    $remaining = @($ManagedAgentNames | Where-Object {
        Test-Path -LiteralPath (Join-Path $Target $_)
    })
    if ($remaining.Count) {
        throw "Uninstall verification failed; managed profile roles remain: $($remaining -join ', ')"
    }
}

function Remove-DirectoryIfEmpty([string] $Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
    if (@(Get-ChildItem -Force -LiteralPath $Path).Count -eq 0) {
        Remove-Item -LiteralPath $Path -Force
    }
}

$source =
    if ((Split-Path -Leaf $PSScriptRoot) -eq '.codex') { Join-Path $PSScriptRoot 'agents' }
    else { Join-Path (Split-Path -Parent $PSScriptRoot) 'codex-agents' }
if (-not (Test-Path -LiteralPath $source)) {
    throw "No generated role files beside this installer: $source"
}
$source = (Resolve-Path -LiteralPath $source).ProviderPath

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
if (-not $sourceFiles.Count) { throw "No generated role files matched the delivery patterns in $source" }
$managedAgentNames = @(
    @($sourceFiles | ForEach-Object { $_.Name }) + $formerManagedAgents | Sort-Object -Unique
)

$profile = Resolve-CodexProfile $CodexHome
$target = Join-Path $profile 'agents'
Assert-NotReparsePoint $profile
Assert-NotReparsePoint $target
$migrationProjects = @(
    $MigrateProjectRoot | ForEach-Object { Resolve-ManagedProject $_ } | Sort-Object -Unique
)

if ($Verify) {
    Assert-ProfileRoles $target $sourceFiles $formerManagedAgents
    Assert-ProjectsMigrated $migrationProjects $managedAgentNames
    $suffix = if ($migrationProjects.Count) { '; managed project copies absent' } else { '' }
    Write-Output "VERIFIED: $($sourceFiles.Count) profile agent(s)$suffix."
    exit 0
}

$changes = 0
if ($Uninstall) {
    foreach ($name in $managedAgentNames) {
        $destination = Join-Path $target $name
        Assert-NotReparsePoint $destination
        if (-not (Test-Path -LiteralPath $destination)) { continue }
        $item = Get-Item -Force -LiteralPath $destination
        if ($item.PSIsContainer) { throw "Managed Codex agent is not a file: $destination" }
        Write-Output "REMOVE $destination"
        $changes++
        if ($Apply) { Remove-Item -LiteralPath $destination -Force }
    }
    if ($Apply) {
        Remove-DirectoryIfEmpty $target
        Assert-ManagedAgentsAbsent $target $managedAgentNames
        Write-Output "UNINSTALLED: $changes change(s), unrelated profile agents preserved."
    }
    else {
        Write-Output "PREVIEW ONLY: $changes change(s); rerun with -Uninstall -Apply to remove base-agents profile roles."
    }
    exit 0
}

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

if ($Apply) {
    # Migration is intentionally ordered after this verification. A failed or partial profile install can
    # never remove the only usable project-scoped copy.
    Assert-ProfileRoles $target $sourceFiles $formerManagedAgents
}

foreach ($project in $migrationProjects) {
    $projectTarget = Join-Path $project '.codex/agents'
    foreach ($name in $managedAgentNames) {
        $destination = Join-Path $projectTarget $name
        Assert-NotReparsePoint $destination
        if (-not (Test-Path -LiteralPath $destination)) { continue }
        $item = Get-Item -Force -LiteralPath $destination
        if ($item.PSIsContainer) { throw "Managed project Codex agent is not a file: $destination" }
        Write-Output "REMOVE $destination"
        $changes++
        if ($Apply) { Remove-Item -LiteralPath $destination -Force }
    }
    if ($Apply) { Remove-DirectoryIfEmpty $projectTarget }
}

if (-not $Apply) {
    Write-Output "PREVIEW ONLY: $changes change(s); rerun with -Apply to install."
}
else {
    Assert-ProjectsMigrated $migrationProjects $managedAgentNames
    Write-Output "INSTALLED: $changes change(s), unrelated profile and project agents preserved."
}
