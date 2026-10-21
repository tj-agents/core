[CmdletBinding()]
param(
    [string]$UserProfilePath = $env:USERPROFILE,
    [switch]$DeferAutoSaveStart,
    [switch]$Check
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
$isCurrentProfile = [string]::Equals($targetProfile, $currentProfile, [System.StringComparison]::OrdinalIgnoreCase)
$desktopDirectory = if ($isCurrentProfile) { [Environment]::GetFolderPath('Desktop') } else { Join-Path $UserProfilePath 'Desktop' }
$saveShortcutPath = Join-Path $desktopDirectory 'SAVE CLI SESSIONS.lnk'
$restoreShortcutPath = Join-Path $desktopDirectory 'RESTORE CLI SESSIONS.lnk'
$autoSaveTaskName = 'CLI Session AutoSave'
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

function Test-CliSessionRecoveryHooks([string] $Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $settings = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    $hooksProperty = $settings.PSObject.Properties['hooks']
    if (-not $hooksProperty) { return $false }
    foreach ($eventProperty in @($settings.hooks.PSObject.Properties)) {
        foreach ($group in @($eventProperty.Value)) {
            $groupHooksProperty = $group.PSObject.Properties['hooks']
            if (-not $groupHooksProperty) { continue }
            if (@($groupHooksProperty.Value | Where-Object { [string]$_.command -match '(?i)cli-session-hook\.ps1' }).Count) { return $true }
        }
    }
    return $false
}

$shortcutShell = New-Object -ComObject WScript.Shell
$shortcuts = @(
    [pscustomobject]@{
        Path = $saveShortcutPath
        TargetPath = Join-Path $env:SystemRoot 'System32\wscript.exe'
        Arguments = "`"$(Join-Path $UserProfilePath 'save-sessions-hidden.vbs')`""
        Description = 'Save exact CLI sessions for recovery'
    },
    [pscustomobject]@{
        Path = $restoreShortcutPath
        TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$(Join-Path $UserProfilePath 'restore-sessions.ps1')`""
        Description = 'Restore saved CLI sessions'
    }
)

function Test-ShortcutCurrent($Shortcut) {
    if (-not (Test-Path -LiteralPath $Shortcut.Path -PathType Leaf)) { return $false }
    $existing = $shortcutShell.CreateShortcut($Shortcut.Path)
    return [string]::Equals($existing.TargetPath, $Shortcut.TargetPath, [System.StringComparison]::OrdinalIgnoreCase) -and
        $existing.Arguments -eq $Shortcut.Arguments -and
        [string]::Equals($existing.WorkingDirectory, $UserProfilePath, [System.StringComparison]::OrdinalIgnoreCase)
}

$staleNames = @($names | Where-Object {
    $target = Join-Path $UserProfilePath $_
    -not (Test-Path -LiteralPath $target -PathType Leaf) -or
        (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath (Join-Path $sourceDirectory $_) -Algorithm SHA256).Hash
})
$codexHooksStale = -not (Test-Path -LiteralPath $codexHooksTarget -PathType Leaf) -or (Test-CliSessionRecoveryHooks $codexHooksTarget)
$claudeSettingsStale = Test-CliSessionRecoveryHooks $claudeSettingsTarget
$staleShortcuts = @($shortcuts | Where-Object { -not (Test-ShortcutCurrent $_) })
$autoSaveTaskMissing = $false
if ($isCurrentProfile) {
    $listenerPath = Join-Path $UserProfilePath 'cli-session-shutdown-listener.ps1'
    $registeredAutoSaveTask = Get-ScheduledTask -TaskName $autoSaveTaskName -ErrorAction SilentlyContinue
    $autoSaveTaskMissing = -not $registeredAutoSaveTask -or -not ([string]$registeredAutoSaveTask.Actions.Arguments -like "*$listenerPath*")
}

$drift = @()
$drift += @($staleNames | ForEach-Object { "deploy $(Join-Path $UserProfilePath $_)" })
if ($codexHooksStale) { $drift += "remove recovery hooks from $codexHooksTarget" }
if ($claudeSettingsStale) { $drift += "remove recovery hooks from $claudeSettingsTarget" }
$drift += @($staleShortcuts | ForEach-Object { "update shortcut $($_.Path)" })
if ($autoSaveTaskMissing) { $drift += "register the $autoSaveTaskName task" }

if ($Check) {
    $drift | ForEach-Object { Write-Output $_ }
    if ($drift.Count) { exit 1 }
    Write-Output 'CLI session recovery is current.'
    exit 0
}

$backedUp = $false
function Backup-DeployedFile([string] $Path, [string] $Name) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if (-not $script:backedUp) {
        New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
        $script:backedUp = $true
    }
    Copy-Item -LiteralPath $Path -Destination (Join-Path $backupDirectory $Name)
}

foreach ($name in $staleNames) { Backup-DeployedFile (Join-Path $UserProfilePath $name) $name }
if ($codexHooksStale) { Backup-DeployedFile $codexHooksTarget 'codex-hooks.json' }
if ($claudeSettingsStale) { Backup-DeployedFile $claudeSettingsTarget 'claude-settings.json' }
foreach ($shortcut in $staleShortcuts) { Backup-DeployedFile $shortcut.Path (Split-Path $shortcut.Path -Leaf) }

foreach ($name in $staleNames) {
    $source = Join-Path $sourceDirectory $name
    $target = Join-Path $UserProfilePath $name
    $temporary = "$target.$PID.$([guid]::NewGuid().ToString('N')).tmp"
    Copy-Item -LiteralPath $source -Destination $temporary
    Move-Item -LiteralPath $temporary -Destination $target -Force
}

if ($codexHooksStale) {
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
}

if ($claudeSettingsStale) {
    $claudeSettings = Get-Content -LiteralPath $claudeSettingsTarget -Raw | ConvertFrom-Json
    $claudeSettings = Remove-CliSessionRecoveryHooks $claudeSettings
    $claudeSettingsTemporary = "$claudeSettingsTarget.$PID.$([guid]::NewGuid().ToString('N')).tmp"
    [System.IO.File]::WriteAllText($claudeSettingsTemporary, ($claudeSettings | ConvertTo-Json -Depth 100), (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $claudeSettingsTemporary -Destination $claudeSettingsTarget -Force
}

if ($staleShortcuts.Count) { New-Item -ItemType Directory -Path $desktopDirectory -Force | Out-Null }
foreach ($shortcut in $staleShortcuts) {
    $link = $shortcutShell.CreateShortcut($shortcut.Path)
    $link.TargetPath = $shortcut.TargetPath
    $link.Arguments = $shortcut.Arguments
    $link.WorkingDirectory = $UserProfilePath
    $link.Description = $shortcut.Description
    $link.Save()
}

$manifest = foreach ($name in $names) {
    $target = Join-Path $UserProfilePath $name
    [pscustomobject]@{ Path=$target; SHA256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash }
}
$manifest += [pscustomobject]@{ Path=$codexHooksTarget; SHA256=(Get-FileHash -LiteralPath $codexHooksTarget -Algorithm SHA256).Hash }
if (Test-Path -LiteralPath $claudeSettingsTarget) {
    $manifest += [pscustomobject]@{ Path=$claudeSettingsTarget; SHA256=(Get-FileHash -LiteralPath $claudeSettingsTarget -Algorithm SHA256).Hash }
}
$manifest += @($saveShortcutPath, $restoreShortcutPath) | ForEach-Object { [pscustomobject]@{ Path=$_; SHA256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash } }
if ($backedUp) {
    $manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backupDirectory 'installed-files.json') -Encoding UTF8
}

$autoSaveTask = $null
if ($isCurrentProfile) {
    $configureAutoSave = Join-Path $UserProfilePath 'configure-cli-session-autosave.ps1'
    $autoSaveTask = & $configureAutoSave -UserProfilePath $UserProfilePath -Disabled:$DeferAutoSaveStart -Start:(-not $DeferAutoSaveStart)
}

Write-Output "Installed CLI session recovery utilities."
if ($backedUp) { Write-Output "Previous live files: $backupDirectory" }
else { Write-Output 'No deployed file changed; no backup was needed.' }
$manifest | Format-Table -AutoSize
if ($autoSaveTask) { $autoSaveTask | Format-List }
if ($DeferAutoSaveStart -and $autoSaveTask) { Write-Output 'CLI Session AutoSave was installed disabled for deployment-state verification.' }
