[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [int[]]$ProcessId,
    [Parameter(Mandatory)]
    [string]$OutputPath,
    [Parameter(Mandatory)]
    [string]$ErrorPath
)

$ErrorActionPreference = 'Stop'
try {
    Import-Module (Join-Path $PSScriptRoot 'cli-session-vault.psm1') -Force
    $result = & (Get-Module cli-session-vault) {
        param([int[]]$Ids)
        Initialize-CliOpenFileProbe
        [CliOpenFileProbe]::GetOpenFiles($Ids)
    } $ProcessId
    $serializable = [ordered]@{}
    foreach ($entry in $result.GetEnumerator()) { $serializable[[string]$entry.Key] = @($entry.Value) }
    [System.IO.File]::WriteAllText($OutputPath, ($serializable | ConvertTo-Json -Depth 5 -Compress), (New-Object System.Text.UTF8Encoding($false)))
} catch {
    [System.IO.File]::WriteAllText($ErrorPath, $_.Exception.ToString(), (New-Object System.Text.UTF8Encoding($false)))
    exit 1
}
