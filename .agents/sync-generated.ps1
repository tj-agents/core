#!/usr/bin/env pwsh
<#
Regenerates everything derived from `.agents/`, `.claude/hooks/`, `.codex/hooks/`, and `standards/` - the
only places anything is authored.

Two skill shapes coexist, chosen per domain:

- **Self-contained** (`process`): the SKILL.md body IS the standard. `@`-import does not work inside a
  SKILL.md (only CLAUDE.md/AGENTS.md expand it), and a router that only points at a separate doc costs a
  guaranteed-needed Read tool call for content the skill will never NOT need - so for a domain with no
  external pairing, the split bought nothing. A self-contained router declares `domain:` in front matter
  instead of a doc path, since there is no doc path left to derive it from.
- **Routed** (`dotnet`, `react`): the authored doc under `standards/<domain>/` is the payload and the
  authored skill maps its name and description to that doc. Generated discovered skills inline the doc
  so invoking one loads the standard in a single step, while the authored path remains mirrored against
  the external `dotagents`/`react-agents` repos for pairing.

Authored:
  standards/<domain>/**.md                routed-domain standards only (self-contained domains have none)
  .agents/skills/<name>/SKILL.md          routed: front matter + the root-relative path of its doc
                                          self-contained: front matter (with `domain:`) + the standard itself
  .agents/skills/<name>/**                anything else beside a SKILL.md - a script the skill invokes, or
                                          detail it names by reference - copied into every generated copy
  .agents/hooks/*.py                      the hook mechanisms, shared verbatim by both harnesses
  .agents/routes/*.json                   the registry naming which repo gets which route table, and one
                                          table per registered kind, emitted by .agents/gen_skill_routes.py
  .agents/hooks/codex-hooks.json          Codex's own wiring - Codex's native convention already is
                                          .agents/, same reason its marketplace manifest lives there too
  .claude/hooks/hooks.json,               Claude's own wiring, mirroring .claude/skills/. Inert for a repo
    run-claude-hook.sh                    Claude Code opens directly - project hooks there come from
                                          .claude/settings.json, not a hooks.json file - so this is purely
                                          the authoring home the generator assembles into the shipped plugin.
  .agents/plugins/marketplace.json         Codex marketplace
  .claude-plugin/marketplace.json          Claude marketplace
  plugins/<p>/.codex-plugin/plugin.json    Codex plugin manifests

Generated:
  .claude/skills/<name>/SKILL.md          routed: front matter plus the canonical doc body, so discovery
                                          loads the standard once. self-contained: verbatim copy.
  plugins/<p>/skills/<name>/SKILL.md      routed: front matter plus the canonical doc body, for the same
                                          single-load behavior. self-contained: verbatim copy.
  <root>/<name>/** beside each SKILL.md   verbatim copy of the authored skill's other files, into all three
                                          generated roots. A plugin cannot reference outside its own root,
                                          so a skill that invokes a script must carry it.
  plugins/<p>/standards/**                full copy of the routed domains' tree, for that same reason.
  plugins/<p>/routes/*                    full copy of the route registry and its tables, shipped by the
                                          plugin that OWNS them, so a registered repo needs no table of its
                                          own. That is the hook's own plugin only where one repo owns both;
                                          the router resolves a registry from any installed plugin.
  plugins/<p>/hooks/*                     full copy of the hook AND its hooks.json wiring, generated so
                                          the matcher cannot drift from the tool names the hook acts on.
                                          Only the ONE plugin payloads.json names as `hooks` gets it -
                                          a copy per plugin fires the router once per installed plugin.
                                          - that drift shipped a plugin inert for every Codex write.
  standards/<domain>/INDEX.md             the tree answers "where is it"; this answers "did I document
                                          this" without opening anything.

Refuses to generate when the two structures disagree: a router naming a doc that does not exist, a doc
no router points at, or two routers claiming one doc. A tree and a skill namespace that can drift is
exactly how 754 lines of frontend law ended up with zero inbound links.

  pwsh .agents/sync-generated.ps1
  pwsh .agents/sync-generated.ps1 -Check   # verify only; non-zero exit if anything is stale
#>

[CmdletBinding()]
param([switch]$Check)

$ErrorActionPreference = 'Stop'

$repoRoot     = Split-Path -Parent $PSScriptRoot
$canonical    = Join-Path $repoRoot '.agents/skills'
$claudeWorkflowSkills = Join-Path $repoRoot '.claude/workflow-skills'
$codexWorkflowSkills = Join-Path $repoRoot '.codex/workflow-skills'
$hookSource   = Join-Path $repoRoot '.agents/hooks'
$routeSource  = Join-Path $repoRoot '.agents/routes'
$workflowSource = Join-Path $repoRoot '.agents/workflows'
$claudeHookSource = Join-Path $repoRoot '.claude/hooks'
$codexHookSource = Join-Path $repoRoot '.codex/hooks'
$manifest     = Join-Path $repoRoot '.agents/plugins/marketplace.json'
$claudeManifest = Join-Path $repoRoot '.claude-plugin/marketplace.json'
$standardsDir = Join-Path $repoRoot 'standards'
$utf8NoBom    = New-Object System.Text.UTF8Encoding($false)

$INDEX_NAME = 'INDEX.md'

function Read-Lf([string]$path) {
    return ([System.IO.File]::ReadAllText($path) -replace "`r`n", "`n")
}

function Escape-TomlString([string]$value) {
    return $value.Replace('\', '\\').Replace('"', '\"')
}

function Get-HostWorkflowSkills([string]$source, [string]$hostName) {
    if (-not (Test-Path $source)) { return [ordered]@{} }
    $skills = [ordered]@{}
    foreach ($dir in @(Get-ChildItem -Path $source -Directory | Sort-Object Name)) {
        $skill = Join-Path $dir.FullName 'SKILL.md'
        if (-not (Test-Path $skill)) {
            throw "$hostName workflow skill '$($dir.Name)' has no SKILL.md."
        }
        $body = Read-Lf $skill
        $declaredName = Get-FrontMatterField $body 'name' "$hostName/$($dir.Name)"
        if ($declaredName -ne $dir.Name) {
            throw "$hostName workflow skill '$($dir.Name)' declares name '$declaredName'; folder and name must match."
        }
        $skills[$dir.Name] = $body
    }
    return $skills
}

# Kept to string trimming rather than [Path]::GetRelativePath / Resolve-Path -RelativeBasePath: both
# need PowerShell 7, and this repo is cloned onto machines that only have 5.1.
function To-RepoRelative([string]$fullPath, [string]$base) {
    $separator = [System.IO.Path]::DirectorySeparatorChar
    $normalizedBase = ((Resolve-Path -LiteralPath $base).ProviderPath.TrimEnd('\', '/')) + $separator
    $full = (Resolve-Path -LiteralPath $fullPath).ProviderPath
    if (-not $full.StartsWith($normalizedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$full is not under $normalizedBase."
    }
    return ($full.Substring($normalizedBase.Length) -replace '\\', '/')
}

function Get-FrontMatterField([string]$text, [string]$field, [string]$name) {
    $match = [regex]::Match($text, "(?s)\A---\n.*?^${field}:[ \t]*(.+?)\n(?:[a-zA-Z-]+:|---)", 'Multiline')
    if (-not $match.Success) {
        throw "$name/SKILL.md has no parsable ``${field}:`` in its front matter."
    }
    $value = $match.Groups[1].Value.Trim() -replace "\s*\n\s*", " "
    # A bare colon-space anywhere in an unquoted YAML scalar silently truncates the value, and the
    # description is what decides whether the skill loads at all - a truncated one never fires.
    if ($field -eq 'description' -and $value -match ':\s') {
        throw "$name/SKILL.md description contains a colon-space, which breaks the YAML scalar: $value"
    }
    return $value
}

# The router's single authored fact about its payload: the root-relative path of its doc, in backticks.
# Parsed rather than held in a side table, because a second structure is a second thing that drifts.
# Anchored to the actual routing sentence (not a bare substring search) so a self-contained skill's
# inlined body can freely mention another skill's old doc path in prose without being misread as a route.
# Returns $null for a self-contained skill: its content IS the payload, so it names no doc to route to.
function Get-RoutedDoc([string]$text, [string]$name) {
    $match = [regex]::Match($text, 'The standard is `(standards/[^`]+\.md)` in `[^`]+`, deployed to')
    if (-not $match.Success) { return $null }
    return $match.Groups[1].Value
}

# A self-contained skill (no routed doc) still has to ship in exactly one plugin, so it declares its
# domain directly in front matter. A routed skill's domain is derived from its doc's path instead -
# a second authored fact would just be a second thing to drift from the first.
function Get-OptionalFrontMatterField([string]$text, [string]$field) {
    $match = [regex]::Match($text, "(?s)\A---\n.*?^${field}:[ \t]*(.+?)\n(?:[a-zA-Z-]+:|---)", 'Multiline')
    if (-not $match.Success) { return $null }
    return $match.Groups[1].Value.Trim()
}

function Expand-RoutedSkill(
    [string]$body,
    [string]$docBody,
    [string]$doc,
    [string]$payloadRootPrefix,
    [string]$name
) {
    $frontMatter = [regex]::Match($body, '(?s)\A---\n.*?^---\n', 'Multiline')
    if (-not $frontMatter.Success) {
        throw "$name/SKILL.md has no complete front matter to combine with its routed document."
    }
    $docDirectory = Split-Path -Parent (Join-Path $repoRoot $doc)
    $expanded = [regex]::Replace(
        $docBody,
        '\]\((?<target>\.\.?/[^)#]+\.md)(?<anchor>#[^)]+)?\)',
        {
            param($match)
            $target = [System.IO.Path]::GetFullPath((Join-Path $docDirectory $match.Groups['target'].Value))
            $relative = To-RepoRelative $target $repoRoot
            return "]($payloadRootPrefix$relative$($match.Groups['anchor'].Value))"
        })
    return $frontMatter.Value.TrimEnd() + "`n`n" + $expanded.TrimStart()
}

# A skill's payload is its whole folder, not only SKILL.md - a launcher skill names an executable beside
# it, and instructions shipped without that executable are a skill that cannot run. This must be called
# for every generated copy: the prune pass deletes anything under a generated root this run did not
# author, so an unemitted sibling is not merely missing from the copy, it is removed from it.
function Add-SkillSiblings([string]$prefix, $router) {
    foreach ($sibling in $router.Siblings) {
        $generated["$prefix/$($router.Name)/$($sibling.Relative)"] = Read-Lf $sibling.FullName
    }
}

# Skills stay flat: discovery is <root>/skills/*/SKILL.md and does not recurse. Only content nests.
$skillDirs = @(Get-ChildItem -Path $canonical -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | Sort-Object Name)
if (-not $skillDirs) { throw "No canonical skills found under .agents/skills." }

$routers = [ordered]@{}
foreach ($dir in $skillDirs) {
    $text = Read-Lf (Join-Path $dir.FullName 'SKILL.md')
    $doc = Get-RoutedDoc $text $dir.Name
    if ($doc) {
        $domain = ($doc -split '/')[1]
    } else {
        $domain = Get-OptionalFrontMatterField $text 'domain'
        if (-not $domain) {
            throw "$($dir.Name)/SKILL.md is self-contained (no routed doc) but declares no ``domain:`` front matter, so no plugin knows to ship it."
        }
    }
    # Progressive disclosure: a sibling file beside SKILL.md holds detail the skill names by reference
    # rather than inlining, so the always-loaded body stays under the compaction re-attachment budget.
    # Skill discovery does not recurse (only SKILL.md is discovered), but a sibling's own content may.
    $siblings = @(Get-ChildItem -Path $dir.FullName -Recurse -File |
        Where-Object { $_.Name -ne 'SKILL.md' } |
        ForEach-Object { [pscustomobject]@{
            Relative = ($_.FullName.Substring($dir.FullName.Length + 1) -replace '\\', '/')
            FullName = $_.FullName
        } })
    $routers[$dir.Name] = [pscustomobject]@{
        Name        = $dir.Name
        Body        = $text
        Description = Get-FrontMatterField $text 'description' $dir.Name
        Doc         = $doc
        Domain      = $domain
        Siblings    = $siblings
    }
}

$claudeHostSkills = Get-HostWorkflowSkills $claudeWorkflowSkills 'Claude'
$codexHostSkills = Get-HostWorkflowSkills $codexWorkflowSkills 'Codex'
foreach ($name in @($claudeHostSkills.Keys + $codexHostSkills.Keys | Select-Object -Unique)) {
    if ($routers.Contains($name)) {
        throw "Host workflow skill '$name' collides with the shared .agents/skills namespace."
    }
}

# The standards tree is walked recursively - nesting is the whole point of the tree.
$docs = @()
if (Test-Path $standardsDir) {
    $docs = @(Get-ChildItem -Path $standardsDir -Recurse -File -Filter '*.md' |
        Where-Object { $_.Name -ne $INDEX_NAME } |
        ForEach-Object { To-RepoRelative $_.FullName $repoRoot } |
        Sort-Object)
}

# Conditional rules are delivered at SessionStart by the profile resolver, never by a skill: a rule must
# not be loadable in a repository whose profile does not declare it subject to the rule. Their owner is
# the catalogue that carries each one's applies_when, so they are reconciled against that below.
$RULES_PREFIX = 'standards/rules/'
$ruleDocs = @($docs | Where-Object { $_.StartsWith($RULES_PREFIX) })
$docs = @($docs | Where-Object { -not $_.StartsWith($RULES_PREFIX) })

# Neither structure may grow an orphan. Self-contained routers (no Doc) name nothing here to check -
# their content is the payload, so there is no doc-side owner or existence to reconcile against.
$problems = @()
foreach ($router in $routers.Values) {
    if ($router.Doc -and $docs -notcontains $router.Doc) {
        $problems += "skill '$($router.Name)' routes to '$($router.Doc)', which does not exist."
    }
}
foreach ($doc in $docs) {
    $owners = @($routers.Values | Where-Object { $_.Doc -eq $doc } | Select-Object -ExpandProperty Name)
    if ($owners.Count -eq 0) {
        $problems += "doc '$doc' has no routing skill, so nothing loads it."
    }
    if ($owners.Count -gt 1) {
        $problems += "doc '$doc' is routed by $($owners.Count) skills ($($owners -join ', ')); it needs exactly one owner."
    }
}
$cataloguePath = Join-Path $repoRoot 'standards/rules/catalogue.json'
if ($ruleDocs -or (Test-Path $cataloguePath)) {
    if (-not (Test-Path $cataloguePath)) {
        $problems += "standards/rules/ carries docs but no catalogue.json, so no profile can select them."
    } else {
        $catalogued = @((Get-Content -Raw -Encoding UTF8 $cataloguePath | ConvertFrom-Json).rules |
            ForEach-Object { $_.doc })
        foreach ($doc in $ruleDocs) {
            if ($catalogued -notcontains $doc) {
                $problems += "rule doc '$doc' is absent from standards/rules/catalogue.json, so no profile selects it."
            }
        }
        foreach ($doc in $catalogued) {
            if ($ruleDocs -notcontains $doc) {
                $problems += "catalogue.json names rule doc '$doc', which does not exist."
            }
        }
    }
}

if ($problems) {
    Write-Host "The standards tree and the skill namespace disagree:"
    foreach ($problem in $problems) { Write-Host "  $problem" }
    exit 1
}

$pluginRoot = Join-Path $repoRoot 'plugins'
$plugins = @()
if (Test-Path $pluginRoot) { $plugins = @(Get-ChildItem -Path $pluginRoot -Directory) }

# Refuse to generate against a marketplace that points at a plugin that is not there, or a plugin
# with no manifest of its own - an unroutable package installs and delivers nothing.
if (-not (Test-Path $manifest)) { throw "Missing canonical manifest .agents/plugins/marketplace.json." }
$manifestBody = Read-Lf $manifest
$manifestJson = ConvertFrom-Json $manifestBody
$declared = @()
foreach ($entry in $manifestJson.plugins) {
    $declared += $entry.name
    if ($entry.source.source -ne 'local' -or -not $entry.source.path) {
        throw "marketplace.json plugin '$($entry.name)' must use a local source object with a path."
    }
    if (-not $entry.policy.installation -or -not $entry.policy.authentication -or -not $entry.category) {
        throw "marketplace.json plugin '$($entry.name)' must declare installation, authentication, and category."
    }
    $source = Join-Path $repoRoot ($entry.source.path -replace '^\./', '')
    if (-not (Test-Path $source)) {
        throw "marketplace.json declares '$($entry.name)' at $($entry.source.path), which does not exist."
    }
    if (-not (Test-Path (Join-Path $source '.claude-plugin/plugin.json'))) {
        throw "Plugin '$($entry.name)' has no .claude-plugin/plugin.json, so Claude cannot load it."
    }
    if (-not (Test-Path (Join-Path $source '.codex-plugin/plugin.json'))) {
        throw "Plugin '$($entry.name)' has no .codex-plugin/plugin.json, so Codex cannot load it."
    }
}
if (-not (Test-Path $claudeManifest)) { throw "Missing Claude manifest .claude-plugin/marketplace.json." }
$claudeDeclared = @((ConvertFrom-Json (Read-Lf $claudeManifest)).plugins | ForEach-Object { $_.name } | Sort-Object)
$codexDeclared = @($declared | Sort-Object)
if (($claudeDeclared -join "`n") -ne ($codexDeclared -join "`n")) {
    throw "Claude and Codex marketplaces declare different plugins."
}

# Which plugin ships which domains. A consumer installs per stack, so the split is authored rather
# than inferred from a plugin's name - and cross-checked both ways against the marketplace so the two
# cannot drift into disagreeing about what exists.
$payloadsFile = Join-Path $repoRoot '.agents/plugins/payloads.json'
if (-not (Test-Path $payloadsFile)) { throw "Missing .agents/plugins/payloads.json." }
$payloadsJson = ConvertFrom-Json (Read-Lf $payloadsFile)
$payloads = $payloadsJson.payloads
$pluginDomains = @{}
foreach ($property in $payloads.PSObject.Properties) {
    if ($declared -notcontains $property.Name) {
        throw "payloads.json declares plugin '$($property.Name)', which marketplace.json does not."
    }
    $pluginDomains[$property.Name] = @($property.Value)
}
foreach ($name in $declared) {
    if (-not $pluginDomains.ContainsKey($name)) {
        throw "marketplace.json declares plugin '$name', which payloads.json assigns no domains."
    }
}
$knownDomains = @(
    @($docs | ForEach-Object { ($_ -split '/')[1] })
    @($routers.Values | Select-Object -ExpandProperty Domain)
) | Sort-Object -Unique
foreach ($plugin in $plugins) {
    if (-not $pluginDomains.ContainsKey($plugin.Name)) {
        throw "plugins/$($plugin.Name) exists but is declared nowhere; add it to marketplace.json and payloads.json."
    }
    foreach ($domain in $pluginDomains[$plugin.Name]) {
        if ($knownDomains -notcontains $domain) {
            throw "plugin '$($plugin.Name)' claims unknown domain '$domain'."
        }
    }
}
$unshipped = @($docs | ForEach-Object { ($_ -split '/')[1] } | Sort-Object -Unique |
    Where-Object { $domain = $_; -not (@($pluginDomains.Values | ForEach-Object { $_ }) -contains $domain) })
if ($unshipped) {
    throw "standards domain(s) '$($unshipped -join ', ')' are in no plugin, so a clone cannot install them."
}
# A self-contained router names its domain directly (no doc for the check above to walk), so it needs
# its own pass: a domain with zero routed docs would otherwise never surface in $docs at all.
$unshippedSelfContained = @($routers.Values | Where-Object { -not $_.Doc } | Select-Object -ExpandProperty Domain -Unique |
    Where-Object { $domain = $_; -not (@($pluginDomains.Values | ForEach-Object { $_ }) -contains $domain) })
if ($unshippedSelfContained) {
    throw "self-contained skill domain(s) '$($unshippedSelfContained -join ', ')' are in no plugin, so a clone cannot install them."
}

# Exactly ONE plugin ships the hook. Copying it into every plugin registers the same PreToolUse matcher
# once per installed plugin, so a single write fires the router two or three times.
#
# The shipped plugin needs every hook file flattened into one hooks/ folder - that is a packaging
# convention of each harness's own plugin format, not something authoring gets to change. But the
# AUTHORED source splits three ways by what actually varies: .agents/hooks/ holds ONLY the shared .py
# mechanisms both harnesses execute verbatim. .claude/hooks/ holds ONLY Claude's own wiring (hooks.json,
# run-claude-hook.sh); .codex/hooks/ holds ONLY Codex's codex-hooks.json - neither
# manifest duplicates the mechanism, each just names the shared script to run. Both are inert for a repo
# a harness opens directly (project hooks come from that harness's own settings file, not a hooks.json
# lying around), so they are purely the authoring home the generator assembles from, same as .agents/skills
# and .claude/skills. A future harness gets the same treatment: its own top-level dot-folder, nothing
# shared duplicated into it.
$routeFiles = @()
if (Test-Path $routeSource) {
    $routeFiles = @(Get-ChildItem -Path $routeSource -File -Filter '*.json' | Sort-Object Name)
}

$hookOwner = $payloadsJson.hooks
# The tables the router reads are the ROUTE OWNER's payload, not the hook's. They are one plugin's
# data (which repo gets which table) while the hook that reads them is mechanism, so the two ship
# separately once the mechanism is generic and the tables are not. Defaults to the hook owner for a
# repo that owns both; the router resolves a registry from any installed plugin, not only its own.
$routeOwner = $payloadsJson.routes
if (-not $routeOwner) { $routeOwner = $hookOwner }
if ($routeFiles.Count -and -not $routeOwner) {
    throw ".agents/routes holds $($routeFiles.Count) table(s) but payloads.json names no 'routes' or 'hooks' owner, so no plugin ships them."
}
if ($routeOwner -and ($declared -notcontains $routeOwner)) {
    throw "payloads.json assigns the route tables to '$routeOwner', which marketplace.json does not declare."
}
$hookFiles = @()
foreach ($source in @($hookSource, $claudeHookSource, $codexHookSource)) {
    if (Test-Path $source) {
        $hookFiles += @(Get-ChildItem -Path $source -File | Where-Object { $_.Extension -in '.py', '.json', '.cmd', '.sh' })
    }
}
$duplicateHookNames = @($hookFiles | Group-Object Name | Where-Object { $_.Count -gt 1 } | Select-Object -ExpandProperty Name)
if ($duplicateHookNames) {
    throw "hook file(s) named in more than one of .agents/hooks, .claude/hooks, .codex/hooks: $($duplicateHookNames -join ', ')."
}
if ($hookFiles.Count -and -not $hookOwner) {
    throw ".agents/hooks, .claude/hooks, or .codex/hooks holds $($hookFiles.Count) file(s) but payloads.json names no 'hooks' owner, so every plugin would ship a duplicate copy."
}
if ($hookOwner -and ($declared -notcontains $hookOwner)) {
    throw "payloads.json assigns the hooks to '$hookOwner', which marketplace.json does not declare."
}

# Workflow resources are optional. A repo whose corpus is standards only ships none and must still
# generate; a repo that HAS them must name their owner, so a tree no plugin ships cannot go unnoticed.
$workflowOwner = $payloadsJson.workflows
if ($workflowOwner) {
    if ($declared -notcontains $workflowOwner) {
        throw "payloads.json assigns workflow resources to '$workflowOwner', which marketplace.json does not declare."
    }
    if (-not (Test-Path $workflowSource)) {
        throw "payloads.json assigns workflow resources to '$workflowOwner', but there are none under .agents/workflows."
    }
    $workflowPlugin = @($plugins | Where-Object { $_.Name -eq $workflowOwner })[0]
    $claudeWorkflowManifest = ConvertFrom-Json (
        Read-Lf (Join-Path $workflowPlugin.FullName '.claude-plugin/plugin.json')
    )
    $codexWorkflowManifest = ConvertFrom-Json (
        Read-Lf (Join-Path $workflowPlugin.FullName '.codex-plugin/plugin.json')
    )
    if (
        -not $claudeWorkflowManifest.version -or
        $claudeWorkflowManifest.version -ne $codexWorkflowManifest.version
    ) {
        throw "workflow plugin versions differ between Claude and Codex manifests."
    }
} elseif (Test-Path $workflowSource) {
    throw ".agents/workflows exists but payloads.json names no 'workflows' owner, so no plugin ships it."
}

# relative path -> LF-normalized content
$generated = [ordered]@{}

if ($workflowOwner) {

$fixtureSource = Join-Path $workflowSource 'fixtures'
$workflowFiles = @(Get-ChildItem -Path $workflowSource -Recurse -File |
    Where-Object { $_.Extension -ne '.pyc' })
foreach ($file in $workflowFiles) {
    $relative = To-RepoRelative $file.FullName $workflowSource
    $generated["plugins/$workflowOwner/workflows/$relative"] = Read-Lf $file.FullName
}

$fixtureTemplate = Read-Lf (Join-Path $fixtureSource 'workflow-contract-fixture.template.md')
$gateContract = (Read-Lf (Join-Path $workflowSource 'contract/v2/gates.md')).Trim()
$renderedFixture = $fixtureTemplate.Replace('{{WORKFLOW_CONTRACT_V2_GATES}}', $gateContract)
if ($renderedFixture.Contains('{{')) {
    throw "The workflow contract fixture contains an unresolved generation token."
}
$generated["plugins/$workflowOwner/workflows/fixtures/workflow-contract-fixture.md"] = $renderedFixture

$roleFixture = ConvertFrom-Json (Read-Lf (Join-Path $fixtureSource 'role.json'))
$roleBody = (Read-Lf (Join-Path $fixtureSource $roleFixture.body)).Trim()
$codexLines = @(
    "name = `"$(Escape-TomlString $roleFixture.name)`"",
    "description = `"$(Escape-TomlString $roleFixture.description)`"",
    "model = `"$(Escape-TomlString $roleFixture.codex.model)`"",
    "model_reasoning_effort = `"$(Escape-TomlString $roleFixture.codex.reasoning_effort)`"",
    "sandbox_mode = `"$(Escape-TomlString $roleFixture.codex.sandbox_mode)`"",
    '',
    'developer_instructions = """',
    $roleBody,
    '"""',
    ''
)
$generated["plugins/$workflowOwner/workflows/fixtures/workflow-contract-fixture.toml"] = ($codexLines -join "`n")
$claudeLines = @(
    '---',
    "name: $($roleFixture.name)",
    "description: $($roleFixture.description)",
    "model: $($roleFixture.claude.model)",
    "tools: $(@($roleFixture.claude.tools) -join ', ')",
    '---',
    '',
    $roleBody,
    ''
)
$generated["plugins/$workflowOwner/workflows/fixtures/workflow-contract-fixture.claude.md"] = ($claudeLines -join "`n")

$codexHost = ConvertFrom-Json (Read-Lf (Join-Path $workflowSource 'hosts/codex.json'))
$claudeHost = ConvertFrom-Json (Read-Lf (Join-Path $workflowSource 'hosts/claude.json'))
$codexRoles = @($codexHost.roles.PSObject.Properties.Name | Sort-Object)
$claudeRoles = @($claudeHost.roles.PSObject.Properties.Name | Sort-Object)
if (($codexRoles -join "`n") -ne ($claudeRoles -join "`n")) {
    throw "Codex and Claude host manifests declare different semantic roles."
}
foreach ($capability in $codexRoles) {
    $codexRole = $codexHost.roles.$capability
    $claudeRole = $claudeHost.roles.$capability
    if ($codexRole.body -ne $claudeRole.body) {
        throw "Codex and Claude role '$capability' do not share one canonical body."
    }
    $body = (Read-Lf (Join-Path (Join-Path $workflowSource 'hosts') $codexRole.body)).Trim()
    $codexAgent = @(
        "name = `"$(Escape-TomlString $codexRole.agent_name)`"",
        "description = `"$(Escape-TomlString $codexRole.description)`"",
        "sandbox_mode = `"$(Escape-TomlString $codexRole.sandbox_mode)`"",
        '',
        'developer_instructions = """',
        $body,
        '"""',
        '',
        '[agents]',
        'enabled = false',
        ''
    ) -join "`n"
    $generated[".codex/agents/$($codexRole.filename)"] = $codexAgent
    $generated["plugins/$workflowOwner/codex-agents/$($codexRole.filename)"] = $codexAgent

    $claudeAgent = [System.Collections.Generic.List[string]]::new()
    $claudeAgent.Add('---')
    $claudeAgent.Add("name: $($claudeRole.agent_name)")
    $claudeAgent.Add("description: $($claudeRole.description)")
    $claudeAgent.Add("tools: $(@($claudeRole.tools) -join ', ')")
    $claudeAgent.Add("disallowedTools: $(@($claudeRole.disallowed_tools) -join ', ')")
    if ($claudeRole.isolation) { $claudeAgent.Add("isolation: $($claudeRole.isolation)") }
    $claudeAgent.Add('---')
    $claudeAgent.Add('')
    $claudeAgent.Add($body)
    $claudeAgent.Add('')
    $renderedClaudeAgent = $claudeAgent -join "`n"
    $generated[".claude/agents/$($claudeRole.filename)"] = $renderedClaudeAgent
    $generated["plugins/$workflowOwner/agents/$($claudeRole.filename)"] = $renderedClaudeAgent
}

$codexInstaller = Read-Lf (Join-Path $workflowSource 'hosts/install-codex-agents.ps1')
$generated[$codexHost.delivery.project_installer] = $codexInstaller
$generated["plugins/$workflowOwner/$($codexHost.delivery.plugin_installer)"] = $codexInstaller

}

foreach ($router in $routers.Values) {
    $generated[".claude/skills/$($router.Name)/SKILL.md"] = if ($router.Doc) {
        Expand-RoutedSkill $router.Body (Read-Lf (Join-Path $repoRoot $router.Doc)) $router.Doc '../../../' $router.Name
    } else {
        $router.Body
    }
    Add-SkillSiblings '.claude/skills' $router
}
foreach ($name in $claudeHostSkills.Keys) {
    $generated[".claude/skills/$name/SKILL.md"] = $claudeHostSkills[$name]
}

foreach ($plugin in $plugins) {
    # A plugin ships only the domains it claims, and only the routers for those domains - a TypeScript
    # project installing a React plugin must not also receive the .NET corpus.
    $mine = @($docs | Where-Object {
        $pluginDomains[$plugin.Name] -contains (($_ -split '/')[1])
    })
    foreach ($doc in $mine) {
        $generated["plugins/$($plugin.Name)/$doc"] = Read-Lf (Join-Path $repoRoot $doc)
        $owner = @($routers.Values | Where-Object { $_.Doc -eq $doc })[0]
        $generated["plugins/$($plugin.Name)/skills/$($owner.Name)/SKILL.md"] =
            (Expand-RoutedSkill $owner.Body (Read-Lf (Join-Path $repoRoot $doc)) $doc '../../' $owner.Name)
        Add-SkillSiblings "plugins/$($plugin.Name)/skills" $owner
    }

    # The rules domain has no router to expand: the SessionStart resolver reads its catalogue and picks
    # per the consuming repository's profile, so the tree ships verbatim, catalogue included.
    if ($pluginDomains[$plugin.Name] -contains 'rules') {
        foreach ($file in Get-ChildItem -Path (Join-Path $standardsDir 'rules') -Recurse -File) {
            $relative = To-RepoRelative $file.FullName $repoRoot
            $generated["plugins/$($plugin.Name)/$relative"] = Read-Lf $file.FullName
        }
    }
    # A self-contained router has no doc to copy or rewrite - its body already IS what ships, verbatim,
    # same as the .claude/skills copy above.
    $mineSelfContained = @($routers.Values | Where-Object { -not $_.Doc -and $pluginDomains[$plugin.Name] -contains $_.Domain })
    foreach ($router in $mineSelfContained) {
        $generated["plugins/$($plugin.Name)/skills/$($router.Name)/SKILL.md"] = $router.Body
        Add-SkillSiblings "plugins/$($plugin.Name)/skills" $router
    }
    if ($plugin.Name -eq $hookOwner) {
        foreach ($hook in $hookFiles) {
            $generated["plugins/$($plugin.Name)/hooks/$($hook.Name)"] = Read-Lf $hook.FullName
        }
    }
    if ($plugin.Name -eq $routeOwner) {
        foreach ($route in $routeFiles) {
            $generated["plugins/$($plugin.Name)/routes/$($route.Name)"] = Read-Lf $route.FullName
        }
    }
}

if ($workflowOwner) {
    foreach ($router in $routers.Values) {
        if ($pluginDomains[$workflowOwner] -notcontains $router.Domain) { continue }
        $generated["plugins/$workflowOwner/codex-skills/$($router.Name)/SKILL.md"] = if ($router.Doc) {
            Expand-RoutedSkill $router.Body (Read-Lf (Join-Path $repoRoot $router.Doc)) $router.Doc '../../' $router.Name
        } else {
            $router.Body
        }
        Add-SkillSiblings "plugins/$workflowOwner/codex-skills" $router
    }
    foreach ($name in $claudeHostSkills.Keys) {
        $generated["plugins/$workflowOwner/skills/$name/SKILL.md"] = $claudeHostSkills[$name]
    }
    foreach ($name in $codexHostSkills.Keys) {
        $generated["plugins/$workflowOwner/codex-skills/$name/SKILL.md"] = $codexHostSkills[$name]
    }
}
# One index per domain, generated from the tree so it cannot drift from it.
$domains = @($docs | ForEach-Object { ($_ -split '/')[1] } | Sort-Object -Unique)
foreach ($domain in $domains) {
    $rows = @()
    # Domain-root docs first, then each subfolder as a block. A plain path sort interleaves them.
    # Sorted ORDINALLY, not with Sort-Object: its comparison is culture-aware, and cultures disagree
    # about punctuation. `COMMIT.md` vs `COMMIT_ALL.md` ('.' against '_') ordered one way on Windows and
    # the other under Linux ICU, so the generated INDEX differed by platform and CI called a locally
    # current tree stale. A generated file that depends on the generating machine's culture is not
    # generated. Folder and path are packed into one key with a tab, which no path contains.
    $keyed = [System.Collections.Generic.List[string]]::new()
    foreach ($doc in @($docs | Where-Object { $_ -like "standards/$domain/*" })) {
        $withinDomain = $doc -replace "^standards/$domain/", ''
        $folder = if ($withinDomain -match '/') { $withinDomain.Substring(0, $withinDomain.LastIndexOf('/')) } else { '' }
        $keyed.Add("$folder`t$doc")
    }
    $keyed.Sort([System.StringComparer]::Ordinal)
    $inDomain = @($keyed | ForEach-Object { ($_ -split "`t", 2)[1] })
    foreach ($doc in $inDomain) {
        $owner = @($routers.Values | Where-Object { $_.Doc -eq $doc })[0]
        $heading = @((Read-Lf (Join-Path $repoRoot $doc)) -split "`n" |
            Where-Object { $_ -match '^#\s+' } | Select-Object -First 1)
        $title = ($heading[0] -replace '^#\s+', '')
        $relative = ($doc -replace "^standards/$domain/", '')
        $rows += "| [``$relative``]($relative) | $title | ``$($owner.Name)`` |"
    }
    $lines = @(
        "# $domain standards",
        '',
        'Generated by `.agents/sync-generated.ps1` from the tree. Do not edit.',
        '',
        '| Doc | Covers | Skill |',
        '|---|---|---|'
    ) + $rows + @('')
    $generated["standards/$domain/$INDEX_NAME"] = ($lines -join "`n")
}

$stale = @(); $written = @(); $unchanged = @()

foreach ($relative in $generated.Keys) {
    $target  = Join-Path $repoRoot $relative
    $body    = $generated[$relative]
    $current = $null
    if (Test-Path $target) { $current = Read-Lf $target }
    if ($current -eq $body) { $unchanged += $relative; continue }
    $stale += $relative
    if ($Check) { continue }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    [System.IO.File]::WriteAllText($target, ($body -replace "`n", "`r`n"), $utf8NoBom)
    $written += $relative
}

# Prune every generated artefact this run did not just author. Membership of $generated is the test, not
# "is there still a skill by this name" - a doc moving between plugins leaves a stale copy behind that a
# name check would happily keep, and a consumer would then install two conflicting copies of one rule.
$pruned = @()
$generatedRoots = @(
    (Join-Path $repoRoot '.claude/skills')
)
$agentGeneratedRoots = @(
    [pscustomobject]@{
        Root = (Join-Path $repoRoot '.claude/agents')
        Pattern = 'workflow-*.md'
    },
    [pscustomobject]@{
        Root = (Join-Path $repoRoot '.codex/agents')
        Pattern = 'workflow-*.toml'
    }
)
foreach ($plugin in $plugins) {
    $generatedRoots += (Join-Path $plugin.FullName 'skills')
    $generatedRoots += (Join-Path $plugin.FullName 'standards')
    $generatedRoots += (Join-Path $plugin.FullName 'hooks')
    if ($plugin.Name -eq $routeOwner) {
        $generatedRoots += (Join-Path $plugin.FullName 'routes')
    }
    if ($plugin.Name -eq $workflowOwner) {
        $generatedRoots += (Join-Path $plugin.FullName 'codex-skills')
        $generatedRoots += (Join-Path $plugin.FullName 'workflows')
        $agentGeneratedRoots += [pscustomobject]@{
            Root = (Join-Path $plugin.FullName 'agents')
            Pattern = 'workflow-*.md'
        }
        $agentGeneratedRoots += [pscustomobject]@{
            Root = (Join-Path $plugin.FullName 'codex-agents')
            Pattern = 'workflow-*.toml'
        }
    }
}
foreach ($root in $generatedRoots) {
    if (-not (Test-Path $root)) { continue }
    foreach ($file in Get-ChildItem -Path $root -Recurse -File) {
        $relative = To-RepoRelative $file.FullName $repoRoot
        if ($generated.Contains($relative)) { continue }
        $pruned += $relative
        if (-not $Check) { Remove-Item -Force $file.FullName }
    }
}
foreach ($scope in $agentGeneratedRoots) {
    if (-not (Test-Path $scope.Root)) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $scope.Root -File -Filter $scope.Pattern) {
        $relative = To-RepoRelative $file.FullName $repoRoot
        if ($generated.Contains($relative)) { continue }
        $pruned += $relative
        if (-not $Check) { Remove-Item -Force $file.FullName }
    }
}
if (-not $Check) {
    $cleanupRoots = @($generatedRoots) + @($agentGeneratedRoots | ForEach-Object { $_.Root })
    foreach ($root in $cleanupRoots) {
        if (-not (Test-Path $root)) { continue }
        Get-ChildItem -Path $root -Recurse -Directory |
            Sort-Object { $_.FullName.Length } -Descending |
            Where-Object { -not (Get-ChildItem -Path $_.FullName -Recurse -File) } |
            ForEach-Object { Remove-Item -Recurse -Force $_.FullName }
    }
}

if ($Check) {
    if ($stale.Count -or $pruned.Count) {
        Write-Host "STALE: $($stale.Count) generated file(s), $($pruned.Count) orphan(s). Run: pwsh .agents/sync-generated.ps1"
        foreach ($item in ($stale + $pruned)) { Write-Host "  $item" }
        exit 1
    }
    Write-Host "generated files are current: $($unchanged.Count) checked ($($routers.Count) skills, $($docs.Count) docs)"
    exit 0
}

Write-Host "generated: $($generated.Count) file(s) from $($routers.Count) skills and $($docs.Count) docs | $($written.Count) written | $($unchanged.Count) unchanged | $($pruned.Count) pruned"
foreach ($item in $written) { Write-Host "  written: $item" }
foreach ($item in $pruned)  { Write-Host "  pruned:  $item" }
