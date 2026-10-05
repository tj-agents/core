$ErrorActionPreference = 'Stop'

# Regression coverage for the fresh-worktree audit defect: a worktree branched moments ago from
# origin/<default> has zero commits ahead, which previously made it indistinguishable from a branch
# that was actually merged and is safe to clean up. Also covers the detached-HEAD check, which used to
# pass the worktree's path where `git merge-base --is-ancestor` expects a commit, so it always failed
# and reported every detached worktree as unsafe regardless of its actual position.

$repository = Split-Path -Parent $PSScriptRoot
$script = Join-Path $repository 'scripts\worktrees.ps1'

$scratch = Join-Path ([System.IO.Path]::GetTempPath()) "core-worktrees-audit-$([guid]::NewGuid().ToString('N'))"
$origin = Join-Path $scratch 'origin.git'
$root = Join-Path $scratch 'root'

try {
    New-Item -ItemType Directory -Force -Path $scratch | Out-Null
    git init --quiet --bare --initial-branch=main $origin
    git clone --quiet $origin $root

    Push-Location $root
    try {
        git config user.email 'test@example.com'
        git config user.name 'Test'

        'seed' | Set-Content -LiteralPath (Join-Path $root 'seed.txt')
        git add seed.txt
        git commit --quiet -m 'seed'
        git push --quiet origin main
        git remote set-head origin main
        $seedHead = git rev-parse HEAD

        # --- a worktree just branched from origin/main: zero commits ahead, never worked on ---
        git worktree add --quiet .worktrees/fresh -b Fresh/Unstarted origin/main

        # --- a branch that did real work, was fast-forward merged into main, and had its remote branch deleted ---
        git worktree add --quiet .worktrees/merged -b Merged/Done origin/main
        Push-Location (Join-Path $root '.worktrees\merged')
        try {
            'merged work' | Set-Content -LiteralPath 'merged.txt'
            git add merged.txt
            git commit --quiet -m 'did some work'
            git push --quiet -u origin Merged/Done
        } finally { Pop-Location }
        git push --quiet origin Merged/Done:main
        git fetch --quiet origin
        git push --quiet origin --delete Merged/Done
        git fetch --quiet origin --prune

        # --- a detached worktree sitting at and behind the now-advanced origin/main: both safe ---
        $mainHead = git rev-parse origin/main
        git worktree add --quiet --detach .worktrees/detached-at $mainHead
        git worktree add --quiet --detach .worktrees/detached-behind $seedHead

        # --- a detached worktree with a commit of its own ahead of origin/main: unsafe ---
        git worktree add --quiet .worktrees/detached-source -b Detach/Source origin/main
        Push-Location (Join-Path $root '.worktrees\detached-source')
        try {
            'unique' | Set-Content -LiteralPath 'unique.txt'
            git add unique.txt
            git commit --quiet -m 'unique commit'
        } finally { Pop-Location }
        $uniqueHead = git rev-parse Detach/Source
        git worktree remove --force .worktrees/detached-source
        git branch -D --quiet Detach/Source
        git worktree add --quiet --detach .worktrees/detached-unsafe $uniqueHead

        $output = @(& $script audit)

        if ($output | Where-Object { $_ -like '*fresh*' }) {
            throw "A freshly branched, never-worked-on worktree was reported:`n$($output -join "`n")"
        }
        if (-not ($output | Where-Object { $_ -like 'MERGED_NOT_IN_MAIN*merged*' })) {
            throw "A merged branch whose remote was deleted was not reported:`n$($output -join "`n")"
        }
        if ($output | Where-Object { $_ -like '*detached-at*' -or $_ -like '*detached-behind*' }) {
            throw "A detached worktree at or behind origin/main was reported unsafe:`n$($output -join "`n")"
        }
        if (-not ($output | Where-Object { $_ -like 'DETACHED_UNSAFE*detached-unsafe*' })) {
            throw "A detached worktree ahead of origin/main was not reported unsafe:`n$($output -join "`n")"
        }
    } finally { Pop-Location }
} finally {
    if (Test-Path -LiteralPath $scratch) { Remove-Item -LiteralPath $scratch -Recurse -Force }
}

Write-Output 'PASS worktrees-audit.tests.ps1'
