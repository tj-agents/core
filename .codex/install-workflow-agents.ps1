[CmdletBinding()]
param(
    [string[]] $ProjectRoot = @(),
    [string] $CodexHome,
    [string[]] $MigrateProjectRoot = @(),
    [switch] $Apply,
    [switch] $Verify,
    [switch] $Uninstall
)

$ErrorActionPreference = 'Stop'
$ownershipManifestName = '.base-agents-delivery.json'
$pendingManifestName = '.base-agents-delivery.pending.json'

if ($Verify -and ($Apply -or $Uninstall)) {
    throw '-Verify cannot be combined with -Apply or -Uninstall.'
}
if ($ProjectRoot.Count) {
    Write-Warning '-ProjectRoot is deprecated; use -MigrateProjectRoot. The profile is installed and verified before project copies are removed.'
    $MigrateProjectRoot = @($MigrateProjectRoot) + @($ProjectRoot)
}
if ($Uninstall -and $MigrateProjectRoot.Count) {
    throw '-MigrateProjectRoot and deprecated -ProjectRoot are available only while installing or verifying profile roles.'
}

function Get-BytesSha256([byte[]] $Bytes) {
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.BitConverter]::ToString($algorithm.ComputeHash($Bytes)).Replace('-', '')
    }
    finally {
        $algorithm.Dispose()
    }
}

function Get-FileSha256([string] $Path) {
    return Get-BytesSha256 ([System.IO.File]::ReadAllBytes($Path))
}

function Get-NormalizedTextSha256([string] $Path) {
    $text = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    $normalized = $text.Replace("`r`n", "`n").Replace("`r", "`n")
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    return Get-BytesSha256 ($utf8.GetBytes($normalized))
}

function Test-SafeDeliveryEntry([string] $Path) {
    # GetAttributes reads the entry itself, so a link whose target is gone is still refused. Returns
    # $false only for a path that does not exist; anything that prevents the check refuses the path.
    try {
        $attributes = [System.IO.File]::GetAttributes($Path)
    } catch [System.IO.FileNotFoundException], [System.IO.DirectoryNotFoundException] {
        return $false
    } catch {
        $reason = $_.Exception
        if ($null -ne $reason.InnerException) { $reason = $reason.InnerException }
        throw "Codex agent delivery path: cannot verify $Path is not a reparse point: $($reason.Message)"
    }
    if (($attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Codex agent delivery path contains a reparse point: $Path"
    }
    return $true
}

function Assert-SafeDeliveryPath([string] $Path) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($fullPath)
    $current = $root
    if (-not (Test-SafeDeliveryEntry $root)) { return }
    $relative = $fullPath.Substring($root.Length)
    # [char[]] is required: PowerShell 7 binds a plain array to Split(string, options), joining the
    # separators into one string that never matches, so no ancestor would be checked.
    foreach ($segment in @($relative.Split([char[]]@(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ), [System.StringSplitOptions]::RemoveEmptyEntries))) {
        $current = Join-Path $current $segment
        if (-not (Test-SafeDeliveryEntry $current)) { break }
    }
}

function Assert-AgentName([string] $Name, [string] $Label) {
    if ([string]::IsNullOrWhiteSpace($Name) -or
        [System.IO.Path]::GetFileName($Name) -ne $Name -or
        -not $Name.EndsWith('.toml', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Invalid $Label Codex agent name: $Name"
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
    Assert-SafeDeliveryPath $resolved
    $item = Get-Item -Force -LiteralPath $resolved -ErrorAction SilentlyContinue
    if ($null -ne $item -and -not $item.PSIsContainer) {
        throw "Codex profile is not a directory: $resolved"
    }
    return $resolved
}

function Resolve-ManagedProject([string] $Path) {
    $candidate = [System.IO.Path]::GetFullPath($Path)
    Assert-SafeDeliveryPath $candidate
    $project = (Resolve-Path -LiteralPath $candidate).ProviderPath
    Assert-SafeDeliveryPath $project
    if (-not (Test-Path -LiteralPath (Join-Path $project '.git'))) {
        throw "MigrateProjectRoot is not a Git checkout: $project"
    }
    Assert-SafeDeliveryPath (Join-Path $project '.codex')
    Assert-SafeDeliveryPath (Join-Path $project '.codex/agents')
    return $project
}

function Read-OwnershipManifest([string] $ManifestPath) {
    $owned = @{}
    if (-not (Test-Path -LiteralPath $ManifestPath)) { return $owned }
    Assert-SafeDeliveryPath $ManifestPath
    $item = Get-Item -Force -LiteralPath $ManifestPath
    if (-not $item.PSIsContainer -and $item.Length -ge 0) {
        try { $manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json }
        catch { throw "Invalid base-agents ownership state: $ManifestPath" }
    }
    else {
        throw "Base-agents ownership state is not a file: $ManifestPath"
    }
    if ($manifest.schema_version -ne 1 -or $manifest.owner -ne 'base-agents') {
        throw "Unsupported base-agents ownership state: $ManifestPath"
    }
    foreach ($entry in @($manifest.files)) {
        Assert-AgentName ([string] $entry.name) 'owned'
        $digest = ([string] $entry.sha256).ToUpperInvariant()
        if ($digest -notmatch '^[0-9A-F]{64}$' -or $owned.ContainsKey([string] $entry.name)) {
            throw "Invalid base-agents ownership entry in $ManifestPath"
        }
        $owned[[string] $entry.name] = $digest
    }
    return $owned
}

function Write-OwnershipManifest([string] $ManifestPath, [hashtable] $Owned) {
    Assert-SafeDeliveryPath $ManifestPath
    if (-not $Owned.Count) {
        if (Test-Path -LiteralPath $ManifestPath) {
            Assert-SafeDeliveryPath $ManifestPath
            Remove-Item -LiteralPath $ManifestPath -Force
        }
        return
    }
    $parent = Split-Path -Parent $ManifestPath
    Assert-SafeDeliveryPath $parent
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Assert-SafeDeliveryPath $parent
    $files = @($Owned.GetEnumerator() | Sort-Object Name | ForEach-Object {
        [ordered]@{ name = $_.Name; sha256 = $_.Value }
    })
    $value = [ordered]@{ schema_version = 1; owner = 'base-agents'; files = $files }
    $temporary = Join-Path $parent ('.base-agents-delivery.{0}.tmp' -f [Guid]::NewGuid().ToString('N'))
    Assert-SafeDeliveryPath $temporary
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($temporary, (($value | ConvertTo-Json -Depth 4) + "`n"), $utf8)
    Assert-SafeDeliveryPath $ManifestPath
    Move-Item -LiteralPath $temporary -Destination $ManifestPath -Force
}

function Test-KnownProjectAgent([string] $Path, [string] $Name, [hashtable] $KnownDigests) {
    if (-not $KnownDigests.ContainsKey($Name)) { return $false }
    $digest = Get-NormalizedTextSha256 $Path
    return @($KnownDigests[$Name]) -contains $digest
}

function Assert-ProfileRoles([string] $Target, [System.IO.FileInfo[]] $SourceFiles, [hashtable] $Owned) {
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
    foreach ($name in @($Owned.Keys)) {
        $destination = Join-Path $Target $name
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
            $problems += "owned role missing $destination"
        }
        elseif ((Get-FileSha256 $destination) -ne $Owned[$name]) {
            $problems += "owned role modified $destination"
        }
    }
    if ($problems.Count) {
        throw "Profile verification failed: $($problems -join '; ')"
    }
}

function Assert-ProjectsMigrated([string[]] $Projects, [string[]] $Names, [hashtable] $KnownDigests) {
    $problems = @()
    foreach ($project in $Projects) {
        $target = Join-Path $project '.codex/agents'
        foreach ($name in $Names) {
            $destination = Join-Path $target $name
            if ((Test-Path -LiteralPath $destination -PathType Leaf) -and
                (Test-KnownProjectAgent $destination $name $KnownDigests)) {
                $problems += $destination
            }
        }
    }
    if ($problems.Count) {
        throw "Project migration verification failed; base-agents-owned role copies remain: $($problems -join ', ')"
    }
}

function Remove-DirectoryIfEmpty([string] $Path) {
    Assert-SafeDeliveryPath $Path
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return }
    if (@(Get-ChildItem -Force -LiteralPath $Path).Count -eq 0) {
        Assert-SafeDeliveryPath $Path
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
foreach ($name in $formerManagedAgents) { Assert-AgentName $name 'former managed' }

$sourceFiles = @($generatedAgentPatterns |
    ForEach-Object { Get-ChildItem -LiteralPath $source -File -Filter $_ } |
    Sort-Object Name -Unique)
if (-not $sourceFiles.Count) { throw "No generated role files matched the delivery patterns in $source" }
$sourceNames = @($sourceFiles | ForEach-Object { $_.Name })
$projectManagedNames = @($sourceNames + $formerManagedAgents | Sort-Object -Unique)
$projectKnownDigests = @{}
foreach ($file in $sourceFiles) {
    $projectKnownDigests[$file.Name] = @((Get-NormalizedTextSha256 $file.FullName))
}
if ($null -ne $delivery.project_managed_agent_sha256) {
    foreach ($property in @($delivery.project_managed_agent_sha256.PSObject.Properties)) {
        Assert-AgentName $property.Name 'project managed'
        $digests = @($property.Value | ForEach-Object { ([string] $_).ToUpperInvariant() })
        if (-not $digests.Count -or @($digests | Where-Object { $_ -notmatch '^[0-9A-F]{64}$' }).Count) {
            throw "Invalid project managed digest inventory for $($property.Name)"
        }
        $existing = if ($projectKnownDigests.ContainsKey($property.Name)) { @($projectKnownDigests[$property.Name]) } else { @() }
        $projectKnownDigests[$property.Name] = @(@($existing) + @($digests) | Sort-Object -Unique)
    }
}

$profile = Resolve-CodexProfile $CodexHome
$target = Join-Path $profile 'agents'
$manifestPath = Join-Path $target $ownershipManifestName
$pendingPath = Join-Path $target $pendingManifestName
Assert-SafeDeliveryPath $target
$migrationProjects = @(
    $MigrateProjectRoot | ForEach-Object { Resolve-ManagedProject $_ } | Sort-Object -Unique
)
$ownedDigests = Read-OwnershipManifest $manifestPath
$pendingExists = Test-Path -LiteralPath $pendingPath
$pendingDigests = Read-OwnershipManifest $pendingPath
if ($pendingExists) {
    foreach ($name in @($pendingDigests.Keys)) {
        $destination = Join-Path $target $name
        Assert-SafeDeliveryPath $destination
        if (-not (Test-Path -LiteralPath $destination)) { continue }
        $item = Get-Item -Force -LiteralPath $destination
        if ($item.PSIsContainer) {
            throw "Interrupted profile install left a non-file agent target: $destination"
        }
        $destinationDigest = Get-FileSha256 $destination
        if ($destinationDigest -eq $pendingDigests[$name]) {
            # The prior apply completed this copy before interruption. The pending journal is proof of
            # ownership; adopting only this exact digest does not claim a pre-existing identical collision.
            $ownedDigests[$name] = $pendingDigests[$name]
        }
        elseif (-not ($ownedDigests.ContainsKey($name) -and
            $destinationDigest -eq $ownedDigests[$name])) {
            throw "Interrupted profile install has an unexpected agent state: $destination. Move it aside or restore the recorded file, then rerun -Apply."
        }
    }
}

if ($Verify) {
    if ($pendingExists) {
        throw "Profile verification found an interrupted install journal at $pendingPath. Rerun with -Apply to recover it."
    }
    Assert-ProfileRoles $target $sourceFiles $ownedDigests
    Assert-ProjectsMigrated $migrationProjects $projectManagedNames $projectKnownDigests
    $suffix = if ($migrationProjects.Count) { '; known base-agents project copies absent' } else { '' }
    Write-Output "VERIFIED: $($sourceFiles.Count) profile agent(s)$suffix."
    exit 0
}

$changes = 0
if ($Uninstall) {
    if ($pendingExists) {
        throw "Profile uninstall found an interrupted install journal at $pendingPath. Rerun with -Apply before uninstalling."
    }
    foreach ($name in @($ownedDigests.Keys | Sort-Object)) {
        $destination = Join-Path $target $name
        Assert-SafeDeliveryPath $destination
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf) -or
            (Get-FileSha256 $destination) -ne $ownedDigests[$name]) {
            throw "Refusing to uninstall a missing or modified owned profile agent: $destination. Restore the recorded file or move it aside, then rerun."
        }
    }
    foreach ($name in @($ownedDigests.Keys | Sort-Object)) {
        $destination = Join-Path $target $name
        Write-Output "REMOVE $destination"
        $changes++
        if ($Apply) {
            Assert-SafeDeliveryPath $destination
            Remove-Item -LiteralPath $destination -Force
        }
    }
    if ($Apply) {
        Write-OwnershipManifest $manifestPath @{}
        Remove-DirectoryIfEmpty $target
        Write-Output "UNINSTALLED: $changes change(s), unrelated profile agents preserved."
    }
    else {
        Write-Output "PREVIEW ONLY: $changes change(s); rerun with -Uninstall -Apply to remove owned base-agents profile roles."
    }
    exit 0
}

$installActions = @()
foreach ($file in $sourceFiles) {
    $destination = Join-Path $target $file.Name
    Assert-SafeDeliveryPath $destination
    $sourceDigest = Get-FileSha256 $file.FullName
    if (-not (Test-Path -LiteralPath $destination)) {
        $state = 'ADD'
    }
    else {
        $item = Get-Item -Force -LiteralPath $destination
        if ($item.PSIsContainer) { throw "Codex profile agent is not a file: $destination" }
        $destinationDigest = Get-FileSha256 $destination
        if ($destinationDigest -eq $sourceDigest) {
            $state = 'UNCHANGED'
        }
        elseif ($ownedDigests.ContainsKey($file.Name) -and $destinationDigest -eq $ownedDigests[$file.Name]) {
            $state = 'REPLACE'
        }
        else {
            throw "Refusing to overwrite an unowned or modified profile agent: $destination. Move the personal file aside or restore the recorded base-agents content, then rerun."
        }
    }
    $installActions += [pscustomobject]@{
        State = $state; File = $file; Destination = $destination; SourceDigest = $sourceDigest
    }
}

$retiredOwned = @()
foreach ($name in @($ownedDigests.Keys | Sort-Object)) {
    if ($sourceNames -contains $name) { continue }
    $destination = Join-Path $target $name
    Assert-SafeDeliveryPath $destination
    if (Test-Path -LiteralPath $destination) {
        $item = Get-Item -Force -LiteralPath $destination
        if ($item.PSIsContainer -or (Get-FileSha256 $destination) -ne $ownedDigests[$name]) {
            throw "Refusing to remove a modified retired profile agent: $destination. Move it aside or restore the recorded file, then rerun."
        }
        $retiredOwned += $destination
    }
}

$newOwned = @{}
foreach ($name in $ownedDigests.Keys) {
    if ($sourceNames -contains $name) { $newOwned[$name] = $ownedDigests[$name] }
}
foreach ($action in $installActions) {
    if ($action.State -ne 'UNCHANGED' -or $ownedDigests.ContainsKey($action.File.Name)) {
        $newOwned[$action.File.Name] = $action.SourceDigest
    }
}
$profileMutationRequired = @($installActions | Where-Object { $_.State -ne 'UNCHANGED' }).Count -gt 0 -or
    $retiredOwned.Count -gt 0
if ($Apply -and ($profileMutationRequired -or $pendingExists)) {
    # Persist intended ownership before the first role mutation. A retry can then adopt only exact files
    # proven by this journal, while pre-existing identical collisions remain deliberately unowned.
    Write-OwnershipManifest $pendingPath $newOwned
}

foreach ($action in $installActions) {
    Write-Output "$($action.State) $($action.Destination)"
    if ($action.State -eq 'UNCHANGED') { continue }
    $changes++
    if ($Apply) {
        Assert-SafeDeliveryPath $target
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Assert-SafeDeliveryPath $target
        Assert-SafeDeliveryPath $action.Destination
        $temporary = Join-Path $target ('.base-agents-delivery.{0}.tmp' -f [Guid]::NewGuid().ToString('N'))
        try {
            Assert-SafeDeliveryPath $temporary
            Copy-Item -LiteralPath $action.File.FullName -Destination $temporary
            if ((Get-FileSha256 $temporary) -ne $action.SourceDigest) {
                throw "Staged profile agent differs from its source: $($action.File.FullName)"
            }
            Assert-SafeDeliveryPath $action.Destination
            Move-Item -LiteralPath $temporary -Destination $action.Destination -Force
        }
        finally {
            if (Test-Path -LiteralPath $temporary) {
                Assert-SafeDeliveryPath $temporary
                Remove-Item -LiteralPath $temporary -Force
            }
        }
    }
}
foreach ($destination in $retiredOwned) {
    Write-Output "REMOVE $destination"
    $changes++
    if ($Apply) {
        Assert-SafeDeliveryPath $destination
        Remove-Item -LiteralPath $destination -Force
    }
}

if ($Apply) {
    Write-OwnershipManifest $manifestPath $newOwned
    # Project cleanup is intentionally ordered after this verification. A failed or partial profile
    # install can never remove the only usable project-scoped copy.
    Assert-ProfileRoles $target $sourceFiles $newOwned
    Write-OwnershipManifest $pendingPath @{}
}

foreach ($project in $migrationProjects) {
    $projectTarget = Join-Path $project '.codex/agents'
    foreach ($name in $projectManagedNames) {
        $destination = Join-Path $projectTarget $name
        Assert-SafeDeliveryPath $destination
        if (-not (Test-Path -LiteralPath $destination)) { continue }
        $item = Get-Item -Force -LiteralPath $destination
        if ($item.PSIsContainer) { throw "Candidate project Codex agent is not a file: $destination" }
        if (-not (Test-KnownProjectAgent $destination $name $projectKnownDigests)) {
            Write-Output "PRESERVE $destination"
            continue
        }
        Write-Output "REMOVE $destination"
        $changes++
        if ($Apply) {
            Assert-SafeDeliveryPath $destination
            Remove-Item -LiteralPath $destination -Force
        }
    }
    if ($Apply) { Remove-DirectoryIfEmpty $projectTarget }
}

if (-not $Apply) {
    Write-Output "PREVIEW ONLY: $changes change(s); rerun with -Apply to install."
}
else {
    Assert-ProjectsMigrated $migrationProjects $projectManagedNames $projectKnownDigests
    Write-Output "INSTALLED: $changes change(s), unrelated profile and project agents preserved."
}
