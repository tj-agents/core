$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$temp = Join-Path ([IO.Path]::GetTempPath()) ('codex-profile-' + [guid]::NewGuid().ToString('N'))
$documents = Join-Path $temp 'Documents'
$bin = Join-Path $temp 'bin'
$codexHome = Join-Path $temp 'codex-home'
$scripts = Join-Path $codexHome 'plugins/cache/base-agents/machine/9.9.9/resources/machine/scripts'
New-Item -ItemType Directory -Path $bin, $scripts -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repository '.agents/machine/scripts/codex-profile.ps1') -Destination $scripts
Copy-Item -LiteralPath (Join-Path $repository '.agents/machine/scripts/codex_marketplace_sync.ps1') -Destination $scripts
$fake = @'
Add-Content -LiteralPath $env:CODEX_TEST_CALLS -Value ($args -join ' ')
$global:LASTEXITCODE = 0
switch ($args -join ' ') {
    'plugin list --json' { '{"installed":[{"pluginId":"machine@base-agents","version":"9.9.9","enabled":true}],"available":[]}' }
    'plugin marketplace upgrade --json' {
        if ($env:CODEX_TEST_FAIL_UPGRADE) { $global:LASTEXITCODE = 1; 'offline'; break }
        '{"selectedMarketplaces":["base-agents"],"upgradedRoots":[],"errors":[]}'
    }
    'plugin list --available --json' { '{"installed":[{"pluginId":"machine@base-agents","enabled":true,"marketplaceSource":{"sourceType":"git"}}],"available":[]}' }
    'plugin add machine@base-agents --json' { '{"pluginId":"machine@base-agents"}' }
    'exec' { 'LAUNCHED exec' }
    default { throw "Unexpected Codex call: $($args -join ' ')" }
}
'@
Set-Content -LiteralPath (Join-Path $bin 'codex.ps1') -Value $fake
$oldPath = $env:PATH
$oldHome = $env:CODEX_HOME
$oldCalls = $env:CODEX_TEST_CALLS
$oldFail = $env:CODEX_TEST_FAIL_UPGRADE
try {
    $env:PATH = "$bin$([IO.Path]::PathSeparator)$oldPath"
    $env:CODEX_HOME = $codexHome
    $env:CODEX_TEST_CALLS = Join-Path $temp 'calls.txt'
    & python -B (Join-Path $repository '.agents/machine/scripts/codex_terminal_profile.py') --documents $documents | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Profile installer failed' }
    $profile = Join-Path $documents 'PowerShell/Microsoft.PowerShell_profile.ps1'
    . $profile
    if ((Get-Command codex).CommandType -ne 'Function') { throw 'Typed Codex was not wrapped' }
    $result = codex exec
    if ($result -ne 'LAUNCHED exec') { throw "Wrong Codex launch: $result" }
    $calls = @(Get-Content -LiteralPath $env:CODEX_TEST_CALLS)
    $expected = @('plugin list --json', 'plugin marketplace upgrade --json',
        'plugin list --available --json', 'plugin add machine@base-agents --json', 'exec')
    if (($calls -join '|') -ne ($expected -join '|')) { throw "Wrong call order: $($calls -join '|')" }
    Clear-Content -LiteralPath $env:CODEX_TEST_CALLS
    $env:CODEX_TEST_FAIL_UPGRADE = '1'
    $result = codex exec 3>&1 | Out-String
    if ($result -notmatch 'refresh failed' -or $result -notmatch 'LAUNCHED exec') {
        throw "A failed refresh did not warn and launch Codex: $result"
    }
    $calls = @(Get-Content -LiteralPath $env:CODEX_TEST_CALLS)
    if (($calls -join '|') -ne 'plugin marketplace upgrade --json|exec') {
        throw "Failed refresh made unexpected calls: $($calls -join '|')"
    }
    'Codex terminal profile tests passed.'
}
finally {
    $env:PATH = $oldPath
    $env:CODEX_HOME = $oldHome
    $env:CODEX_TEST_CALLS = $oldCalls
    $env:CODEX_TEST_FAIL_UPGRADE = $oldFail
    $root = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $target = [IO.Path]::GetFullPath($temp)
    if (-not $target.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'Test cleanup outside temp' }
    Remove-Item -LiteralPath $target -Recurse -Force
}
