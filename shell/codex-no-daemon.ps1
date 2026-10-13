# The shared Codex daemon currently starts Windows hook children with visible consoles.
# Keep interactive CLI sessions in-process until the host fixes that launch path.
if (-not (Get-Command Invoke-BaseAgentsCodexBeforeNoDaemon -CommandType Function -ErrorAction SilentlyContinue)) {
    $existingCodex = Get-Command codex -CommandType Function -ErrorAction SilentlyContinue
    if ($existingCodex) {
        Set-Item Function:global:Invoke-BaseAgentsCodexBeforeNoDaemon -Value $existingCodex.ScriptBlock
        function global:codex {
            $forward = @($args)
            $maintenance = @(
                'agents', 'exec', 'e', 'review', 'login', 'logout', 'mcp', 'plugin',
                'app-server', 'remote-control', 'app', 'completion', 'update', 'doctor',
                'sandbox', 'debug', 'apply', 'a', 'queue', 'archive', 'delete',
                'migrate-rollouts', 'unarchive', 'cloud', 'exec-server', 'features', 'help'
            )
            if ($forward -contains '--no-daemon' -or $forward -contains '--remote' -or
                @($forward | Where-Object { $_ -like '--remote=*' }).Count -gt 0 -or
                $forward -contains '--help' -or
                $forward -contains '-h' -or $forward -contains '--version' -or $forward -contains '-V' -or
                ($forward.Count -gt 0 -and $forward[0] -in $maintenance)) {
                & Invoke-BaseAgentsCodexBeforeNoDaemon @forward
            }
            else {
                & Invoke-BaseAgentsCodexBeforeNoDaemon --no-daemon @forward
            }
        }
    }
}
