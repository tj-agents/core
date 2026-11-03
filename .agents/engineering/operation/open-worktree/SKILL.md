---
name: open-worktree
description: Select, create, inspect or close a checkout for active work. Reuse available checkouts for sequential delivery; create isolation for concurrent execution or an explicit request. Covers ownership, fresh bases, branch casing, space before restoring dependencies and safe closure. Use when selecting or managing a worktree.

kind: operation
domain: process
lane: L7
---

# Checkout isolation for active work

`engineering:branching` owns sequential delivery, required stack relationships and checkout allocation.
Reuse an available checkout for sequential work after preserving its previous work and verifying that no
writer, build, monitor or active session still owns it. Create a separate worktree when concurrent execution,
necessary isolation or an explicit request requires one. A branch or open PR can exist without its own
permanent checkout; a stack alone does not require one worktree per layer.

Planning-only authoring needs no isolated worktree. The active delivery checkout owns the plan and ledger
for its slice, and material updates ride its substantive commits. Before creating another checkout or
restoring its dependencies, inspect available space and existing generated outputs. Preserve unfinished
work and required evidence, and close completed worktrees promptly through the lifecycle below.

Creation is *setup*, never the deliverable. **When the invocation also carries a task, continue that task in
the new checkout in the same session**, addressing it by absolute path — nothing requires a fresh session, and
stopping after the checkout exists is the failure this sentence prevents.

## Choose the operation

| Intent | Procedure |
|---|---|
| Planning-only authoring with no delivery branch | Use the normal checkout; **do not create a worktree** |
| Continue sequential work in an available checkout | Verify ownership, clean/preserved status and task binding; switch branches under `engineering:branching` |
| Create or restore an actively needed isolated checkout | **Create**, below |
| Resume plan-managed work | The repository's plan floor — its ledger owns the branch, PR and worktree identity |
| Read-only inventory | `./scripts/worktrees.ps1 audit` when the repository ships it; otherwise `git worktree list --porcelain` and each entry's `git -C "<worktree>" status --porcelain` |
| Close a merged PR's worktree | `engineering:merge` Step 5's cleanup, which uses the helper when present and native Git otherwise |
| Retire a superseded no-PR branch | `./scripts/worktrees.ps1 retire` when the repository ships it; otherwise report the worktree and leave it |

**`scripts/worktrees.ps1` is repository-vendored, not plugin-shipped.** Where a repository carries it, the
script classifies registered worktrees from Git evidence and **never deletes**, refusing dirty, detached,
mismatched, post-PR, case-colliding, persistent and missing-ledger states; trust its refusal. Where it is
absent, use the fallbacks above. **Never substitute a manual deletion for `retire`.**

## Create

1. **Apply the repository's worktree identity gate first.** Read its guidance and state whether the task
   matches the current branch directly, or is branch-local work because it changes code not yet on the default
   branch. Verify against the dirty paths and the other registered worktrees rather than matching on a shared
   refactor name. A necessary dependent slice also matches: record why it must precede the parent's
   merge, then branch from that parent's tip under `engineering:branching`. Do not treat all unmerged feature code as
   one mandatory PR. **If none of these bases holds, stop and resolve ownership.** A planning-only task
   never reaches this creation procedure; active delivery continues in the ledger's recorded slice.
2. **Confirm no open red generated-sync PR before starting new work** — `engineering:merging` owns
   that gate and the reason it is a branch-time check rather than a per-prompt one. A red one means the
   platform is mid-break; clear it first.
3. **Create through the shared script, never by typing `git worktree add` yourself.** Naming is
   `engineering:branching`'s: the repository's capitalized `<Type>/<Name>` form, and **never a second
   casing of an existing name** — a case-insensitive filesystem cannot hold both, and the remote then
   breaks fetch for everyone. Match an existing branch's casing rather than creating a variant.

   ```text
   python -B <skill-directory>/scripts/create_worktree.py <Type>/<Name>    # Windows
   python3 -B <skill-directory>/scripts/create_worktree.py <Type>/<Name>   # Linux/macOS
   ```

   The script resolves the repository from any existing checkout, fetches with pruning, flattens `/` to
   `-` in the folder name, and always lands the result at `<repository-root>/.worktrees/<flattened-branch>`
   — **the only supported location.** It independently chooses the right start point (an existing local
   branch, an existing remote-only branch's tracking ref, or the fetched remote default) and prints the
   resulting branch, path, HEAD and base as JSON; read that JSON rather than re-deriving the path yourself.
   For a dependent stack layer, pass `--from <parent-ref>` with the verified parent ref and record its SHA.
   Do not merge main separately into each layer as a substitute for reconciling the stack.

4. **Never create a sibling `<repo-root-parent>/<repo-name>.worktrees/<branch>` folder, and never place one
   under a directory the agent harness reserves for its own ephemeral worktrees.** A sibling folder sits
   outside the repository's own directory tree. The native host resolves project-local settings and plugin
   registrations by walking up the physical filesystem from the working directory; a worktree nested under
   the repository root inherits the main checkout's registration for free by that walk, while a sibling
   folder never reaches it — skills enabled in the main checkout silently stay unavailable there,
   permanently, because no session refresh changes where the host looks. A directory the harness reserves
   for its own ephemeral worktrees causes a different failure: manual trees collide with it and land as
   stray gitlinks that break submodule-aware checkouts. Inventory still reports both shapes — see the table
   above — so an already-misplaced sibling worktree can be found and relocated into the nested location
   with `git worktree move`; that inventory coverage is for cleanup, not a second accepted creation target.
5. **Verify** the resulting path, branch, HEAD, base or existing remote head, and clean status. Use absolute
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
