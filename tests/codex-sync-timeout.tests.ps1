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
    'Codex sync timeout tests passed.'
}
finally {
    $root = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $target = [IO.Path]::GetFullPath($temp)
    if (-not $target.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'Test cleanup outside temp' }
    Remove-Item -LiteralPath $target -Recurse -Force
}
