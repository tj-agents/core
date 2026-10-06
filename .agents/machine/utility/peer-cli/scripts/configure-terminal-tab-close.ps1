<#
.SYNOPSIS
Make Windows Terminal close a tab when its process exits.

.DESCRIPTION
Terminal's default is `closeOnExit: automatic`, which keeps the tab when a process exits non-zero — and a
process that was killed always does. So every agent session ended by tooling leaves a dead pane behind,
and they accumulate until the window is unusable.

Setting `always` on the profile defaults makes a finished or killed session take its tab with it, which is
what `peer-cli close` should mean. `graceful` is the softer option: it closes only on exit code 0, so a
killed session still leaves its tab.

Writes a timestamped backup beside the settings file before changing anything.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('always', 'graceful', 'automatic', 'never')]
    [string] $CloseOnExit = 'always',

    [string] $SettingsPath = (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'),

    [switch] $Preview
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $SettingsPath)) {
    throw "Windows Terminal settings not found at $SettingsPath."
}
$SettingsPath = (Resolve-Path -LiteralPath $SettingsPath).ProviderPath

$text = Get-Content -LiteralPath $SettingsPath -Raw -Encoding UTF8

if ($text -match '"closeOnExit"\s*:\s*"(?<value>[^"]+)"') {
    $current = $Matches.value
    if ($current -eq $CloseOnExit) {
        Write-Output "closeOnExit is already '$CloseOnExit'."
        return
    }
    $updated = $text -replace '("closeOnExit"\s*:\s*")[^"]+(")', "`${1}$CloseOnExit`${2}"
}
else {
    # The defaults block is the one every profile inherits; a per-profile value would miss agent tabs
    # launched under any other profile.
    if ($text -notmatch '(?<head>"defaults"\s*:\s*\r?\n?\s*\{)') {
        throw 'No profiles.defaults block found; set closeOnExit by hand.'
    }
    $updated = [regex]::Replace(
        $text,
        '("defaults"\s*:\s*\r?\n?\s*\{)',
        "`$1`r`n            `"closeOnExit`": `"$CloseOnExit`",",
        1)
}

if ($Preview) {
    Write-Output "Would set closeOnExit to '$CloseOnExit' in $SettingsPath."
    return
}

if (-not $PSCmdlet.ShouldProcess($SettingsPath, "Set closeOnExit to '$CloseOnExit'")) { return }

$backup = "$SettingsPath.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
Copy-Item -LiteralPath $SettingsPath -Destination $backup
[IO.File]::WriteAllText($SettingsPath, $updated, [Text.UTF8Encoding]::new($false))

Write-Output "closeOnExit set to '$CloseOnExit'. Backup: $backup"
Write-Output 'Windows Terminal picks this up immediately; no restart needed.'
