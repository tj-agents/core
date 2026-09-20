#!/usr/bin/env pwsh
<#
Synchronizes installable plugin payloads from canonical shared definitions under `.agents/` and
host-only adapters under `.codex/` and `.claude/`. It never authors or rewrites those three source trees.

  pwsh .agents/sync-generated.ps1
  pwsh .agents/sync-generated.ps1 -Check
#>

[CmdletBinding()]
param([switch]$Check)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$script = Join-Path $repoRoot 'scripts/sync_plugin_packages.py'
$arguments = @('-B', $script, '--root', $repoRoot)
if ($Check) { $arguments += '--check' }
& python @arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }