[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch] $VerifyOnly,
    [string] $DocumentsPath = [Environment]::GetFolderPath('MyDocuments')
)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'codex-no-daemon.ps1'
$start = '# >>> core codex no-daemon >>>'
$end = '# <<< core codex no-daemon <<<'
$escapedSource = $source.Replace("'", "''")
$block = "$start`r`n. '$escapedSource'`r`n$end"
$targets = @(
    (Join-Path $DocumentsPath 'PowerShell\Microsoft.PowerShell_profile.ps1'),
    (Join-Path $DocumentsPath 'WindowsPowerShell\Microsoft.PowerShell_profile.ps1')
)
foreach ($target in $targets) {
    $current = if (Test-Path -LiteralPath $target -PathType Leaf) { [IO.File]::ReadAllText($target) } else { '' }
    if ($VerifyOnly) {
        if (-not $current.Contains($block)) { throw "Codex no-daemon launcher is not installed in $target" }
        if ($current.LastIndexOf($start) -lt $current.LastIndexOf('# <<< base-agents codex launcher <<<')) {
            throw "Codex no-daemon launcher precedes the plugin launcher in $target"
        }
        "verified: $target"
        continue
    }
    if ($current.Contains($block) -and $current.LastIndexOf($start) -gt $current.LastIndexOf('# <<< base-agents codex launcher <<<')) {
        "already installed: $target"
        continue
    }
    $pattern = [regex]::Escape($start) + '(?s).*?' + [regex]::Escape($end)
    $withoutOld = [regex]::Replace($current, $pattern, '').TrimEnd()
    $next = if ($withoutOld) { "$withoutOld`r`n`r`n$block`r`n" } else { "$block`r`n" }
    if ($next -eq $current) { "already installed: $target"; continue }
    if ($PSCmdlet.ShouldProcess($target, 'install no-daemon Codex launcher')) {
        $directory = Split-Path -Parent $target
        [void](New-Item -ItemType Directory -Path $directory -Force)
        [IO.File]::WriteAllText($target, $next, [Text.UTF8Encoding]::new($false))
        "installed: $target"
    }
}
