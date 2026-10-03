[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('gh-secret')]
    [string]$Destination,

    [Parameter(Mandatory = $true)]
    [string]$Name,

    [string]$Repo,

    [string]$Org,

    [ValidateSet('all', 'private', 'selected')]
    [string]$Visibility,

    [string]$ExpectedPrefix,

    # Masked paste instead of the clipboard, for a session without a workable clipboard.
    [switch]$Prompt
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'gh CLI not found on PATH; install GitHub CLI before delivering to gh-secret.'
}
if ($Repo -and $Org) { throw 'Pass -Repo or -Org, not both.' }
if ($Destination -eq 'gh-secret' -and -not $Repo -and -not $Org) {
    throw 'gh-secret needs -Repo <owner/repo> or -Org <organization>.'
}

$value = if ($Prompt) {
    Read-Host -MaskInput "Paste the value for $Name"
}
else {
    Get-Clipboard -Raw
}
if ($null -ne $value) { $value = $value.Trim() }
if ([string]::IsNullOrWhiteSpace($value)) {
    throw 'No value found; copy the credential first, or rerun with -Prompt and paste once.'
}
if ($value -match '\s') {
    throw 'The value contains whitespace, so this is not a single credential. Copy the credential and rerun.'
}
if ($ExpectedPrefix -and -not $value.StartsWith($ExpectedPrefix)) {
    throw "The value does not start with '$ExpectedPrefix', so this is not the expected credential. Copy the credential and rerun."
}

switch ($Destination) {
    'gh-secret' {
        $target = if ($Repo) { @('--repo', $Repo) } else { @('--org', $Org) }
        if ($Org -and $Visibility) { $target += @('--visibility', $Visibility) }

        $value | & gh secret set $Name @target
        if ($LASTEXITCODE -ne 0) { throw "gh secret set failed with exit code $LASTEXITCODE." }

        $listTarget = if ($Repo) { @('--repo', $Repo) } else { @('--org', $Org) }
        $listed = & gh secret list @listTarget | Out-String
        if ($LASTEXITCODE -ne 0) { throw "gh secret list failed with exit code $LASTEXITCODE." }
        if ($listed -notmatch "(?m)^$([regex]::Escape($Name))\b") {
            throw "Secret $Name is not listed at the destination after the set."
        }
    }
}

$length = $value.Length
$value = $null

$cleared = ''
if (-not $Prompt) {
    Set-Clipboard -Value ' '
    $back = Get-Clipboard -Raw
    if ($back -and $ExpectedPrefix -and $back.Trim().StartsWith($ExpectedPrefix)) {
        throw 'The clipboard still holds the credential after clearing; clear it manually.'
    }
    $cleared = '; clipboard cleared'
}

$where = if ($Repo) { $Repo } else { "org $Org" }
"Delivered $length chars to $Destination $Name ($where); secret listed at destination$cleared."
