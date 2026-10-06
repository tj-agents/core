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

    $stderrCodex = Join-Path $temp 'stderr codex.ps1'
    Set-Content -LiteralPath $stderrCodex -Value @'
param()
[Console]::Error.WriteLine('codex: a routine progress line')
'{"errors":[]}'
'@
    $stderrCaught = $null
    $stderrResult = $null
    try {
        $stderrResult = Invoke-CodexSyncCommand -CodexExecutable $stderrCodex -Arguments @('plugin', 'marketplace', 'upgrade', '--json') -TimeoutSeconds 10
    }
    catch { $stderrCaught = $_ }
    if ($stderrCaught) { throw "A successful command with stderr output should not fail: $($stderrCaught.Exception.Message)" }
    if ($null -eq $stderrResult -or @($stderrResult.errors).Count -ne 0) { throw 'Stderr noise corrupted the parsed JSON result' }

    $failTrust = Join-Path $temp 'fail_hook_trust.py'
    Set-Content -LiteralPath $failTrust -Value @'
import sys
print('trust helper starting')
print('bad trust reason', file=sys.stderr)
sys.exit(1)
'@
    $trustRunner = Join-Path $temp 'trust-runner.py'
    Copy-Item -LiteralPath (Join-Path $repository '.agents/machine/scripts/bounded_process.py') -Destination $trustRunner -Force
    $trustError = $null
    try {
        Invoke-CodexHookTrust -CodexExecutable $stderrCodex -WorkingDirectory $temp -HelperScript $failTrust -RunnerPath $trustRunner -TimeoutSeconds 10
    }
    catch { $trustError = $_ }
    if (-not $trustError) { throw 'A failing hook trust helper did not report a failure' }
    if ($trustError.Exception.Message -notmatch 'could not trust tj-agents hooks.*bad trust reason') {
        throw "Hook trust failure message lost its stderr reason: $($trustError.Exception.Message)"
    }

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
time.sleep(70)
'@

    $trustClock = [Diagnostics.Stopwatch]::StartNew()
    $trustFailed = $false
    try {
        Sync-CodexStandards -CodexExecutable $fastCodex -WorkingDirectory $temp -TimeoutSeconds 40 -HookTrustHelperScript $hungTrust | Out-Null
    }
    catch { $trustFailed = $_.Exception.Message -match 'could not trust tj-agents hooks.*timed out after' }
    if (-not $trustFailed) { throw 'Hung Codex hook trust did not report its trust-specific timeout' }
    if ($trustClock.Elapsed.TotalSeconds -gt 55) { throw 'Codex hook trust timeout did not release the caller promptly' }

    $script:cleanupCalls = 0
    function Remove-Item {
        [CmdletBinding()]
        param(
            [Parameter(Position = 0)] [string] $Path,
            [string] $LiteralPath,
            [switch] $Force,
            [switch] $Recurse
        )
        $script:cleanupCalls++
        if ($script:cleanupCalls -eq 2) {
            $exception = [IO.IOException]::new('The process cannot access the file because it is being used by another process.')
            $record = [Management.Automation.ErrorRecord]::new($exception, 'FileLocked', [Management.Automation.ErrorCategory]::WriteError, $LiteralPath)
            $PSCmdlet.WriteError($record)
        }
    }
    $failUpgradeCodex = Join-Path $temp 'fail codex.ps1'
    Set-Content -LiteralPath $failUpgradeCodex -Value 'exit 7'
    $maskCaught = $null
    try {
        Sync-CodexStandards -CodexExecutable $failUpgradeCodex -WorkingDirectory $temp -TimeoutSeconds 10 | Out-Null
    }
    catch { $maskCaught = $_ }
    Microsoft.PowerShell.Management\Remove-Item -Path Function:\Remove-Item
    if (-not $maskCaught) { throw 'A failing marketplace upgrade with a locked cleanup file did not report a failure' }
    if ($maskCaught.Exception.Message -notmatch 'Codex plugin sync failed') {
        throw "A locked trust-snapshot cleanup masked the real sync failure: $($maskCaught.Exception.Message)"
    }

    'Codex sync timeout tests passed.'
}
finally {
    if (Test-Path -LiteralPath Function:\Remove-Item) {
        Microsoft.PowerShell.Management\Remove-Item -Path Function:\Remove-Item -ErrorAction SilentlyContinue
    }
    $root = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $target = [IO.Path]::GetFullPath($temp)
    if (-not $target.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'Test cleanup outside temp' }
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $target -Recurse -Force
}
