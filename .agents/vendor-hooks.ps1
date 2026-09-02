#!/usr/bin/env pwsh
<#
Copies only repo-invariant command-line utilities into a consuming repo and records their provenance.

Automatic hooks are delivered exclusively by the installed `process-standards` plugin for both Codex
and Claude. A consumer must run `scripts/provision-agent-standards.ps1` before work; copying hook code and
per-repository hook registrations creates a second owner that can drift from the plugin.

One tier remains for scripts a standard names at a stable repository-relative path:

  scripts/*.ps1       ->  <repo>/scripts/             repo-invariant executables a standard may name
                                                      outright, because every consumer has the same one

The second tier is what lets a standard write `./scripts/docker-health.ps1` as a constant rather than
inventing a parameter with one value. A script only belongs here when its BODY ports: no suite name, no
project path, no repo layout. `e2e.ps1` and `integration.ps1` do not qualify - they are lists of one
repo's test projects, so the standard states their invocation grammar and each repo owns the body.

One manifest covers both tiers, keyed by tier, so a consumer verifies every generated copy from one file.

  pwsh .agents/vendor-hooks.ps1 -Into C:\path\to\repo
  pwsh .agents/vendor-hooks.ps1 -Into C:\path\to\repo -Check   # verify only; non-zero exit if stale
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Into,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$intoRoot = (Resolve-Path $Into).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Read-Lf([string]$path) {
    return ([System.IO.File]::ReadAllText($path) -replace "`r`n", "`n")
}

function Get-Sha256([string]$text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
        return 'sha256:' + (($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    } finally { $sha.Dispose() }
}

$tiers = @(
    [pscustomobject]@{ Key = 'scripts'; Source = 'scripts'; Filter = '*.ps1'; Target = 'scripts' }
)

$dirty = (& git -C $repoRoot status --porcelain -- ($tiers | ForEach-Object { $_.Source }))
if ($dirty -and -not $Check) {
    throw "Canonical files are uncommitted; commit them first so the recorded provenance is real."
}

$manifest = [ordered]@{}
$stale = @()
$copied = 0

foreach ($tier in $tiers) {
    $source = Join-Path $repoRoot $tier.Source
    $target = Join-Path $intoRoot $tier.Target
    if (-not (Test-Path $target)) { throw "$Into has no $($tier.Target) directory to vendor into." }

    $files = @(Get-ChildItem -Path $source -File -Filter $tier.Filter | Sort-Object Name)
    if (-not $files) { throw "No canonical files found under $($tier.Source)." }

    $entries = [ordered]@{}
    foreach ($file in $files) {
        $body = Read-Lf $file.FullName
        $relative = "$($tier.Source)/$($file.Name)"
        # The commit that last touched THIS file, not repo HEAD - otherwise any unrelated commit
        # upstream makes every vendored copy report drift when only a provenance string moved.
        $commit = (& git -C $repoRoot log -1 --format=%H -- $relative)
        if (-not $commit) { throw "$relative has no commit yet; commit it first so the recorded provenance is real." }
        $commit = $commit.Trim()
        $entry = [ordered]@{
            source = 'tomjseery/process-agents'
            path   = $relative
        }
        $entry['commit'] = $commit
        $entry['sha256'] = Get-Sha256 $body
        $entries[$file.Name] = $entry

        $destination = Join-Path $target $file.Name
        $current = $null
        if (Test-Path $destination) { $current = Read-Lf $destination }
        if ($current -eq $body) { continue }
        $stale += $relative
        if ($Check) { continue }
        [System.IO.File]::WriteAllText($destination, ($body -replace "`n", "`r`n"), $utf8NoBom)
    }
    $manifest[$tier.Key] = $entries
    $copied += $files.Count
}

$manifestPath = Join-Path $intoRoot '.agents/hooks/vendored.json'
# Hand-formatted, because ConvertTo-Json indents differently between PowerShell 5.1 and 7 - which would
# make -Check report drift purely from which shell ran it.
$lines = @('{')
$tierIndex = 0
foreach ($tierKey in $manifest.Keys) {
    $tierIndex++
    $entries = $manifest[$tierKey]
    $lines += "  ""$tierKey"": {"
    $i = 0
    foreach ($name in $entries.Keys) {
        $i++
        $entry = $entries[$name]
        $lines += "    ""$name"": {"
        $fieldIndex = 0
        foreach ($field in $entry.Keys) {
            $fieldIndex++
            $fieldComma = ','
            if ($fieldIndex -eq $entry.Count) { $fieldComma = '' }
            $lines += "      ""$field"": ""$($entry[$field])""$fieldComma"
        }
        $entryComma = ','
        if ($i -eq $entries.Count) { $entryComma = '' }
        $lines += "    }$entryComma"
    }
    $tierComma = ','
    if ($tierIndex -eq $manifest.Count) { $tierComma = '' }
    $lines += "  }$tierComma"
}
$lines += '}'
$manifestBody = ($lines -join "`n") + "`n"
$manifestCurrent = $null
if (Test-Path $manifestPath) { $manifestCurrent = Read-Lf $manifestPath }
if ($manifestCurrent -ne $manifestBody) {
    $stale += '.agents/hooks/vendored.json'
    if (-not $Check) {
        [System.IO.File]::WriteAllText($manifestPath, ($manifestBody -replace "`n", "`r`n"), $utf8NoBom)
    }
}

if ($Check) {
    if ($stale.Count) {
        Write-Host "STALE in ${Into}: $($stale -join ', '). Run: pwsh .agents/vendor-hooks.ps1 -Into $Into"
        exit 1
    }
    Write-Host "vendored files in $Into are current ($copied file(s))"
    exit 0
}

Write-Host "vendored $copied file(s) into $Into"
foreach ($item in $stale) { Write-Host "  written: $item" }
