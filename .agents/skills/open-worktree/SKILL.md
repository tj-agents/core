---
name: open-worktree
description: Create, inspect, or close one isolated git worktree so every in-flight delivery branch gets its own checkout and carries its plan and ledger. Covers the planning-only no-worktree exception, the worktree identity gate, starting at fetched origin/main, branch casing, flat folders, safe audit/close/retire, and stale guidance links. Use when the user wants a worktree created, a branch or PR isolated, worktrees listed, or one closed or retired.
domain: process
---

# One checkout per in-flight branch

Give every in-flight branch its own working tree, so two branches cannot corrupt each other through a single
shared checkout. The failure this prevents is concrete: an unrelated guidance edit bleeding into a refactor's
PR, or a build running against a tree half-switched to another branch.

**Planning-only authoring is the exception.** It needs no isolated worktree. Once implementation starts, the
delivery branch's worktree owns the plan and ledger for that slice, and material updates ride its substantive
commits. Never maintain a competing normal-checkout copy while that worktree is active.

Creation is *setup*, never the deliverable. **When the invocation also carries a task, continue that task in
the new checkout in the same session**, addressing it by absolute path — nothing requires a fresh session, and
stopping after the checkout exists is the failure this sentence prevents.

## Choose the operation

| Intent | Procedure |
|---|---|
| Planning-only authoring with no delivery branch | Use the normal checkout; **do not create a worktree** |
| Create or restore one branch checkout | **Create**, below |
| Resume plan-managed work | The repository's plan floor — its ledger owns the branch, PR and worktree identity |
| Read-only inventory | `./scripts/worktrees.ps1 audit` |
| Close a merged PR's worktree | `./scripts/worktrees.ps1 close` |
| Retire a superseded no-PR branch | `./scripts/worktrees.ps1 retire` |

**`worktrees.ps1` is a vendored constant, not a per-repo path.** Its body carries no repo-specific value — no
suite name, no project path, no service roster — so it is generated into every consumer beside the hooks and
may be named outright. Cleanup is repository automation and needs no agent judgment: the script classifies
registered worktrees from Git evidence and **never deletes**, refusing dirty, detached, mismatched, post-PR,
case-colliding, persistent and missing-ledger states. **Never substitute a manual deletion for `retire`.**

## Create

1. **Apply the repository's worktree identity gate first.** Read its guidance and state whether the task
   matches the current branch directly, or is branch-local work because it changes code not yet on the default
   branch. Verify against the dirty paths and the other registered worktrees rather than matching on a shared
   refactor name. **If neither basis holds, stop and ask.** Do not split code that exists only on the current
   feature branch onto a new branch. A planning-only task never reaches this creation procedure; active
   plan-managed delivery continues in its ledger's owning worktree.
2. **Confirm no open red generated-sync PR before starting new work** — [`merging`](../merging/SKILL.md) owns
   that gate and the reason it is a branch-time check rather than a per-prompt one. A red one means the
   platform is mid-break; clear it first.
3. Resolve the common repository root with Git, so the operation works from any existing checkout:

   ```powershell
   $commonDirectory = git rev-parse --path-format=absolute --git-common-dir
   $repository = [IO.Path]::GetDirectoryName($commonDirectory.Trim())
   ```

4. **Fetch with pruning, and start new branches at the fetched remote default — never at local default**,
   which is routinely stale. Naming is [`git-branching`](../git-branching/SKILL.md)'s: the repository's capitalized
   `<Type>/<Name>` form, and **never a second casing of an existing name** — a case-insensitive filesystem
   cannot hold both, and the remote then breaks fetch for everyone. Match an existing branch's casing rather
   than creating a variant.

   ```powershell
   $branch = '<Type>/<Name>'
   $path = Join-Path $repository ".worktrees/$($branch.Replace('/', '-'))"
   git -C $repository fetch origin --prune
   git -C $repository worktree add $path -b $branch origin/<default>
   ```

   For an existing local branch, omit `-b` and the start point. For a remote-only branch, create its matching
   local tracking ref with `-b $branch --track "origin/$branch"`.

5. **Flatten `/` to `-` in the folder name.** A branch hierarchy left unflattened creates nested worktree
   roots, which are ambiguous to every tool that walks the tree. `worktrees.ps1 audit` recognises both a
   `.worktrees` directory inside the repository and a `<repo>.worktrees` sibling, so either placement is
   inventoried — but **never** place one under a directory the agent harness reserves for its own ephemeral
   worktrees, where manual trees collide with it and land as stray gitlinks that break submodule-aware
   checkouts.
6. **Verify** the resulting path, branch, HEAD, base or existing remote head, and clean status. Use absolute
   paths for every subsequent tool call in the session.

## Do not copy or junction guidance directories into a new checkout

Tracked `.agents` and `.claude` content **arrives with the checkout**; copying or linking it is redundant at
best. The real hazard is the untracked remainder: a directory left behind by an earlier layout, or a local copy
of a skill that has since moved into an installed plugin. Linking those into a fresh tree **resurrects stale
duplicates of skills that now ship from the plugin**, which then shadow the current ones — silently, because
both resolve under the same name.

A deletion that follows a link into the main checkout's real files is the other reason to avoid them. Where a
link already exists, unlink it before removing a tree.

## Report

For creation: the branch, the absolute path, HEAD and base, and whether the attached task continued. For
inspection or closure: the script's classification, or the verified surviving worktree list.
