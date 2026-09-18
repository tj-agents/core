[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('codex','claude')][string]$Tool,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')][string]$SessionId,
    [Parameter(Mandatory)][string]$WindowGroup
)

$ErrorActionPreference = 'Stop'
$env:CLI_SESSION_WINDOW_GROUP = $WindowGroup
$env:MSBUILDDISABLENODEREUSE = '1'
$env:DOTNET_CLI_USE_MSBUILD_SERVER = '0'
$env:DOTNET_PROCESSOR_COUNT = '4'

if ($Tool -eq 'codex') {
    $nativeCodex = 'C:\nvm4w\nodejs\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe'
    if (-not (Test-Path -LiteralPath $nativeCodex -PathType Leaf)) {
        throw "Native Codex executable not found: $nativeCodex"
    }
    & $nativeCodex -c 'tui.alternate_screen=always' resume $SessionId
} else {
    & "$env:USERPROFILE\.local\bin\claude.exe" --resume $SessionId
}

exit $LASTEXITCODE
