function Invoke-CodexSyncCommand {
    param(
        [Parameter(Mandatory)][string] $CodexExecutable,
        [Parameter(Mandatory)][string[]] $Arguments
    )

    $output = @(& $CodexExecutable @Arguments 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Codex plugin sync failed: $($Arguments -join ' '): $($output -join ' ')"
    }
    try {
        return ($output -join "`n" | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw "Codex plugin sync returned invalid JSON: $($Arguments -join ' ')"
    }
}

function Invoke-CodexHookTrust {
    param(
        [Parameter(Mandatory)][string] $CodexExecutable,
        [Parameter(Mandatory)][string] $WorkingDirectory
    )

    $helper = Join-Path $PSScriptRoot 'codex_hook_trust.py'
    if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) { throw "Codex hook trust helper missing: $helper" }
    & python -B $helper --codex $CodexExecutable --project $WorkingDirectory | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { throw 'Codex could not trust tj-agents hooks' }
}

function Sync-CodexStandards {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string] $CodexExecutable,
        [Parameter(Mandatory)][string] $WorkingDirectory
    )

    $resolved = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
    Push-Location -LiteralPath $resolved
    try {
        $upgrade = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -Arguments @(
            'plugin', 'marketplace', 'upgrade', '--json'
        )
        if ($upgrade.errors -and @($upgrade.errors).Count -gt 0) {
            throw "Codex marketplace upgrade failed: $($upgrade.errors | ConvertTo-Json -Compress)"
        }

        $inventory = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -Arguments @(
            'plugin', 'list', '--available', '--json'
        )
        $selected = @($inventory.installed) + @($inventory.available) |
            Where-Object { $_ -and $_.enabled -and $_.marketplaceSource.sourceType -eq 'git' } |
            ForEach-Object { $_.pluginId } |
            Sort-Object -Unique
        foreach ($identity in $selected) {
            $installed = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -Arguments @(
                'plugin', 'add', $identity, '--json'
            )
            if ($installed.pluginId -ne $identity) {
                throw "Codex installed $($installed.pluginId) while refreshing $identity"
            }
        }
        Invoke-CodexHookTrust -CodexExecutable $CodexExecutable -WorkingDirectory $resolved
        return @($selected)
    }
    finally {
        Pop-Location
    }
}
