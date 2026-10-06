$ErrorActionPreference = 'Stop'

# Exercises deliver-credential.ps1 against a deterministic `gh` shim and in-process clipboard/prompt
# stubs, so this never touches a real `gh`, a real clipboard or a real credential. The shim is a .cmd
# batch file (not a .ps1) so plain command resolution finds it on PATH the same way it finds a real
# `gh`, matching the pattern already used for a `gh` shim in .agents/hooks/tests/test_delivery_binding_gate.py.

$repository = Split-Path -Parent $PSScriptRoot
$deliverScript = Join-Path $repository '.agents\machine\utility\create-credential\scripts\deliver-credential.ps1'
$scratch = Join-Path ([IO.Path]::GetTempPath()) "deliver-credential-tests-$([guid]::NewGuid().ToString('N'))"
$originalPath = $env:PATH

function Assert-Contains {
    param([string] $Actual, [string] $Expected, [string] $Message)
    if (-not $Actual.Contains($Expected)) { throw "$Message Output: $Actual" }
}

function Assert-NotContains {
    param([string] $Actual, [string] $Unexpected, [string] $Message)
    if ($Actual.Contains($Unexpected)) { throw "$Message Output: $Actual" }
}

function Assert-Throws {
    param(
        [Parameter(Mandatory)][scriptblock] $Script,
        [Parameter(Mandatory)][string] $ExpectedSubstring,
        [Parameter(Mandatory)][string] $Message
    )
    $caught = $null
    try { & $Script }
    catch { $caught = $_ }
    if (-not $caught) { throw "$Message Expected a terminating error but the script succeeded." }
    if ($caught.Exception.Message -notlike "*$ExpectedSubstring*") {
        throw "$Message Got: $($caught.Exception.Message)"
    }
}

function Reset-FakeGh {
    Remove-Item Env:\GH_FAKE_SET_EXIT, Env:\GH_FAKE_LIST_EXIT, Env:\GH_FAKE_LIST_OUTPUT_FILE, `
        Env:\GH_FAKE_LOG, Env:\GH_FAKE_CLOBBER_CLIPBOARD_FILE, Env:\GH_FAKE_CLOBBER_VALUE `
        -ErrorAction SilentlyContinue
}

function Set-FakeGhListing {
    param([string] $Name)
    $listingFile = Join-Path $scratch 'listing.txt'
    Set-Content -LiteralPath $listingFile -Value "$Name  Updated 2026-01-01" -NoNewline
    $env:GH_FAKE_LIST_OUTPUT_FILE = $listingFile
}

function Set-Clipboard {
    param([string] $Value)
    $global:clipboardSetCalls++
    Set-Content -LiteralPath $global:clipboardFile -Value $Value -NoNewline
}

function Get-Clipboard {
    param([switch] $Raw)
    $global:clipboardGetCalls++
    if (-not (Test-Path -LiteralPath $global:clipboardFile)) { return $null }
    Get-Content -LiteralPath $global:clipboardFile -Raw
}

function Read-Host {
    param(
        [Parameter(Position = 0)][string] $Prompt,
        [switch] $AsSecureString
    )
    $global:readHostCalls++
    ConvertTo-SecureString -String $global:promptValue -AsPlainText -Force
}

try {
    New-Item -ItemType Directory -Path $scratch -Force | Out-Null
    $binDir = Join-Path $scratch 'bin'
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
    $ghShim = Join-Path $binDir 'gh.cmd'
    [IO.File]::WriteAllText($ghShim, @'
@echo off
if not defined GH_FAKE_SET_EXIT set GH_FAKE_SET_EXIT=0
if not defined GH_FAKE_LIST_EXIT set GH_FAKE_LIST_EXIT=0
if defined GH_FAKE_LOG echo %* >> "%GH_FAKE_LOG%"
if /I "%1 %2"=="secret list" (
  if defined GH_FAKE_LIST_OUTPUT_FILE type "%GH_FAKE_LIST_OUTPUT_FILE%"
  exit /b %GH_FAKE_LIST_EXIT%
)
if /I "%1 %2"=="secret set" (
  more >nul
  if defined GH_FAKE_CLOBBER_CLIPBOARD_FILE (
    if defined GH_FAKE_CLOBBER_VALUE (
      echo %GH_FAKE_CLOBBER_VALUE% > "%GH_FAKE_CLOBBER_CLIPBOARD_FILE%"
    )
  )
  exit /b %GH_FAKE_SET_EXIT%
)
echo gh-fake: unrecognized command %* 1>&2
exit /b 2
'@)
    $env:PATH = "$binDir;$env:PATH"
    $global:clipboardFile = Join-Path $scratch 'clipboard.txt'
    $ghLog = Join-Path $scratch 'gh.log'

    # Happy path: clipboard relay, gh succeeds, clipboard confirmed cleared afterward.
    Reset-FakeGh
    Set-Content -LiteralPath $global:clipboardFile -Value 'github_pat_happyvalue' -NoNewline
    Set-FakeGhListing -Name 'HAPPY_TOKEN'
    $env:GH_FAKE_LOG = $ghLog
    $global:clipboardSetCalls = 0
    $global:clipboardGetCalls = 0
    $output = & $deliverScript -Destination gh-secret -Name 'HAPPY_TOKEN' -Repo 'owner/repo' -ExpectedPrefix 'github_pat_'
    Assert-Contains -Actual $output -Expected 'Delivered 21 chars to gh-secret HAPPY_TOKEN (owner/repo)' -Message 'Happy-path delivery summary is wrong.'
    Assert-Contains -Actual $output -Expected '; clipboard cleared' -Message 'A confirmed clear must be reported.'
    $clearedClipboard = Get-Content -LiteralPath $global:clipboardFile -Raw
    if ($clearedClipboard.Trim() -ne '') { throw "The clipboard was not actually overwritten: '$clearedClipboard'" }
    $ghCalls = Get-Content -LiteralPath $ghLog -Raw
    Assert-Contains -Actual $ghCalls -Expected 'secret set HAPPY_TOKEN --repo owner/repo' -Message 'gh secret set did not receive the expected arguments.'
    Assert-Contains -Actual $ghCalls -Expected 'secret list --repo owner/repo' -Message 'gh secret list did not receive the expected arguments.'

    # gh secret set fails: the clipboard must still be cleared (finally semantics), and the error propagates.
    Reset-FakeGh
    Set-Content -LiteralPath $global:clipboardFile -Value 'github_pat_failingvalue' -NoNewline
    $env:GH_FAKE_SET_EXIT = '1'
    Assert-Throws -Script { & $deliverScript -Destination gh-secret -Name 'FAILING_TOKEN' -Repo 'owner/repo' } `
        -ExpectedSubstring 'gh secret set failed' -Message 'A failing gh secret set did not raise the expected error.'
    $afterFailureClipboard = Get-Content -LiteralPath $global:clipboardFile -Raw
    if ($afterFailureClipboard.Trim() -ne '') { throw "A failed delivery left the credential on the clipboard: '$afterFailureClipboard'" }

    # The clipboard already holds different (newer) content by the time delivery finishes: never clobber it.
    Reset-FakeGh
    Set-Content -LiteralPath $global:clipboardFile -Value 'github_pat_clobbervalue' -NoNewline
    Set-FakeGhListing -Name 'CLOBBER_TOKEN'
    $env:GH_FAKE_CLOBBER_CLIPBOARD_FILE = $global:clipboardFile
    $env:GH_FAKE_CLOBBER_VALUE = 'something-else-the-user-copied'
    $clobberOutput = & $deliverScript -Destination gh-secret -Name 'CLOBBER_TOKEN' -Repo 'owner/repo'
    Assert-Contains -Actual $clobberOutput -Expected 'already held different content, nothing cleared' -Message 'Newer clipboard content must not be reported as cleared.'
    $finalClobberClipboard = Get-Content -LiteralPath $global:clipboardFile -Raw
    Assert-Contains -Actual $finalClobberClipboard -Expected 'something-else-the-user-copied' -Message 'Newer clipboard content must survive delivery.'

    # -Prompt: a SecureString paste, never touching Get-Clipboard/Set-Clipboard at all.
    Reset-FakeGh
    Set-FakeGhListing -Name 'PROMPT_TOKEN'
    $global:promptValue = 'github_pat_promptvalue'
    $global:clipboardSetCalls = 0
    $global:clipboardGetCalls = 0
    $global:readHostCalls = 0
    $promptOutput = & $deliverScript -Destination gh-secret -Name 'PROMPT_TOKEN' -Repo 'owner/repo' -Prompt -ExpectedPrefix 'github_pat_'
    if ($global:readHostCalls -ne 1) { throw "-Prompt did not read exactly once via Read-Host: $($global:readHostCalls)" }
    if ($global:clipboardSetCalls -ne 0 -or $global:clipboardGetCalls -ne 0) { throw '-Prompt must never touch the clipboard.' }
    Assert-NotContains -Actual $promptOutput -Unexpected 'clipboard' -Message '-Prompt delivery must not mention the clipboard.'
    Assert-Contains -Actual $promptOutput -Expected 'Delivered' -Message '-Prompt delivery did not report success.'

    # -Visibility selected needs -SelectedRepos, and passes it through as --repos.
    Reset-FakeGh
    Set-FakeGhListing -Name 'ORG_TOKEN'
    $env:GH_FAKE_LOG = $ghLog
    Set-Content -LiteralPath $ghLog -Value '' -NoNewline
    Set-Content -LiteralPath $global:clipboardFile -Value 'github_pat_orgvalue' -NoNewline
    & $deliverScript -Destination gh-secret -Name 'ORG_TOKEN' -Org 'my-org' -Visibility selected -SelectedRepos 'repo-a', 'repo-b' | Out-Null
    $orgCalls = Get-Content -LiteralPath $ghLog -Raw
    Assert-Contains -Actual $orgCalls -Expected '--visibility selected' -Message 'Visibility was not passed to gh secret set.'
    Assert-Contains -Actual $orgCalls -Expected '--repos repo-a,repo-b' -Message 'Selected repositories were not passed as --repos.'

    # Validation rejects before ever invoking gh: no log entry appears for any of these.
    $validationCases = @(
        @{ Params = @{ Destination = 'gh-secret'; Name = '-x'; Repo = 'owner/repo' }; Expect = 'starts with' }
        @{ Params = @{ Destination = 'gh-secret'; Name = 'bad name'; Repo = 'owner/repo' }; Expect = 'not a valid GitHub Actions secret name' }
        @{ Params = @{ Destination = 'gh-secret'; Name = 'GITHUB_TOKEN'; Repo = 'owner/repo' }; Expect = "reserved 'GITHUB_' prefix" }
        @{ Params = @{ Destination = 'gh-secret'; Name = 'OK_TOKEN'; Repo = '-owner/repo' }; Expect = 'starts with' }
        @{ Params = @{ Destination = 'gh-secret'; Name = 'OK_TOKEN'; Org = '-org' }; Expect = 'starts with' }
        @{ Params = @{ Destination = 'gh-secret'; Name = 'OK_TOKEN'; Org = 'my-org'; Visibility = 'selected' }; Expect = 'needs -SelectedRepos' }
        @{ Params = @{ Destination = 'gh-secret'; Name = 'OK_TOKEN'; Org = 'my-org'; SelectedRepos = @('repo-a') }; Expect = 'only applies with -Visibility selected' }
        @{ Params = @{ Destination = 'gh-secret'; Name = 'OK_TOKEN'; Repo = 'owner/repo'; Visibility = 'all' }; Expect = 'only applies to -Org' }
    )
    foreach ($case in $validationCases) {
        Reset-FakeGh
        Remove-Item -LiteralPath $ghLog -ErrorAction SilentlyContinue
        $env:GH_FAKE_LOG = $ghLog
        $caseParams = $case.Params
        $caseLabel = ($caseParams | ConvertTo-Json -Compress)
        Assert-Throws -Script { & $deliverScript @caseParams } -ExpectedSubstring $case.Expect `
            -Message "Validation case $caseLabel did not reject as expected."
        if (Test-Path -LiteralPath $ghLog) { throw "Validation case $caseLabel still invoked gh." }
    }
}
finally {
    Remove-Item function:Get-Clipboard, function:Set-Clipboard, function:Read-Host -ErrorAction SilentlyContinue
    Remove-Variable -Scope Global -Name clipboardFile, clipboardSetCalls, clipboardGetCalls, promptValue, readHostCalls -ErrorAction SilentlyContinue
    $env:PATH = $originalPath
    Reset-FakeGh
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS deliver-credential.tests.ps1'
