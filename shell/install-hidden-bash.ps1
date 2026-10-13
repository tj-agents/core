[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch] $VerifyOnly,
    [string] $DocumentsPath = [Environment]::GetFolderPath('MyDocuments')
)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'hidden-bash.c'
$target = Join-Path $PSScriptRoot 'hidden-bash.exe'
$buildTarget = Join-Path $PSScriptRoot 'hidden-bash.build.exe'
$profileSource = Join-Path $PSScriptRoot 'hidden-bash-profile.ps1'
$profileStart = '# >>> core hidden bash >>>'
$profileEnd = '# <<< core hidden bash <<<'
$escapedProfileSource = $profileSource.Replace("'", "''")
$profileBlock = "$profileStart`r`n. '$escapedProfileSource'`r`n$profileEnd"
$profileTargets = @(
    (Join-Path $DocumentsPath 'PowerShell\Microsoft.PowerShell_profile.ps1'),
    (Join-Path $DocumentsPath 'WindowsPowerShell\Microsoft.PowerShell_profile.ps1')
)
$realBash = [Environment]::GetEnvironmentVariable('TJ_AGENTS_REAL_GIT_BASH', 'User')
if (-not $realBash) {
    $existing = [Environment]::GetEnvironmentVariable('CLAUDE_CODE_GIT_BASH_PATH', 'User')
    if ($existing -and $existing -ne $target) { $realBash = $existing }
}
if (-not $realBash) { $realBash = 'C:\Program Files\Git\bin\bash.exe' }
if ($realBash -eq $target) { throw 'The real Git Bash path cannot point to the hidden proxy itself' }
if (-not (Test-Path -LiteralPath $realBash -PathType Leaf)) { throw "Git Bash not found: $realBash" }

if ($VerifyOnly) {
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Hidden Bash proxy missing: $target" }
    if ([Environment]::GetEnvironmentVariable('TJ_AGENTS_REAL_GIT_BASH', 'User') -ne $realBash) { throw 'Real Bash user environment is not configured' }
    if ([Environment]::GetEnvironmentVariable('CLAUDE_CODE_GIT_BASH_PATH', 'User') -ne $target) { throw 'Claude Code user environment is not configured' }
    foreach ($profileTarget in $profileTargets) {
        if (-not (Test-Path -LiteralPath $profileTarget -PathType Leaf) -or -not [IO.File]::ReadAllText($profileTarget).Contains($profileBlock)) {
            throw "Claude proxy profile block is not installed in $profileTarget"
        }
    }
    "verified: $target -> $realBash"
    return
}

$compiler = (Get-Command clang.exe -CommandType Application -ErrorAction SilentlyContinue).Source
if (-not $compiler) { $compiler = (Get-Command gcc.exe -CommandType Application -ErrorAction SilentlyContinue).Source }
if (-not $compiler) { throw 'clang.exe or gcc.exe is required to build the Windows GUI Bash proxy' }
if ($PSCmdlet.ShouldProcess($target, 'build the no-window Bash proxy')) {
    try {
        & $compiler -O2 -municode -mwindows $source -o $buildTarget
        if ($LASTEXITCODE -ne 0) { throw "Failed to build $buildTarget" }
        $startInfo = [Diagnostics.ProcessStartInfo]::new($buildTarget)
        $startInfo.ArgumentList.Add('-c')
        $startInfo.ArgumentList.Add('printf HIDDEN_BASH_OK; exit 73')
        $startInfo.Environment['TJ_AGENTS_REAL_GIT_BASH'] = $realBash
        $startInfo.UseShellExecute = $false
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $startInfo.CreateNoWindow = $true
        $probe = [Diagnostics.Process]::Start($startInfo)
        try {
            if (-not $probe.WaitForExit(10000)) {
                $probe.Kill($true)
                throw 'The hidden Bash proxy smoke check timed out'
            }
            $probeOutput = $probe.StandardOutput.ReadToEnd()
            if ($probe.ExitCode -ne 73 -or $probeOutput -ne 'HIDDEN_BASH_OK') {
                throw 'The hidden Bash proxy did not preserve Bash output and exit status'
            }
        }
        finally { $probe.Dispose() }
        Move-Item -LiteralPath $buildTarget -Destination $target -Force
    }
    finally {
        Remove-Item -LiteralPath $buildTarget -ErrorAction SilentlyContinue
    }
}
if ($PSCmdlet.ShouldProcess('user environment', 'configure Claude Code to use the no-window Bash proxy')) {
    [Environment]::SetEnvironmentVariable('TJ_AGENTS_REAL_GIT_BASH', $realBash, 'User')
    [Environment]::SetEnvironmentVariable('CLAUDE_CODE_GIT_BASH_PATH', $target, 'User')
    $env:TJ_AGENTS_REAL_GIT_BASH = $realBash
    $env:CLAUDE_CODE_GIT_BASH_PATH = $target
}
foreach ($profileTarget in $profileTargets) {
    $current = if (Test-Path -LiteralPath $profileTarget -PathType Leaf) { [IO.File]::ReadAllText($profileTarget) } else { '' }
    if ($current.Contains($profileBlock)) { continue }
    $pattern = [regex]::Escape($profileStart) + '(?s).*?' + [regex]::Escape($profileEnd)
    $withoutOld = [regex]::Replace($current, $pattern, '').TrimEnd()
    $next = if ($withoutOld) { "$withoutOld`r`n`r`n$profileBlock`r`n" } else { "$profileBlock`r`n" }
    if ($next -eq $current) { continue }
    if ($PSCmdlet.ShouldProcess($profileTarget, 'load the Claude proxy in new PowerShell sessions')) {
        [void](New-Item -ItemType Directory -Path (Split-Path -Parent $profileTarget) -Force)
        [IO.File]::WriteAllText($profileTarget, $next, [Text.UTF8Encoding]::new($false))
    }
}
if ($WhatIfPreference) { "previewed: $target -> $realBash" }
else { "configured: $target -> $realBash" }
