# Configurable auto-merge

## Authorization

Tommy, 2026-10-08: design and implement a repository-declared, opt-in auto-merge setting for tj-agents/core; test, commit, push, and open a pull request. Merge only when the setting and existing delivery authority permit it.

## Outcome

Repositories can explicitly enable or disable agent-initiated auto-merge. When omitted, no auto-merge action occurs. When enabled, the delivery workflow may arm auto-merge only after its existing exact-head checks, independent review, and readiness decision pass; the necessary host permission is derived from that declaration. The setting must never grant merging by default or bypass existing stop classes and scoped authorization.

## Source context

- Existing merge authorization resolves to absent unless the user, a goal, or a scoped approval records it.
- PR #153 exposed that an explicit user approval cannot reach a disconnected live Codex session reliably.
- `harness_permissions_sync.py` already composes host permission grants from installed marketplace declarations; its previous cache/manifest discovery does not establish provenance.

## Decisions

- This is a new feature slice, isolated at `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Feature-ConfigurableAutoMerge` on `Feature/ConfigurableAutoMerge`, based on `origin/main` `9561267`.
- Add optional, strict-boolean `auto_merge` to the existing `.agents/delivery-authorization.json` schema. Omission and `false` disable auto-merge; only `true` enables the mechanism.
- `auto_merge: true` grants no merge authority. Arming requires separately resolved standing or scoped merge authority, all six existing stop classes and configured custom stops passing, no hold label, and current-head CI, review, and readiness checks passing.
- Example: `{ "standing_authorization": "absent", "instruction": null, "auto_merge": true }` enables the mechanism but supplies no authority.
- The guarded CLI is `python -B <engineering>/workflows/auto_merge.py --root <absolute-checkout>`. It accepts exactly those arguments, derives the bound PR and head itself, and uses fixed `gh --repo --match-head-commit` operations. Generate exact-root-scoped Claude and Codex allowances from this guarded command through trusted installed-plugin permission sync only. Core declares no allowance and does not opt in its own feature PR.
- The successor owns this workstream only. It must not modify PR #153 or the `Fix/HandoffRequestPhrasing` worktree.

## Execution checkpoint

- Keep this GOAL as the single progress owner; do not create a duplicate ledger or roadmap. It is not an `_PLAN`.
- Implement one atomic slice on the current branch, based on `origin/main` `9561267` (fetch confirmed zero commits behind): runtime, schema, guarded permission, and tests together. Expected size is 15–25 files and fewer than 1,000 substantive lines. No intermediate state may grant an unsafe permission.
- Runtime owner: `.agents/continuation/owner.json`, id `18eee3b41f0bd0778e335c43`. Registration succeeded as `AgentStandards-Continuation-eebc798108dcb5878a7b3460ff97109b8f45e206288b5593b5df38eb29fa53de`, foreground parent PID `43300`; an observed wake returned `foreground-owned` without launching another writer.
- Authored implementation is complete. Strict shared policy validation and conditional grants are bound to enabled/applicable installed-source provenance and complete package bytes; own-resource resolution passes canonical and both generated host layouts. Native Codex AppServer `plugin/list` was verified on the installed CLI; Claude uses its installed-plugin and marketplace registries. The guarded command preserves the canonical local review-file fallback and rejects stale, unresolved and invalid security evidence. Resolver debt is tracked in `docs/workflows/TECH_DEBT.md`; the explicit `name=canonical/path` workaround is in use.
- Final focused regressions: permission sync 25, guarded wrapper 9, delivery runtime 29, direct binding hook 33, harness manifests 14. Captured logs are under the Git-private `agent-workflow/runs/configurable-auto-merge/artifacts` directory, including `packaged-resource-lookup`, `guarded-merge-final`, `policy-runtime-final2`, and `direct-auto-hook-final3` labels. Generator order completed as `final2-digests` then `final2-sync-generated`; final generated, digest and manifest checks, source-layout tests (19), skill packaging, paired instruction files (3), tier payload and authored diff checks all pass.
- Measured slice assessment against `origin/main`: 13 source files (+608/-98), 6 test files (+457/-3), 3 documentation files (+79/-0), plus 21 generated files (+1918/-793) excluded from the PR. The 1,166 source/test changed lines warrant an atomicity exception: a declaration-only layer exposes an unconsumed setting, a permission-first layer separates a privileged grant from its guard, and extracting the small shared validator creates another gated dependency without an independent outcome. Keep this capability atomic with focused consumer tests, verified generation, independent security review, and exact-head draft-PR CI; add no unrelated scope.
- Out-of-scope baseline: static permission grants still consume installed/cache manifests without the new conditional grant's source verification. The explicit configurable-auto-merge-only authorization excludes a separate static-grant hardening workstream. Resolve when all static grants bind enabled/applicable installation records to verified publisher/source/package bytes with regression coverage; this goal records the observation without changing unrelated permission behavior.
- Next lane: L7 for the verified authored checkpoint, native review with its declared specialist, L2 for independent security evidence at the same frozen candidate, then L7 for authorized publication.

## Completion

- A documented explicit enable/disable configuration is validated on both supported hosts.
- Omission has a regression test proving that it does not permit or arm auto-merge.
- Enabled behavior has coverage proving that it honors the existing readiness, review, authorization, and stop gates.
- Authored source, tests, and any required manifest/harness declarations are committed; a PR is open with validation evidence.

## Next Steps

Scope: complete the authorized goal through a draft PR. Current slice: configurable auto-merge mechanism. Remaining scope: focused and repository checks, independent review, commit, push, and draft PR. Merge remains conditional on the configured setting and existing delivery authority.

Done when focused and repository-required checks pass, independent review passes, and the code is committed, pushed, and open as a draft PR with evidence recorded here. Merge is conditional on the setting and existing delivery authority.
