$python = if ($IsWindows -or $env:OS -eq 'Windows_NT') { 'python' } else { 'python3' }
& $python -B (Join-Path $PSScriptRoot 'scripts/runtime_sources.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -B (Join-Path $PSScriptRoot '.agents/machine/scripts/setup_machine.py') @args
exit $LASTEXITCODE
