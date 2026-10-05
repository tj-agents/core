$ErrorActionPreference = 'Stop'

$repository = Split-Path -Parent $PSScriptRoot
$peerCli = Join-Path $repository '.agents\machine\utility\peer-cli\scripts\peer-cli.ps1'
$scratch = Join-Path ([IO.Path]::GetTempPath()) "peer-cli-tests-$([guid]::NewGuid().ToString('N'))"
$originalStateDirectory = $env:AGENT_STATE_DIRECTORY
function Assert-Contains {
    param([string] $Actual, [string] $Expected, [string] $Message)

    if (-not $Actual.Contains($Expected)) { throw "$Message Output: $Actual" }
}

function Assert-NotContains {
    param([string] $Actual, [string] $Unexpected, [string] $Message)

    if ($Actual.Contains($Unexpected)) { throw "$Message Output: $Actual" }
}

function Write-RecordedSession {
    param([string] $Directory, [string] $SessionId, [string] $Cwd)

    [pscustomobject]@{
        title = $SessionId
        session_id = $SessionId
        cwd = $Cwd
        pid = $PID
        started_at = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Directory "$SessionId.json")
}

function Invoke-PeerCliList {
    param([string] $WorkingDirectory, [string] $Under, [switch] $IncludeUnrecorded)

    Push-Location -LiteralPath $WorkingDirectory
    try {
        if ($IncludeUnrecorded) {
            if (-not $PSBoundParameters.ContainsKey('Under')) {
                return (& $peerCli list -IncludeUnrecorded 2>&1 | Out-String)
            }
            return (& $peerCli list -IncludeUnrecorded -Under $Under 2>&1 | Out-String)
        }
        if (-not $PSBoundParameters.ContainsKey('Under')) {
            return (& $peerCli list 2>&1 | Out-String)
        }
        return (& $peerCli list -Under $Under 2>&1 | Out-String)
    }
    finally {
        Pop-Location
    }
}

try {
    $stateDirectory = Join-Path $scratch 'state\cli-sessions'
    $repositoryRoot = Join-Path $scratch 'org\repo'
    $recordedDirectory = Join-Path $repositoryRoot 'child'
    $siblingDirectory = Join-Path $scratch 'org\sibling\child'
    $nearMissDirectory = Join-Path $scratch 'org\repo-other\child'
    $outsideDirectory = Join-Path $scratch 'outside'
    New-Item -ItemType Directory -Path $stateDirectory, $recordedDirectory, $siblingDirectory, $nearMissDirectory, $outsideDirectory, (Join-Path $repositoryRoot '.git') -Force | Out-Null
    $env:AGENT_STATE_DIRECTORY = Split-Path -Parent $stateDirectory

    Write-RecordedSession -Directory $stateDirectory -SessionId 'relative-scope' -Cwd $recordedDirectory
    $relativeOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under '.'
    Assert-Contains -Actual $relativeOutput -Expected 'relative-scope' -Message 'Relative -Under did not include the recorded session.'

    Write-RecordedSession -Directory $stateDirectory -SessionId 'parent-relative-scope' -Cwd $siblingDirectory
    $parentRelativeOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under '..'
    Assert-Contains -Actual $parentRelativeOutput -Expected 'parent-relative-scope' -Message 'Parent-relative -Under did not include the sibling session.'

    $forwardSlashDirectory = $recordedDirectory -replace '\\', '/'
    Write-RecordedSession -Directory $stateDirectory -SessionId 'forward-slash-scope' -Cwd $forwardSlashDirectory
    $forwardSlashRoot = $repositoryRoot -replace '\\', '/'
    $slashOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under $forwardSlashRoot
    Assert-Contains -Actual $slashOutput -Expected 'forward-slash-scope' -Message 'Forward-slash paths did not match the scope.'

    Write-RecordedSession -Directory $stateDirectory -SessionId 'near-prefix' -Cwd $nearMissDirectory
    $boundaryOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under $repositoryRoot
    Assert-NotContains -Actual $boundaryOutput -Unexpected 'near-prefix' -Message 'A sibling path sharing the repository prefix matched the scope.'

    $missingScope = Join-Path $scratch 'missing-scope'
    $missingScopeOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -Under $missingScope
    Assert-Contains -Actual $missingScopeOutput -Expected 'No CLI sessions in scope.' -Message 'A missing explicit scope did not produce an empty result.'

    $defaultOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot
    Assert-Contains -Actual $defaultOutput -Expected 'parent-relative-scope' -Message 'The default organization scope did not include the sibling session.'

    $emptyState = Join-Path $scratch 'empty-state'
    $env:AGENT_STATE_DIRECTORY = $emptyState
    . $peerCli list -All | Out-Null
    function Get-Item {
        param([string] $LiteralPath)
        [pscustomobject]@{ Parent = $null }
    }
    if ($null -ne (Get-OrganizationRoot -RepoRoot 'drive-root')) {
        throw 'A repository at a drive root must not have an organization root.'
    }
    Remove-Item function:Get-Item
    function Get-OrganizationRoot {
        param([string] $RepoRoot)
        return $null
    }
    $driveRoot = [IO.Path]::GetPathRoot($repositoryRoot)
    $driveRootScope = Get-ListScope -Sessions @(
        [pscustomobject]@{ SessionId = 'drive-root'; Cwd = $driveRoot; Recorded = $true },
        [pscustomobject]@{ SessionId = 'drive-root-child'; Cwd = (Join-Path $driveRoot 'repository-child'); Recorded = $true },
        [pscustomobject]@{ SessionId = 'outside-drive-root'; Cwd = '\\outside-server\share'; Recorded = $true }
    ) -RepoRoot $driveRoot
    $driveRootSessions = ($driveRootScope.Sessions | ForEach-Object { $_.SessionId }) -join ','
    if ($driveRootSessions -ne 'drive-root,drive-root-child') {
        throw "Drive-root fallback returned the wrong sessions: $driveRootSessions"
    }

    $env:AGENT_STATE_DIRECTORY = Split-Path -Parent $stateDirectory
    $fakeClaude = Join-Path $scratch 'claude.exe'
    Copy-Item -LiteralPath $env:ComSpec -Destination $fakeClaude
    $fakeProcess = Start-Process -FilePath $fakeClaude -ArgumentList '/c', 'ping -n 31 127.0.0.1 > nul' -PassThru -WindowStyle Hidden
    try {
        $unrecordedUnderOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -IncludeUnrecorded -Under $outsideDirectory
        Assert-Contains -Actual $unrecordedUnderOutput -Expected ([string]$fakeProcess.Id) -Message 'Unrecorded sessions were hidden by the explicit scope filter.'
        $unrecordedDefaultOutput = Invoke-PeerCliList -WorkingDirectory $repositoryRoot -IncludeUnrecorded
        Assert-Contains -Actual $unrecordedDefaultOutput -Expected ([string]$fakeProcess.Id) -Message 'Unrecorded sessions were hidden by the default scope filter.'
    }
    finally {
        if (-not $fakeProcess.HasExited) { & taskkill.exe /PID $fakeProcess.Id /T /F | Out-Null }
        $fakeProcess.WaitForExit()
        $fakeProcess.Dispose()
    }
}
finally {
    $env:AGENT_STATE_DIRECTORY = $originalStateDirectory
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS peer-cli.tests.ps1'
