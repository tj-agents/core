$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repository = Split-Path -Parent $PSScriptRoot
$peerCli = Join-Path $repository '.agents/machine/utility/peer-cli/scripts'
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('powershell host compat ' + [guid]::NewGuid().ToString('N'))
$originalStateDirectory = $env:AGENT_STATE_DIRECTORY
$utf8 = [Text.UTF8Encoding]::new($false)
function Assert([bool] $Condition, [string] $Message) { if (-not $Condition) { throw $Message } }

try {
    $scripts = @(& git -C $repository ls-files -- '.agents/*.ps1')
    Assert ($scripts.Count -gt 0) 'No authored PowerShell scripts were found.'
    foreach ($relative in $scripts) {
        $path = Join-Path $repository $relative
        $tokens = $null
        $errors = $null
        [void][Management.Automation.Language.Parser]::ParseFile($path, [ref] $tokens, [ref] $errors)
        if ($errors.Count) { throw "$relative does not parse under PowerShell $($PSVersionTable.PSVersion): $($errors[0].Message)" }
        Assert (-not (Select-String -LiteralPath $path -Pattern '^\s*#Requires\s+-(Version\s+[6-9]|PSEdition\s+Core)' -Quiet)) "$relative requires PowerShell 7."
    }

    $stateRoot = Join-Path $scratch 'state'
    $sessions = Join-Path $stateRoot 'cli-sessions'
    New-Item -ItemType Directory -Path $sessions -Force | Out-Null
    $env:AGENT_STATE_DIRECTORY = $stateRoot
    $title = 'Fix caf' + [char]0x00e9 + ' tab'
    $entry = [ordered]@{ session_id = 'a1b2c3d4'; title = $title; cwd = $scratch; pid = $PID; started_at = 0 }
    [IO.File]::WriteAllText((Join-Path $sessions 'a1b2c3d4.json'), ($entry | ConvertTo-Json), $utf8)

    $resolved = & (Join-Path $peerCli 'peer-cli.ps1') resolve $title
    Assert ($resolved -ceq 'a1b2c3d4') "peer-cli resolve did not read the UTF-8 registry entry: $resolved"
    $closed = & (Join-Path $peerCli 'peer-cli.ps1') close $title
    Assert ("$closed" -ceq "'$title' is already gone.") "peer-cli close did not report the departed session: $closed"

    $listed = @(& (Join-Path $peerCli 'close-tab.ps1') -List)
    Assert ($listed.Count -gt 0) 'close-tab -List produced no output.'

    $settings = Join-Path $scratch 'settings.json'
    $original = "{`r`n    `"profiles`":`r`n    {`r`n        `"defaults`":`r`n        {`r`n            `"font`": `"Caf" + [char]0x00e9 + "`"`r`n        }`r`n    }`r`n}"
    [IO.File]::WriteAllText($settings, $original, $utf8)
    & (Join-Path $peerCli 'configure-terminal-tab-close.ps1') -SettingsPath $settings | Out-Null
    $bytes = [IO.File]::ReadAllBytes($settings)
    Assert (-not ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)) 'Terminal settings gained a byte-order mark.'
    $written = $utf8.GetString($bytes)
    Assert ($written.Contains('"closeOnExit": "always"')) 'closeOnExit was not written to the defaults block.'
    Assert ($written.Contains('Caf' + [char]0x00e9)) 'Non-ASCII settings content was not preserved.'
    $again = & (Join-Path $peerCli 'configure-terminal-tab-close.ps1') -SettingsPath $settings
    Assert ("$again" -ceq "closeOnExit is already 'always'.") "A second run did not detect the existing value: $again"

    # --- configure-terminal-tab-close: a relative -SettingsPath resolves against $PWD, not the process
    # directory --- Push-Location changes $PWD without changing [Environment]::CurrentDirectory, so a
    # relative path handed to a raw .NET API (as the backup/write steps do) silently targets the wrong
    # directory unless the script resolves it against $PWD first.
    $relativeScratch = Join-Path $scratch 'relative'
    New-Item -ItemType Directory -Path $relativeScratch -Force | Out-Null
    $relativeSettings = Join-Path $relativeScratch 'settings.json'
    [IO.File]::WriteAllText($relativeSettings, $original, $utf8)
    $processDirectory = [Environment]::CurrentDirectory
    Push-Location -LiteralPath $relativeScratch
    try {
        & (Join-Path $peerCli 'configure-terminal-tab-close.ps1') -SettingsPath 'settings.json' | Out-Null
    } finally {
        Pop-Location
    }
    Assert ([Environment]::CurrentDirectory -eq $processDirectory) 'Test setup invariant broken: Push-Location changed the process directory.'
    $writtenRelative = $utf8.GetString([IO.File]::ReadAllBytes($relativeSettings))
    Assert ($writtenRelative.Contains('"closeOnExit": "always"')) 'A relative -SettingsPath did not update the file at $PWD.'
    Assert (-not (Test-Path -LiteralPath (Join-Path $processDirectory 'settings.json'))) 'A relative -SettingsPath wrote beside the process directory instead of $PWD.'

    Write-Output "PowerShell host compatibility tests passed under PowerShell $($PSVersionTable.PSVersion)."
} finally {
    $env:AGENT_STATE_DIRECTORY = $originalStateDirectory
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}
