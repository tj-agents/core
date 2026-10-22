$python = if ($IsWindows -or $env:OS -eq 'Windows_NT') { 'python' } else { 'python3' }
& $python -B (Join-Path $PSScriptRoot '.agents/machine/scripts/reload_plugins.py') --project (Get-Location).Path @args
exit $LASTEXITCODE
