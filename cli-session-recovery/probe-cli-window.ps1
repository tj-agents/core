[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ProcessIds,
    [Parameter(Mandatory)][string]$Out,
    [int]$DeadlineSeconds = 87
)

$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'cli-session-vault.psm1') -Force

function Write-ProbeResult($TitleMap, $WindowGroups, $ProbedProcessIds, $AbsentProcessIds, $FailedProcessIds, [bool]$Complete, [string]$Path) {
    $json = [ordered]@{
        titleMap = $TitleMap
        windowGroups = $WindowGroups
        probedProcessIds = @($ProbedProcessIds)
        absentProcessIds = @($AbsentProcessIds)
        failedProcessIds = @($FailedProcessIds)
        complete = $Complete
    } | ConvertTo-Json -Compress
    $temporary = "$Path.tmp"
    [System.IO.File]::WriteAllText($temporary, $json, (New-Object System.Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

$deadline = (Get-Date).AddSeconds($DeadlineSeconds)
$windowGroups = @{}
$probedProcessIds = @()
$absentProcessIds = @()
$failedProcessIds = @()
$requestedProcessIds = @($ProcessIds.Split(',') | Where-Object { $_ -match '^\d+$' })
$titleMap = @{}
Write-ProbeResult $titleMap $windowGroups $probedProcessIds $absentProcessIds $failedProcessIds $false $Out
$titleMap = & (Get-Module cli-session-vault) { Get-WindowsTerminalTitleWindowMap }
Write-ProbeResult $titleMap $windowGroups $probedProcessIds $absentProcessIds $failedProcessIds $false $Out
foreach ($id in $requestedProcessIds) {
    if ((Get-Date) -ge $deadline) { break }
    $probedProcessIds += [int]$id
    $probe = Invoke-CliSessionConsoleWindowProbe ([pscustomobject]@{ ProcessId=[int]$id }) -Detailed
    if (-not $probe.Succeeded) {
        $failedProcessIds += [int]$id
    } elseif ($probe.WindowGroup) {
        $windowGroups[$id] = $probe.WindowGroup
    } else {
        $absentProcessIds += [int]$id
    }
    Write-ProbeResult $titleMap $windowGroups $probedProcessIds $absentProcessIds $failedProcessIds $false $Out
}
$complete = Test-CliSessionWindowProbeComplete $requestedProcessIds $probedProcessIds $failedProcessIds
Write-ProbeResult $titleMap $windowGroups $probedProcessIds $absentProcessIds $failedProcessIds $complete $Out
exit 0
