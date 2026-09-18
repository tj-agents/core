[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('codex','claude')]
    [string]$Tool
)

exit 0
