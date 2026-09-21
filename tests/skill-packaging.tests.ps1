$ErrorActionPreference = 'Stop'

# Guards the rule in PACKAGING.md: a utility skill's own runtime dependencies must be shipped beside it in
# the generated plugin, resolved via the `<skill-directory>` placeholder, never through a machine-local
# path the plugin does not carry. `handoff-claude` and `handoff-codex` both required
# `~/.claude/routing/route.py` - a file this repo never packaged and had no authoritative source to
# package - so this check runs against the actual generated package, not the authored source, to prove
# what an install actually delivers.

$repository = Split-Path -Parent $PSScriptRoot
$pluginSkills = Join-Path $repository 'plugins\machine\skills'

function Get-MissingRequiredFiles {
    param(
        [Parameter(Mandatory)][string] $SkillDir,
        [Parameter(Mandatory)][string] $Name
    )

    $relative = if ($Name -eq 'bootstrap-capabilities') {
        'scripts\bootstrap_capabilities.py'
    } else {
        $harness = $Name.Substring('handoff-'.Length)
        "scripts\launch-$harness.ps1"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $SkillDir $relative) -PathType Leaf)) {
        return @($relative)
    }
    return @()
}
function Get-UnpackagedSkillDirectoryReferences {
    param([Parameter(Mandatory)][string] $SkillDir)

    $skillMd = Join-Path $SkillDir 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillMd -PathType Leaf)) { throw "No SKILL.md at $SkillDir." }
    $body = [System.IO.File]::ReadAllText($skillMd)

    $missing = @()
    foreach ($match in [regex]::Matches($body, "<skill-directory>[\\/]([^'`"\s]+)")) {
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

$targets = @('bootstrap-capabilities', 'handoff-claude', 'handoff-codex')

foreach ($name in $targets) {
    $dir = Join-Path $pluginSkills $name
    if (-not (Test-Path -LiteralPath $dir)) { throw "Generated package is missing $name. Run pwsh .agents/sync-generated.ps1." }

    $missing = @(Get-UnpackagedSkillDirectoryReferences -SkillDir $dir) + @(Get-MissingRequiredFiles -SkillDir $dir -Name $name)
    if ($missing.Count -gt 0) {
        throw "$name references packaged dependencies the generated plugin does not contain: $($missing -join ', ')"
    }

    $body = [System.IO.File]::ReadAllText((Join-Path $dir 'SKILL.md'))
    foreach ($forbidden in $forbiddenPatterns) {
        if ($body.Contains($forbidden)) {
            throw "$name/SKILL.md references '$forbidden', a path this repo does not package."
        }
    }
}

# Prove the packaged-dependency check has teeth: strip a shipped script from a scratch copy of the
# generated package and confirm detection actually fails it, rather than trivially passing everything.
$scratch = Join-Path ([System.IO.Path]::GetTempPath()) "base-agents-packaging-$([guid]::NewGuid().ToString('N'))"
try {
    $source = Join-Path $pluginSkills 'handoff-claude'
    Copy-Item -LiteralPath $source -Destination $scratch -Recurse
    Remove-Item -LiteralPath (Join-Path $scratch 'scripts\launch-claude.ps1') -Force

    $missing = @(Get-UnpackagedSkillDirectoryReferences -SkillDir $scratch) + @(Get-MissingRequiredFiles -SkillDir $scratch -Name 'handoff-claude')
    if ($missing.Count -eq 0) {
        throw 'Validation did not detect a packaged dependency removed from a generated skill copy.'
    }
} finally {
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS skill-packaging.tests.ps1'
