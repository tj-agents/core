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

    Write-Output "PowerShell host compatibility tests passed under PowerShell $($PSVersionTable.PSVersion)."
} finally {
    $env:AGENT_STATE_DIRECTORY = $originalStateDirectory
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}
