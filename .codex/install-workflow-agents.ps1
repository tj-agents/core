[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot,
    [switch] $Apply
)

$ErrorActionPreference = 'Stop'

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
    # Only the two generated copies sit beside role files; the authored source does not.
    throw "No generated role files beside this installer: $source"
}
$source = (Resolve-Path -LiteralPath $source).ProviderPath
$target = Join-Path $project '.codex/agents'
Assert-NotReparsePoint (Join-Path $project '.codex')
Assert-NotReparsePoint $target
$changes = 0

foreach ($file in @(Get-ChildItem -LiteralPath $source -File -Filter 'workflow-*.toml' | Sort-Object Name)) {
    $destination = Join-Path $target $file.Name
    Assert-NotReparsePoint $destination
    $state =
        if (-not (Test-Path -LiteralPath $destination)) { 'ADD' }
        elseif ((Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash -eq
                (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash) { 'UNCHANGED' }
        else { 'REPLACE' }
    Write-Output "$state $destination"
    if ($state -eq 'UNCHANGED') { continue }
    $changes++
    if ($Apply) {
        New-Item -ItemType Directory -Force -Path $target | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    }
}

if (-not $Apply) {
    Write-Output "PREVIEW ONLY: $changes change(s); rerun with -Apply to install."
}
else {
    Write-Output "INSTALLED: $changes change(s), unrelated project agents preserved."
}
