function Invoke-CodexSyncCommand {
    param(
        [Parameter(Mandatory)][string] $CodexExecutable,
        [Parameter(Mandatory)][string[]] $Arguments,
        [double] $TimeoutSeconds = 60,
        [string] $RunnerPath = (Join-Path $PSScriptRoot 'bounded_process.py')
    )

    $python = Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $command = @($CodexExecutable) + $Arguments
    if ([IO.Path]::GetExtension($CodexExecutable) -eq '.ps1') {
        $hostName = if ($PSVersionTable.PSEdition -eq 'Desktop') { 'powershell.exe' } elseif ($env:OS -eq 'Windows_NT') { 'pwsh.exe' } else { 'pwsh' }
        $shell = Join-Path $PSHOME $hostName
        $command = @($shell, '-NoProfile', '-NonInteractive',
            '-ExecutionPolicy', 'Bypass', '-File', $CodexExecutable) + $Arguments
    }
    $duration = $TimeoutSeconds.ToString('R', [Globalization.CultureInfo]::InvariantCulture)
    $previousEncoding = [Console]::OutputEncoding
    $previousErrorAction = $ErrorActionPreference
    $stdout = [Collections.Generic.List[string]]::new()
    $stderr = [Collections.Generic.List[string]]::new()
    try {
        [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
        $ErrorActionPreference = 'Continue'
        foreach ($item in @(& $python.Source -B $RunnerPath --timeout $duration -- @command 2>&1)) {
            if ($item -is [System.Management.Automation.ErrorRecord]) { $stderr.Add($item.Exception.Message) }
            else { $stdout.Add([string] $item) }
        }
        $exitCode = $LASTEXITCODE
    }
    finally {
        [Console]::OutputEncoding = $previousEncoding
        $ErrorActionPreference = $previousErrorAction
    }
    $combined = @($stdout) + @($stderr)
    if ($exitCode -ne 0) {
        throw "Codex plugin sync failed: $($Arguments -join ' '): $($combined -join ' ')"
    }
    try {
        return ($stdout -join "`n" | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw "Codex plugin sync returned invalid JSON: $($Arguments -join ' '): $($combined -join ' ')"
    }
}

function Invoke-CodexHookTrust {
    param(
        [Parameter(Mandatory)][string] $CodexExecutable,
        [Parameter(Mandatory)][string] $WorkingDirectory,
        [Parameter(Mandatory)][string] $HelperScript,
        [Parameter(Mandatory)][string] $RunnerPath,
        [double] $TimeoutSeconds = 60
    )

    $python = Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $duration = $TimeoutSeconds.ToString('R', [Globalization.CultureInfo]::InvariantCulture)
    $previousEncoding = [Console]::OutputEncoding
    $previousErrorAction = $ErrorActionPreference
    try {
        [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
        $ErrorActionPreference = 'Continue'
        $output = @(& $python.Source -B $RunnerPath --timeout $duration -- $python.Source -B $HelperScript --codex $CodexExecutable --project $WorkingDirectory 2>&1) | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.Exception.Message } else { $_ }
        }
        $exitCode = $LASTEXITCODE
    }
    finally {
        [Console]::OutputEncoding = $previousEncoding
        $ErrorActionPreference = $previousErrorAction
    }
    $output | ForEach-Object { Write-Host $_ }
    if ($exitCode -ne 0) { throw "Codex could not trust tj-agents hooks: $($output -join ' ')" }
}

function Sync-CodexStandards {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string] $CodexExecutable,
        [Parameter(Mandatory)][string] $WorkingDirectory,
        [ValidateRange(0.001, 3600)][double] $TimeoutSeconds = 60,
        [string] $HookTrustHelperScript = (Join-Path $PSScriptRoot 'codex_hook_trust.py')
    )

    Write-Host ('standards: refreshing Codex plugins ({0:g}s maximum)...' -f $TimeoutSeconds)
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $resolved = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
    $runnerSnapshot = Join-Path ([IO.Path]::GetTempPath()) ('core-plugin-sync-' + [guid]::NewGuid().ToString('N') + '.py')
    $trustSnapshot = $null
    Push-Location -LiteralPath $resolved
    try {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'bounded_process.py') -Destination $runnerSnapshot -ErrorAction Stop
        $helper = $HookTrustHelperScript
        if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) { throw "Codex hook trust helper missing: $helper" }
        $trustSnapshot = [IO.Path]::GetTempFileName()
        Copy-Item -LiteralPath $helper -Destination $trustSnapshot -Force
        $upgrade = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -RunnerPath $runnerSnapshot -TimeoutSeconds ($TimeoutSeconds - $clock.Elapsed.TotalSeconds) -Arguments @(
            'plugin', 'marketplace', 'upgrade', '--json'
        )
        if ($upgrade.errors -and @($upgrade.errors).Count -gt 0) {
            throw "Codex marketplace upgrade failed: $($upgrade.errors | ConvertTo-Json -Compress)"
        }

        $inventory = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -RunnerPath $runnerSnapshot -TimeoutSeconds ($TimeoutSeconds - $clock.Elapsed.TotalSeconds) -Arguments @(
            'plugin', 'list', '--available', '--json'
        )
        $selected = @($inventory.installed) + @($inventory.available) |
            Where-Object { $_ -and $_.enabled -and $_.marketplaceSource.sourceType -eq 'git' } |
            ForEach-Object { $_.pluginId } |
            Sort-Object -Unique
        foreach ($identity in $selected) {
            $installed = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -RunnerPath $runnerSnapshot -TimeoutSeconds ($TimeoutSeconds - $clock.Elapsed.TotalSeconds) -Arguments @(
                'plugin', 'add', $identity, '--json'
            )
            if ($installed.pluginId -ne $identity) {
                throw "Codex installed $($installed.pluginId) while refreshing $identity"
            }
        }
        if (@($selected).Count -gt 0 -or @($inventory.installed | Where-Object { $_.enabled }).Count -gt 0) {
            Invoke-CodexHookTrust -CodexExecutable $CodexExecutable -WorkingDirectory $resolved -HelperScript $trustSnapshot -RunnerPath $runnerSnapshot -TimeoutSeconds ($TimeoutSeconds - $clock.Elapsed.TotalSeconds)
        }
        return @($selected)
    }
    finally {
        Pop-Location
        Remove-Item -LiteralPath $runnerSnapshot -Force -ErrorAction SilentlyContinue
        if ($trustSnapshot) { Remove-Item -LiteralPath $trustSnapshot -Force -ErrorAction SilentlyContinue }
    }
}
