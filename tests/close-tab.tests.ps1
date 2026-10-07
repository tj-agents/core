$ErrorActionPreference = 'Stop'

$repository = Split-Path -Parent $PSScriptRoot
$closeTabScript = Join-Path $repository '.agents\machine\utility\peer-cli\scripts\close-tab.ps1'

function Assert-Equal {
    param([object] $Expected, [object] $Actual, [string] $Message)
    if ($Expected -ne $Actual) { throw "$Message Expected: $Expected Actual: $Actual" }
}

function Assert-True {
    param([object] $Actual, [string] $Message)
    if ($Actual -ne $true) { throw "$Message Actual: $Actual" }
}

function Assert-False {
    param([object] $Actual, [string] $Message)
    if ($Actual -ne $false) { throw "$Message Actual: $Actual" }
}

# -List exits before the Title-matching parameter set, so this only loads functions; it runs under
# Set-StrictMode Latest exactly as the production invocation does, which is what the regression needs.
. $closeTabScript -List | Out-Null

$zero = Resolve-TabMatches -Tabs @([pscustomobject]@{ Title = 'other-tab' }) -Title 'missing-tab'
Assert-Equal -Expected 0 -Actual $zero.Matched.Count -Message 'A title with no tabs did not resolve to zero matches.'
Assert-True -Actual $zero.Wildcard -Message 'A title with no exact match was not treated as a wildcard lookup.'

$one = Resolve-TabMatches -Tabs @([pscustomobject]@{ Title = 'solo-tab' }) -Title 'solo-tab'
Assert-Equal -Expected 1 -Actual $one.Matched.Count `
    -Message 'A single exact-title match collapsed under StrictMode instead of staying a one-element collection.'
Assert-False -Actual $one.Wildcard -Message 'A single exact title match was wrongly treated as a wildcard.'
Assert-Equal -Expected 'solo-tab' -Actual $one.Matched[0].Title -Message 'The single match did not preserve the matched tab.'

$two = Resolve-TabMatches -Tabs @([pscustomobject]@{ Title = 'dup-tab' }, [pscustomobject]@{ Title = 'dup-tab' }) -Title 'dup-tab'
Assert-Equal -Expected 2 -Actual $two.Matched.Count -Message 'Two tabs sharing an exact title did not resolve to two matches.'
Assert-False -Actual $two.Wildcard -Message 'Two exact title matches were wrongly treated as a wildcard.'

$wildcard = Resolve-TabMatches -Tabs @([pscustomobject]@{ Title = 'build-a' }, [pscustomobject]@{ Title = 'build-b' }) -Title 'build-*'
Assert-Equal -Expected 2 -Actual $wildcard.Matched.Count -Message 'A wildcard pattern did not resolve to its matching tabs.'
Assert-True -Actual $wildcard.Wildcard -Message 'A pattern with no exact match was not treated as a wildcard lookup.'

Write-Output 'PASS close-tab.tests.ps1'
