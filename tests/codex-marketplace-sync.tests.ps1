$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
. (Join-Path $repository '.agents/machine/scripts/codex_marketplace_sync.ps1')

$script:calls = [System.Collections.Generic.List[string]]::new()
$script:failUpgrade = $false

function Invoke-CodexHookTrust {
    param([string] $CodexExecutable, [string] $WorkingDirectory, [string] $HelperScript)
    if ($CodexExecutable -ne 'Invoke-FakeCodex' -or $WorkingDirectory -ne $repository) {
        throw 'Hook trust received the wrong executable or project'
    }
    if (-not (Test-Path -LiteralPath $HelperScript)) { throw 'Hook trust was not preserved before refresh' }
    $script:calls.Add('trust tj-agents hooks')
}

function Invoke-FakeCodex {
    $commandLine = $args -join ' '
    $script:calls.Add($commandLine)
    $global:LASTEXITCODE = 0
    if ($commandLine -eq 'plugin marketplace upgrade --json') {
        if ($script:failUpgrade) {
            $global:LASTEXITCODE = 1
            'upgrade failed'
        } else {
            '{"selectedMarketplaces":["base-agents"],"upgradedRoots":["cache"],"errors":[]}'
        }
        return
    }
    if ($commandLine -eq 'plugin list --available --json') {
        '{"installed":[{"pluginId":"base@base-agents","enabled":true,"marketplaceSource":{"sourceType":"git"}},{"pluginId":"local@local","enabled":true,"marketplaceSource":{"sourceType":"local"}}],"available":[{"pluginId":"engineering@base-agents","enabled":true,"marketplaceSource":{"sourceType":"git"}},{"pluginId":"unused@base-agents","enabled":false,"marketplaceSource":{"sourceType":"git"}}]}'
        return
    }
    if ($commandLine -match '^plugin add (.+) --json$') {
        '{"pluginId":"' + $Matches[1] + '"}'
        return
    }
    throw "Unexpected fake Codex command: $commandLine"
}

$before = (Get-Location).Path
$selected = @(Sync-CodexStandards -CodexExecutable 'Invoke-FakeCodex' -WorkingDirectory $repository)
if (($selected -join ',') -ne 'base@base-agents,engineering@base-agents') {
    throw "Wrong plugin selection: $($selected -join ',')"
}
$expected = @(
    'plugin marketplace upgrade --json',
    'plugin list --available --json',
    'plugin add base@base-agents --json',
    'plugin add engineering@base-agents --json',
    'trust tj-agents hooks'
)
if (($script:calls -join '|') -ne ($expected -join '|')) {
    throw "Wrong refresh sequence: $($script:calls -join '|')"
}
if ((Get-Location).Path -ne $before) { throw 'Startup sync changed the caller directory' }

$script:calls.Clear()
$script:failUpgrade = $true
$blocked = $false
try {
    Sync-CodexStandards -CodexExecutable 'Invoke-FakeCodex' -WorkingDirectory $repository | Out-Null
}
catch {
    $blocked = $_.Exception.Message -like '*upgrade failed*'
}
if (-not $blocked) { throw 'Failed marketplace refresh did not block startup' }
if ($script:calls.Count -ne 1) { throw 'Refresh failure continued to plugin installation' }
if ((Get-Location).Path -ne $before) { throw 'Failed sync changed the caller directory' }

$global:LASTEXITCODE = 0
Write-Output 'Codex marketplace startup sync tests passed.'
