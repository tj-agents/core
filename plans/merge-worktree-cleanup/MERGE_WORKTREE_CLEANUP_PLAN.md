# Merge worktree cleanup and host retargeting

## Authorized scope

Follow the Winwrap handoff through completion: remove the verified empty residual directory once
its external host attachment is released, then correct core's shared merge workflow so a host
session attached to a merged linked worktree retargets before physical removal. Repair the shipped
handoff launcher lookup required by that fallback. Do not change Winwrap library or documentation
content, delete remote branches, force-push, edit installed plugin-cache output directly, or remove
dirty, unmerged, primary, non-empty, or open-PR-owned worktrees. Do not merge the resulting standards
PR without Tommy's explicit approval.

## Problem

PR #35 added the safe native-Git fallback when a repository lacks `scripts/worktrees.ps1`, but Step 5
still attempts physical removal before applying `base:cd`. A shell working directory, per-command
`workdir`, or `git -C` does not release the Codex/Claude host attachment to the linked worktree, so
Windows can unregister and empty it while refusing to remove the root directory. The handoff fallback
is also broken from the packaged canonical `.agents/.../scripts` location because its shared-library
lookup reaches only the shallower host skill layouts.

## Decisions

- Keep `.agents/engineering/workflow/merge/SKILL.md`, `.agents/base/cd/SKILL.md`, and the canonical
  machine launcher scripts as the authored owners; regenerate host/distribution outputs.
- Preserve every existing cleanup gate: never remove the primary checkout, dirty or unmerged
  content, or a branch with an open PR.
- Retarget the host to the primary checkout before removal when a native host `/cd` capability is
  exposed. Otherwise perform one real handoff to the primary checkout, checkpointing the exact
  delivery binding; the successor owns removal and final inventory after the predecessor releases
  the directory.
- Treat any residual path, including an empty locked directory, as incomplete cleanup. Never confuse
  Git deregistration or an empty directory with physical removal.
- Resolve shared launcher resources from every generated layout: authored source, packaged canonical
  `.agents`, and host `skills`/`codex-skills` entries.

## Phases

### 1. Complete Winwrap residual cleanup

- Re-prove that
  `C:\Users\tommy\source\repos\cpp\windows\winwrap\.worktrees\Refactor-Value-Window-Factories`
  is empty, absent from `git worktree list`, and has no remaining local or remote topic branch.
- Remove that exact directory non-recursively only after the predecessor host releases it. Do not
  terminate an unrelated process or use force against a non-empty or unresolved target.
- Verify the directory is absent while preserving current unrelated Winwrap worktrees and changes.

Verification gate: fresh filesystem and Git inventory demonstrates the exact residual directory is
absent and no registered worktree, branch, or unrelated user-owned content was changed.

### 2. Retarget before merged-worktree removal

- Amend Step 5 of `engineering:merge` so it resolves whether the target is the active host checkout
  before either the repository helper or native Git can remove it.
- When native host retargeting is exposed, invoke `/cd <primary-checkout>` through that interface and
  continue only after the host confirms the new attachment.
- When it is not exposed, invoke the canonical `handoff` workflow once with the primary checkout and
  exact delivery/cleanup binding. After verified launcher submission, the predecessor releases the
  writer and host attachment; the successor waits for that release, then owns helper/native-Git removal,
  residual-path verification, and every remaining delivery step.
- Preserve the existing helper/native-Git selection and all safety gates delivered by PR #35.

Consumption contract: an agent entering Step 5 supplies the exact repository, merged PR, target branch
and head, target worktree, primary checkout, and remote default. The native-retarget path returns control
to the same workflow only after confirmed host attachment to the primary checkout. The handoff path starts
exactly one successor in the primary checkout with that complete binding and transfers exclusive cleanup
ownership; only that successor may return final-inventory evidence to Step 6.

Verification gate: focused static/contract tests prove retarget/handoff ordering, successor ownership,
residual-path failure semantics, and the prohibition on shell `cd`/`git -C` as host-retarget substitutes.

### 3. Repair packaged launcher resolution and deliver

- Extend the narrow canonical launcher resolver so its shared `agent-cli.ps1` dependency is found from
  authored source plus every generated package layout, including `.agents/machine/.../scripts`.
- Expand packaging regression coverage to execute or resolve the actual canonical and host-discovery
  copies rather than testing only the shallower `skills/` copy.
- Add or update focused regression coverage, refresh required package versions/catalog digests,
  regenerate distributions, and run repository-mandated validation.
- Review the exact candidate, commit it, and open or update a PR. Stop at the explicit merge-approval
  gate; do not merge that PR without Tommy's approval.

Consumption contract: generated machine packages remain self-contained. Each generated launcher resolves
the same shipped package resource without relying on an author checkout or machine-local assembly, then
passes control to the unchanged shared launcher implementation.

Verification gate: focused tests plus `pwsh .agents/sync-generated.ps1 -Check` pass, independent
review findings are resolved, and delivery reaches its authorized terminal state.

## Acceptance criteria

- The exact Winwrap residual directory is absent without disturbing unrelated Winwrap work.
- The canonical merge workflow retargets or performs a real continuation handoff before removing an
  active host worktree, deletes merged worktrees by default, and rejects every residual path.
- The packaged Codex handoff fallback resolves its shared library from the installed canonical layout.
- Generated outputs and package/catalog metadata agree with canonical sources.
- Required tests, generation checks, and review are complete; the standards change is committed and its
  PR is open, awaiting Tommy's explicit merge approval.
