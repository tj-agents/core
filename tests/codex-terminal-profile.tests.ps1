$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$temp = Join-Path ([IO.Path]::GetTempPath()) ('codex-profile-' + [guid]::NewGuid().ToString('N'))
$documents = Join-Path $temp 'Documents'
$bin = Join-Path $temp 'bin'
$codexHome = Join-Path $temp 'codex-home'
$scripts = Join-Path $codexHome 'plugins/cache/base-agents/machine/9.9.9/resources/machine/scripts'
New-Item -ItemType Directory -Path $bin, $scripts -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repository '.agents/machine/scripts/codex-profile.ps1') -Destination $scripts
Copy-Item -LiteralPath (Join-Path $repository '.agents/machine/scripts/codex_marketplace_sync.py') -Destination $scripts
# codex_marketplace_sync.py imports codex_hook_trust.command and claude_standards_sync.apply_harness_permissions
# from beside itself, and -- since codex-profile.ps1 now omits --codex -- resolves the native codex itself
# through agent_cli.resolve_codex_executable(), so all three real shared scripts travel with it here, not
# just the hook-trust stub this file replaces with its own fake.
Copy-Item -LiteralPath (Join-Path $repository '.agents/machine/scripts/agent_cli.py') -Destination $scripts
Copy-Item -LiteralPath (Join-Path $repository '.agents/machine/scripts/claude_standards_sync.py') -Destination $scripts
$trustStub = @'
import os
from pathlib import Path


def command(executable):
    # codex_marketplace_sync.py imports this name for real; the fake below never calls it with a `.ps1`
    # shim, so the real one's PowerShell-wrapping branch is not exercised here.
    return [str(executable)]


# Module-level code here must stay side-effect-free, exactly like the real codex_hook_trust.py: this file
# is also *imported* for `command` above, not only ever run as its own process the way the snapshot copy
# below is, and an import must never itself count as a trust run.
if __name__ == "__main__":
    with Path(os.environ["CODEX_TEST_CALLS"]).open("a", encoding="utf-8") as calls:
        calls.write("trust tj-agents hooks\n")
'@
Set-Content -LiteralPath (Join-Path $scripts 'codex_hook_trust.py') -Value $trustStub
$fake = @'
Add-Content -LiteralPath $env:CODEX_TEST_CALLS -Value ($args -join ' ')
$global:LASTEXITCODE = 0
switch ($args -join ' ') {
    'plugin list --json' { '{"installed":[{"pluginId":"machine@base-agents","version":"9.9.9","enabled":true}],"available":[]}' }
    'exec' { 'LAUNCHED exec' }
    default { throw "Unexpected Codex call: $($args -join ' ')" }
}
# codex_marketplace_sync.py runs this fake as its own nested `pwsh -File` child process (it is now a
# separate Python process rather than codex-profile.ps1's own PowerShell session), so the real process
# exit code -- what that child process actually returns, not merely this script's own $LASTEXITCODE
# convention variable -- must be set explicitly for the failed-upgrade case below to reach Python at all.
exit $global:LASTEXITCODE
'@
Set-Content -LiteralPath (Join-Path $bin 'codex.ps1') -Value $fake

# codex-profile.ps1 omits --codex from the sync call, so codex_marketplace_sync.py resolves its own
# native codex via agent_cli.resolve_codex_executable() -- a *different* discovery path from the
# PowerShell-resolved `codex.ps1` shim above, which still only ever serves the profile block's version
# probe (`plugin list --json`) and the final `exec` launch. The native fake answers everything in between
# (`plugin marketplace upgrade`, `plugin list --available`, `plugin add`) and is built per-platform,
# matching agent_cli.codex_candidate_paths()'s own two independent search paths.
$isWindowsHost = $IsWindows -or $env:OS -eq 'Windows_NT'
$callsPath = Join-Path $temp 'calls.txt'
if ($isWindowsHost) {
    # agent_cli.codex_candidate_paths() searches $env:LOCALAPPDATA\OpenAI\Codex\bin recursively for
    # codex.exe, unconditionally on Windows -- no npm shim needed for this half of the fixture at all.
    $localAppData = Join-Path $temp 'local appdata'
    $desktopBin = Join-Path $localAppData 'OpenAI\Codex\bin\h'
    New-Item -ItemType Directory -Force -Path $desktopBin | Out-Null
    $batchPath = Join-Path $desktopBin 'codex.bat'
    $nativeDispatch = @"
if "%1" == "--version" goto version
echo %* >> "$callsPath"
if "%*" == "plugin marketplace upgrade --json" goto upgrade
if "%*" == "plugin list --available --json" goto list
if "%*" == "plugin add machine@base-agents --json" goto add
echo Unexpected native codex call: %* 1>&2
exit /b 2
:version
echo codex-cli 0.160.0
exit /b 0
:upgrade
if defined CODEX_TEST_FAIL_UPGRADE (echo offline 1>&2 & exit /b 1)
if defined CODEX_TEST_TRUST_SOURCE del "%CODEX_TEST_TRUST_SOURCE%" >nul 2>nul
echo {"selectedMarketplaces":["base-agents"],"upgradedRoots":[],"errors":[]}
exit /b 0
:list
echo {"installed":[{"pluginId":"machine@base-agents","enabled":true,"marketplaceSource":{"sourceType":"git"}}],"available":[]}
exit /b 0
:add
echo {"pluginId":"machine@base-agents"}
exit /b 0
"@
    Set-Content -LiteralPath $batchPath -Value $nativeDispatch
    # codex_candidate_paths only globs for codex.exe; a tiny C# stub re-launches the batch file so
    # subprocess.run([path, '--version']) (no shell) still reaches it, same technique
    # handoff-launchers.tests.ps1 used before it moved to launch_codex.py's own Python-level tests.
    $exePath = Join-Path $desktopBin 'codex.exe'
    # Backslashes are doubled for the C# string literal below, not left for PowerShell to interpolate
    # raw: an unescaped path segment like `...\bin\...` would otherwise land on the real C# escape `\b`
    # (backspace) and corrupt the literal, rather than merely looking like one.
    $batchPathEscaped = $batchPath.Replace('\', '\\')
    $stubSource = @"
using System;
using System.Diagnostics;
class Stub {
    static int Main(string[] args) {
        var start = new ProcessStartInfo("cmd.exe", "/c \"$batchPathEscaped\" " + string.Join(" ", args));
        start.UseShellExecute = false;
        var process = Process.Start(start);
        process.WaitForExit();
        return process.ExitCode;
    }
}
"@
    $sourcePath = Join-Path $temp 'stub.cs'
    [System.IO.File]::WriteAllText($sourcePath, $stubSource)
    $builder = Join-Path $temp 'build-stub.ps1'
    [System.IO.File]::WriteAllText($builder, @'
param([Parameter(Mandatory)][string]$SourcePath, [Parameter(Mandatory)][string]$ExePath)
Add-Type -OutputType ConsoleApplication -OutputAssembly $ExePath -TypeDefinition (Get-Content -LiteralPath $SourcePath -Raw)
'@)
    & powershell -NoProfile -ExecutionPolicy Bypass -File $builder -SourcePath $sourcePath -ExePath $exePath
    if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) { throw "Failed to build native codex stub at $exePath." }
} else {
    # agent_cli.codex_candidate_paths()'s POSIX root: Path(shim).parent/node_modules/@openai/codex, then
    # the same codex-*/vendor/*/bin/codex glob underneath it the npm package itself would have. `shim`
    # only has to exist and be executable on PATH as `codex` -- its own content is never run.
    $nativeBin = Join-Path $temp 'native bin'
    $packageDir = Join-Path $nativeBin 'node_modules/@openai/codex'
    $vendorBin = Join-Path $packageDir 'node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin'
    New-Item -ItemType Directory -Force -Path $vendorBin | Out-Null
    $shimPath = Join-Path $nativeBin 'codex'
    Set-Content -LiteralPath $shimPath -Value "#!/bin/sh`nexit 0`n" -NoNewline
    & chmod +x $shimPath
    $posixDispatch = @"
#!/bin/sh
if [ "`$*" = "--version" ]; then echo "codex-cli 0.160.0"; exit 0; fi
echo "`$*" >> "$callsPath"
case "`$*" in
  "plugin marketplace upgrade --json")
    if [ -n "`$CODEX_TEST_FAIL_UPGRADE" ]; then echo "offline" >&2; exit 1; fi
    if [ -n "`$CODEX_TEST_TRUST_SOURCE" ]; then rm -f "`$CODEX_TEST_TRUST_SOURCE"; fi
    echo '{"selectedMarketplaces":["base-agents"],"upgradedRoots":[],"errors":[]}' ;;
  "plugin list --available --json")
    echo '{"installed":[{"pluginId":"machine@base-agents","enabled":true,"marketplaceSource":{"sourceType":"git"}}],"available":[]}' ;;
  "plugin add machine@base-agents --json")
    echo '{"pluginId":"machine@base-agents"}' ;;
  *)
    echo "Unexpected native codex call: `$*" >&2
    exit 2 ;;
esac
"@
    $binaryPath = Join-Path $vendorBin 'codex'
    Set-Content -LiteralPath $binaryPath -Value $posixDispatch -NoNewline
    & chmod +x $binaryPath
}

$oldPath = $env:PATH
$oldHome = $env:CODEX_HOME
$oldCalls = $env:CODEX_TEST_CALLS
$oldFail = $env:CODEX_TEST_FAIL_UPGRADE
$oldTrustSource = $env:CODEX_TEST_TRUST_SOURCE
$oldLocalAppData = $env:LOCALAPPDATA
try {
    $env:PATH = if ($isWindowsHost) { "$bin$([IO.Path]::PathSeparator)$oldPath" } else { "$bin$([IO.Path]::PathSeparator)$nativeBin$([IO.Path]::PathSeparator)$oldPath" }
    $env:CODEX_HOME = $codexHome
    $env:CODEX_TEST_CALLS = $callsPath
    $env:CODEX_TEST_TRUST_SOURCE = Join-Path $scripts 'codex_hook_trust.py'
    if ($isWindowsHost) { $env:LOCALAPPDATA = $localAppData }
    & python -B (Join-Path $repository '.agents/machine/scripts/codex_terminal_profile.py') --documents $documents | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Profile installer failed' }
    $profile = Join-Path $documents 'PowerShell/Microsoft.PowerShell_profile.ps1'
    . $profile
    if ((Get-Command codex).CommandType -ne 'Function') { throw 'Typed Codex was not wrapped' }
    $result = codex exec
    if ($result -ne 'LAUNCHED exec') { throw "Wrong Codex launch: $result" }
    $calls = @(Get-Content -LiteralPath $env:CODEX_TEST_CALLS)
    $expected = @('plugin list --json', 'plugin marketplace upgrade --json',
        'plugin list --available --json', 'plugin add machine@base-agents --json', 'trust tj-agents hooks', 'exec')
    if (($calls -join '|') -ne ($expected -join '|')) { throw "Wrong call order: $($calls -join '|')" }
    Clear-Content -LiteralPath $env:CODEX_TEST_CALLS
    Set-Content -LiteralPath $env:CODEX_TEST_TRUST_SOURCE -Value $trustStub
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
    $env:CODEX_TEST_TRUST_SOURCE = $oldTrustSource
    if ($null -eq $oldLocalAppData) { Remove-Item Env:\LOCALAPPDATA -ErrorAction SilentlyContinue } else { $env:LOCALAPPDATA = $oldLocalAppData }
    $root = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $target = [IO.Path]::GetFullPath($temp)
    if (-not $target.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { throw 'Test cleanup outside temp' }
    Remove-Item -LiteralPath $target -Recurse -Force
}
