[CmdletBinding()]
param(
    [string]$UserProfilePath = $env:USERPROFILE,
    [switch]$DeferAutoSaveStart
)

$ErrorActionPreference = 'Stop'
$sourceDirectory = $PSScriptRoot
$vault = Join-Path $UserProfilePath '.cli-session-vault'
$backupDirectory = Join-Path $vault ("deployment-backups\{0}" -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$codexHooksSource = Join-Path $sourceDirectory 'config\codex-hooks.json'
$codexHooksTarget = Join-Path $UserProfilePath '.codex\hooks.json'
$claudeSettingsTarget = Join-Path $UserProfilePath '.claude\settings.json'
$targetProfile = [System.IO.Path]::GetFullPath($UserProfilePath).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
$currentProfile = [System.IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
$desktopDirectory = if ([string]::Equals($targetProfile, $currentProfile, [System.StringComparison]::OrdinalIgnoreCase)) { [Environment]::GetFolderPath('Desktop') } else { Join-Path $UserProfilePath 'Desktop' }
$saveShortcutPath = Join-Path $desktopDirectory 'SAVE CLI SESSIONS.lnk'
$restoreShortcutPath = Join-Path $desktopDirectory 'RESTORE CLI SESSIONS.lnk'
$names = @(
    'save-sessions-hidden.vbs',
    'configure-cli-session-autosave.ps1',
    'cli-session-shutdown-listener.ps1',
    'save-sessions.ps1',
    'restore-sessions.ps1',
    'start-saved-cli.ps1',
    'probe-cli-window.ps1',
    'probe-cli-open-files.ps1',
    'cli-session-hook.ps1',
    'cli-session-vault.psm1',
    'reconcile-live-sessions.ps1'
)

$parseErrors = @()
foreach ($name in $names) {
    $source = Join-Path $sourceDirectory $name
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing deployment source: $source" }
    if ([System.IO.Path]::GetExtension($source) -ne '.ps1' -and [System.IO.Path]::GetExtension($source) -ne '.psm1') { continue }
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors) | Out-Null
    $parseErrors += @($errors)
}
if ($parseErrors.Count -gt 0) { throw ($parseErrors.Message -join [Environment]::NewLine) }
Get-Content -LiteralPath $codexHooksSource -Raw | ConvertFrom-Json | Out-Null

function Remove-CliSessionRecoveryHooks($Settings) {
    $hooksProperty = $Settings.PSObject.Properties['hooks']
    if (-not $hooksProperty) { return $Settings }
    foreach ($eventProperty in @($Settings.hooks.PSObject.Properties)) {
        $groups = @()
        foreach ($group in @($eventProperty.Value)) {
            $groupHooksProperty = $group.PSObject.Properties['hooks']
            if (-not $groupHooksProperty) {
                $groups += $group
                continue
            }
            $remainingHooks = @($groupHooksProperty.Value | Where-Object { [string]$_.command -notmatch '(?i)cli-session-hook\.ps1' })
            if ($remainingHooks.Count -eq 0) { continue }
            $group | Add-Member -NotePropertyName hooks -NotePropertyValue $remainingHooks -Force
            $groups += $group
        }
        $Settings.hooks | Add-Member -NotePropertyName $eventProperty.Name -NotePropertyValue $groups -Force
    }
    return $Settings
}

New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
foreach ($name in $names) {
    $target = Join-Path $UserProfilePath $name
    if (Test-Path -LiteralPath $target) { Copy-Item -LiteralPath $target -Destination (Join-Path $backupDirectory $name) }
}
if (Test-Path -LiteralPath $codexHooksTarget) {
    Copy-Item -LiteralPath $codexHooksTarget -Destination (Join-Path $backupDirectory 'codex-hooks.json')
}
if (Test-Path -LiteralPath $claudeSettingsTarget) {
    Copy-Item -LiteralPath $claudeSettingsTarget -Destination (Join-Path $backupDirectory 'claude-settings.json')
}
foreach ($shortcutPath in @($saveShortcutPath, $restoreShortcutPath)) {
    if (Test-Path -LiteralPath $shortcutPath) { Copy-Item -LiteralPath $shortcutPath -Destination (Join-Path $backupDirectory (Split-Path $shortcutPath -Leaf)) }
}

foreach ($name in $names) {
    $source = Join-Path $sourceDirectory $name
    $target = Join-Path $UserProfilePath $name
    $temporary = "$target.$PID.$([guid]::NewGuid().ToString('N')).tmp"
    Copy-Item -LiteralPath $source -Destination $temporary
    Move-Item -LiteralPath $temporary -Destination $target -Force
}

New-Item -ItemType Directory -Path (Split-Path -Parent $codexHooksTarget) -Force | Out-Null
$codexHooks = if (Test-Path -LiteralPath $codexHooksTarget) {
    Get-Content -LiteralPath $codexHooksTarget -Raw | ConvertFrom-Json
} else {
    Get-Content -LiteralPath $codexHooksSource -Raw | ConvertFrom-Json
}
$codexHooks = Remove-CliSessionRecoveryHooks $codexHooks
$codexHooksTemporary = "$codexHooksTarget.$PID.$([guid]::NewGuid().ToString('N')).tmp"
[System.IO.File]::WriteAllText($codexHooksTemporary, ($codexHooks | ConvertTo-Json -Depth 100), (New-Object System.Text.UTF8Encoding($false)))
Move-Item -LiteralPath $codexHooksTemporary -Destination $codexHooksTarget -Force

if (Test-Path -LiteralPath $claudeSettingsTarget) {
    $claudeSettings = Get-Content -LiteralPath $claudeSettingsTarget -Raw | ConvertFrom-Json
    $claudeSettings = Remove-CliSessionRecoveryHooks $claudeSettings
    $claudeSettingsTemporary = "$claudeSettingsTarget.$PID.$([guid]::NewGuid().ToString('N')).tmp"
    [System.IO.File]::WriteAllText($claudeSettingsTemporary, ($claudeSettings | ConvertTo-Json -Depth 100), (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $claudeSettingsTemporary -Destination $claudeSettingsTarget -Force
}

New-Item -ItemType Directory -Path $desktopDirectory -Force | Out-Null
$shortcutShell = New-Object -ComObject WScript.Shell
$saveShortcut = $shortcutShell.CreateShortcut($saveShortcutPath)
$saveShortcut.TargetPath = Join-Path $env:SystemRoot 'System32\wscript.exe'
$saveShortcut.Arguments = "`"$(Join-Path $UserProfilePath 'save-sessions-hidden.vbs')`""
$saveShortcut.WorkingDirectory = $UserProfilePath
$saveShortcut.Description = 'Save exact CLI sessions for recovery'
$saveShortcut.Save()
$restoreShortcut = $shortcutShell.CreateShortcut($restoreShortcutPath)
$restoreShortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$restoreShortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$(Join-Path $UserProfilePath 'restore-sessions.ps1')`""
$restoreShortcut.WorkingDirectory = $UserProfilePath
$restoreShortcut.Description = 'Restore saved CLI sessions'
$restoreShortcut.Save()

$manifest = foreach ($name in $names) {
    $target = Join-Path $UserProfilePath $name
    [pscustomobject]@{ Path=$target; SHA256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash }
}
$manifest += [pscustomobject]@{ Path=$codexHooksTarget; SHA256=(Get-FileHash -LiteralPath $codexHooksTarget -Algorithm SHA256).Hash }
if (Test-Path -LiteralPath $claudeSettingsTarget) {
    $manifest += [pscustomobject]@{ Path=$claudeSettingsTarget; SHA256=(Get-FileHash -LiteralPath $claudeSettingsTarget -Algorithm SHA256).Hash }
}
$manifest += @($saveShortcutPath, $restoreShortcutPath) | ForEach-Object { [pscustomobject]@{ Path=$_; SHA256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash } }
$manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backupDirectory 'installed-files.json') -Encoding UTF8

$autoSaveTask = $null
if ([string]::Equals($targetProfile, $currentProfile, [System.StringComparison]::OrdinalIgnoreCase)) {
    $configureAutoSave = Join-Path $UserProfilePath 'configure-cli-session-autosave.ps1'
    $autoSaveTask = & $configureAutoSave -UserProfilePath $UserProfilePath -Disabled:$DeferAutoSaveStart -Start:(-not $DeferAutoSaveStart)
}

Write-Output "Installed CLI session recovery utilities."
Write-Output "Previous live files: $backupDirectory"
$manifest | Format-Table -AutoSize
if ($autoSaveTask) { $autoSaveTask | Format-List }
if ($DeferAutoSaveStart -and $autoSaveTask) { Write-Output 'CLI Session AutoSave was installed disabled for deployment-state verification.' }
