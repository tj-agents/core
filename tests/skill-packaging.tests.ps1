$ErrorActionPreference = 'Stop'

# Guards the rule in PACKAGING.md: a utility skill's own runtime dependencies must be shipped beside it in
# the generated plugin, resolved via the `<skill-directory>` placeholder, never through a machine-local
# path the plugin does not carry. `handoff-claude` and `handoff-codex` both required
# `~/.claude/routing/route.py` - a file this repo never packaged and had no authoritative source to
# package - so this check runs against the actual generated package, not the authored source, to prove
# what an install actually delivers.

$repository = Split-Path -Parent $PSScriptRoot
$pluginRoot = Join-Path $repository 'plugins\machine'
# A host adapter's generated SKILL.md is only a redirect to the canonical copy below -- its own body
# carries no `<skill-directory>` references and no forbidden-path strings to find. The canonical body is
# what actually says `<skill-directory>`, and that placeholder means the adapter folder a host loaded it
# from (one of these two), never the canonical folder itself: a host never resolves it against
# `.agents/machine/utility/`. So the canonical body is read once per skill, and its references are
# checked against each adapter folder in turn.
$canonicalSkills = Join-Path $pluginRoot '.agents\machine\utility'
$adapterRoots = @(
    (Join-Path $pluginRoot 'skills')
    (Join-Path $pluginRoot 'codex-skills')
)

$script:RequiredSkillScripts = @{
    'bootstrap-capabilities' = 'scripts\bootstrap_capabilities.py'
    'handoff-claude'         = 'scripts\launch_claude.py'
    'handoff-codex'          = 'scripts\launch_codex.py'
    'followup-codex'         = 'scripts\codex_followup.py'
    'open-claude'            = 'scripts\open_claude.py'
}

function Get-MissingRequiredFiles {
    param(
        [Parameter(Mandatory)][string] $SkillDir,
        [Parameter(Mandatory)][string] $Name
    )

    $relative = $script:RequiredSkillScripts[$Name]
    if (-not $relative) { throw "No required script is mapped for skill '$Name'; add it to `$RequiredSkillScripts." }
    if (-not (Test-Path -LiteralPath (Join-Path $SkillDir $relative) -PathType Leaf)) {
        return @($relative)
    }
    return @()
}

function Get-UnpackagedSkillDirectoryReferences {
    param(
        [Parameter(Mandatory)][string] $Body,
        [Parameter(Mandatory)][string] $SkillDir
    )

    $missing = @()
    foreach ($match in [regex]::Matches($Body, "<skill-directory>[\\/]([^'`"\s]+)")) {
        $relative = $match.Groups[1].Value -replace '/', '\'
        $target = Join-Path $SkillDir $relative
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            $missing += $relative
        }
    }
    return $missing
}

# Machine-local path shapes that name a file this repo cannot ship: a caller's home directory, username,
# or an unpackaged path outside the skill's own folder. This is the exact shape of the confirmed defect.
$forbiddenPatterns = @('routing/route.py', '.claude\routing', '$env:USERPROFILE', '%USERPROFILE%', '~/', '~\')

# Every mapped skill, sorted for a stable run order; adding a skill to $RequiredSkillScripts is now the
# only place that needs to change to bring it under this check.
$targets = @($script:RequiredSkillScripts.Keys | Sort-Object)

foreach ($name in $targets) {
    $canonicalDir = Join-Path $canonicalSkills $name
    if (-not (Test-Path -LiteralPath $canonicalDir)) {
        throw "Generated package is missing the canonical definition of $name at $canonicalDir. Run pwsh .agents/sync-generated.ps1."
    }
    $canonicalBody = [System.IO.File]::ReadAllText((Join-Path $canonicalDir 'SKILL.md'))

    foreach ($forbidden in $forbiddenPatterns) {
        if ($canonicalBody.Contains($forbidden)) {
            throw "$name's canonical SKILL.md ($canonicalDir) references '$forbidden', a path this repo does not package."
        }
    }

    foreach ($adapterRoot in $adapterRoots) {
        $adapterDir = Join-Path $adapterRoot $name
        if (-not (Test-Path -LiteralPath $adapterDir)) {
            throw "Generated package is missing $name under $adapterRoot. Run pwsh .agents/sync-generated.ps1."
        }

        $missing = @(Get-UnpackagedSkillDirectoryReferences -Body $canonicalBody -SkillDir $adapterDir) +
                   @(Get-MissingRequiredFiles -SkillDir $adapterDir -Name $name)
        if ($missing.Count -gt 0) {
            throw "$name's canonical <skill-directory> references or required script do not resolve under ${adapterDir}: $($missing -join ', ')"
        }
    }
}

# Prove the packaged-dependency check has teeth: strip a shipped script from a scratch copy of an adapter
# folder and confirm detection actually fails it, rather than trivially passing everything.
$scratch = Join-Path ([System.IO.Path]::GetTempPath()) "base-agents-packaging-$([guid]::NewGuid().ToString('N'))"
try {
    $source = Join-Path $pluginRoot 'skills\handoff-claude'
    Copy-Item -LiteralPath $source -Destination $scratch -Recurse
    Remove-Item -LiteralPath (Join-Path $scratch 'scripts\launch_claude.py') -Force

    $canonicalBody = [System.IO.File]::ReadAllText((Join-Path $canonicalSkills 'handoff-claude\SKILL.md'))
    $missing = @(Get-UnpackagedSkillDirectoryReferences -Body $canonicalBody -SkillDir $scratch) +
               @(Get-MissingRequiredFiles -SkillDir $scratch -Name 'handoff-claude')
    if ($missing.Count -eq 0) {
        throw 'Validation did not detect a packaged dependency removed from a generated skill copy.'
    }
} finally {
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS skill-packaging.tests.ps1'
