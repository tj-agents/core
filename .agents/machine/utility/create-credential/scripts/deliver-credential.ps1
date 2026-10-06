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

    [string[]]$SelectedRepos,

    [string]$ExpectedPrefix,

    # Masked paste instead of the clipboard, for a session without a workable clipboard. Tommy runs
    # this himself in his own interactive terminal - an agent's non-interactive shell has no stdin to
    # paste into.
    [switch]$Prompt
)

$ErrorActionPreference = 'Stop'

function Assert-SafeArgument {
    param([string]$Value, [string]$Label)
    if ($Value -and $Value.StartsWith('-')) {
        throw "-$Label '$Value' starts with '-' and would be parsed as a flag; rename it."
    }
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'gh CLI not found on PATH; install GitHub CLI before delivering to gh-secret.'
}
if ($Repo -and $Org) { throw 'Pass -Repo or -Org, not both.' }
if ($Destination -eq 'gh-secret' -and -not $Repo -and -not $Org) {
    throw 'gh-secret needs -Repo <owner/repo> or -Org <organization>.'
}
Assert-SafeArgument -Value $Name -Label 'Name'
Assert-SafeArgument -Value $Repo -Label 'Repo'
Assert-SafeArgument -Value $Org -Label 'Org'
foreach ($selectedRepo in $SelectedRepos) {
    Assert-SafeArgument -Value $selectedRepo -Label 'SelectedRepos'
}
if ($Visibility -and $Repo) {
    throw '-Visibility only applies to -Org; gh silently ignores it with -Repo.'
}
if ($Visibility -eq 'selected' -and -not $SelectedRepos) {
    throw '-Visibility selected needs -SelectedRepos <repo> (one or more); otherwise gh creates a secret no repository can read.'
}
if ($Visibility -ne 'selected' -and $SelectedRepos) {
    throw '-SelectedRepos only applies with -Visibility selected.'
}
if ($Name -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
    throw "Secret name '$Name' is not a valid GitHub Actions secret name (letters, digits and underscore; cannot start with a digit)."
}
if ($Name -match '^GITHUB_') {
    throw "Secret name '$Name' starts with the reserved 'GITHUB_' prefix."
}

$deliveredValue = $null
$clearStatus = if ($Prompt) { 'skipped' } else { 'pending' }

try {
    $value = if ($Prompt) {
        $secure = Read-Host -AsSecureString "Paste the value for $Name"
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try {
            [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        }
        finally {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
            $secure.Dispose()
        }
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

    if (-not $Prompt) { $deliveredValue = $value }

    switch ($Destination) {
        'gh-secret' {
            $target = if ($Repo) { @('--repo', $Repo) } else { @('--org', $Org) }
            if ($Org -and $Visibility) {
                $target += @('--visibility', $Visibility)
                if ($Visibility -eq 'selected') { $target += @('--repos', ($SelectedRepos -join ',')) }
            }

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
}
finally {
    if ($clearStatus -eq 'pending') {
        $current = $null
        try { $current = Get-Clipboard -Raw } catch { $current = $null }
        if ($current -and $current.Trim() -eq $deliveredValue) {
            Set-Clipboard -Value ' '
            $after = $null
            try { $after = Get-Clipboard -Raw } catch { $after = $null }
            if ($null -ne $after -and $after.Trim() -ne $deliveredValue) {
                $clearStatus = 'cleared'
            }
            else {
                $clearStatus = 'failed'
                Write-Warning 'The clipboard still holds the credential after clearing; clear it manually. Windows clipboard history or cloud sync may also retain the earlier copy.'
            }
        }
        else {
            $clearStatus = 'already-changed'
        }
    }
    $deliveredValue = $null
}

$clearedNote = switch ($clearStatus) {
    'cleared' { '; clipboard cleared' }
    'failed' { '; clipboard still holds the credential, clear it manually' }
    'already-changed' { '; clipboard already held different content, nothing cleared' }
    default { '' }
}

$where = if ($Repo) { $Repo } else { "org $Org" }
"Delivered $length chars to $Destination $Name ($where); secret listed at destination$clearedNote."
