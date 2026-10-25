$python = if ($IsWindows -or $env:OS -eq 'Windows_NT') { 'python' } else { 'python3' }
& $python -B (Join-Path $PSScriptRoot 'scripts/runtime_sources.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -B (Join-Path $PSScriptRoot '.agents/dependencies/agent/.agents/agent/runtime/reload_plugins.py') --project (Get-Location).Path @args
exit $LASTEXITCODE
