$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
. (Join-Path $repository '.agents/machine/scripts/codex_marketplace_sync.ps1')
$temp = Join-Path ([IO.Path]::GetTempPath()) ('codex-sync-timeout-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
$fake = Join-Path $temp 'fake codex.ps1'
Set-Content -LiteralPath $fake -Value 'Start-Sleep -Seconds 30'
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $failed = $false
    try { Sync-CodexStandards -CodexExecutable $fake -WorkingDirectory $temp -TimeoutSeconds 1 | Out-Null }
    catch { $failed = $_.Exception.Message -match 'timed out' }
    if (-not $failed) { throw 'Hung Codex sync did not report its timeout' }
    if ($clock.Elapsed.TotalSeconds -gt 9) { throw 'Codex timeout did not release the caller promptly' }

    $fastCodex = Join-Path $temp 'fast codex.ps1'
    Set-Content -LiteralPath $fastCodex -Value @'
param()
$joined = $args -join ' '
if ($joined -like '*marketplace upgrade*') {
    '{"errors":[]}'
}
elseif ($joined -like '*list --available*') {
    '{"installed":[{"pluginId":"test-plugin","enabled":true,"marketplaceSource":{"sourceType":"git"}}],"available":[]}'
}
elseif ($joined -like '*plugin add*') {
    '{"pluginId":"test-plugin"}'
}
else {
    exit 1
}
'@

    $hungTrust = Join-Path $temp 'hung_hook_trust.py'
    Set-Content -LiteralPath $hungTrust -Value @'
import time
time.sleep(15)
'@

    $trustClock = [Diagnostics.Stopwatch]::StartNew()
    $trustFailed = $false
    try {
        Sync-CodexStandards -CodexExecutable $fastCodex -WorkingDirectory $temp -TimeoutSeconds 12 -HookTrustHelperScript $hungTrust | Out-Null
    }
    catch { $trustFailed = $_.Exception.Message -match 'trust' -or $_.Exception.Message -match 'timed out' }
    if (-not $trustFailed) { throw 'Hung Codex hook trust did not report its timeout' }
    if ($trustClock.Elapsed.TotalSeconds -gt 16) { throw 'Codex hook trust timeout did not release the caller promptly' }

    $sourcePath = Join-Path $repository '.agents/machine/scripts/codex_marketplace_sync.ps1'
    $source = Get-Content -LiteralPath $sourcePath -Raw
    if ($source -notmatch [regex]::Escape('if ($trustSnapshot) { Remove-Item -LiteralPath $trustSnapshot -Force -ErrorAction SilentlyContinue }')) {
        throw 'Hook trust snapshot cleanup does not silently continue on failure'
    }

    'Codex sync timeout tests passed.'
}
finally {
    $root = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $target = [IO.Path]::GetFullPath($temp)
    if (-not $target.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'Test cleanup outside temp' }
    Remove-Item -LiteralPath $target -Recurse -Force
}
