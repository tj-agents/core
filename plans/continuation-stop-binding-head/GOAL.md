# Continuation Stop hook reports `binding-head-changed` for every active delivery binding

Status: handed off 2026-10-12 as a bounded side workstream from a Claude session working on the azure
app-profile goal. That session keeps its own goal and writes nothing here.

## Defect

Observed 2026-10-12. Cause confirmed by reproducing it against the installed engineering package
`d747cbed6add`.

- `.agents/hooks/continuation_stop.py` `binding_active()` compares each of `repo`, `worktree`, `branch` and
  `head` from `runtime.binding_from_artifact(artifact)` against `runtime.identity(root)`. For `head` it reads
  `binding.get("head")`.
- `.agents/workflows/delivery_runtime.py` `binding_from_artifact()` renames the artifact's `head` to
  `remote_head_sha` (`ARTIFACT_ALIASES`), so `binding.get("head")` is always `None`. It never matches the real
  HEAD, and the Stop hook returns
  `Reconcile the canonical continuation owner before ending this turn: binding-head-changed` for every
  active `.agents/persistent-workflow-binding.json`, even when HEAD equals the bound head.
- Reproduced in `core/.worktrees/Docs-LanesHostSplitDebt` (PR #227). The artifact head and git HEAD were both
  `e4bbf8f213e8f61178e5cea64539a247cb6c8f79`; `binding_from_artifact` returned `head: None`.
- `completion.py:85` already reads `binding.get("head", binding.get("remote_head_sha"))`, which shows the
  intended mapping.
- Impact: a false Stop block on every delivery the agent owns. It misleads agents into reconciling
  correct state. P1, because it fires on every owned PR.

## Authorization

Standing authorization (`engineering:session-guidance`, standards-defect default) covers this repository:
fix, test, open the PR and merge once core's gates pass. Installing into other scopes, publishing outside
this repository, and destructive operations stay gated.

## Checkout

- Worktree: `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-ContinuationStopBindingHead`
- Branch: `Fix/ContinuationStopBindingHead`, from `origin/main`. The only writer is the successor.

## Completion

- `binding_active` compares the binding's `remote_head_sha`, or uses the same alias mapping as
  `binding_from_artifact`, so a matching HEAD passes and a different HEAD still reports
  `binding-head-changed`.
- `.agents/hooks/tests/test_continuation_stop.py` gains regression cases for:
  - a binding artifact whose `head` equals HEAD: no reconcile message;
  - one whose `head` differs: `binding-head-changed`.
- Core's repository gates pass, the PR is reviewed, and it is merged under the repository's delivery policy.
- Record the outcome under Progress.

## Next Steps

1. Push `2173ae7`, open the focused PR, and drive its CI and merge under the repository delivery policy.

## Progress

- 2026-10-12: created and handed off (lane L4: a specified fix with a focused test).
- 2026-10-12: successor acknowledged the handoff in `C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-ContinuationStopBindingHead` on `Fix/ContinuationStopBindingHead`; selected L4 for the specified, focused repair. First action: inspect the hook and its regression tests before implementing the alias-safe comparison.
- 2026-10-12: `binding_active` now compares the normalized binding's `remote_head_sha`; regression coverage proves an artifact `head` matching HEAD remains active and a differing head still raises `binding-head-changed`. `python -B -m unittest discover -s .agents\hooks\tests -p 'test_*.py' -q` passed with the test process's external Git ignore override. Committed as `2173ae7`; the local review at `reviews\Fix-ContinuationStopBindingHead.md` approved the frozen `c91b60c..2173ae7` range with no findings. Next: push the candidate and open its PR.
- 2026-10-12: delivery wake re-read PR #230 at the bound `2173ae76ab0fd1e042ae0f414c95dc1f67ff5fcb`. GitHub reports the PR open but `mergeable=false` and `mergeable_state=dirty`; `main` is now `4090e7d238754b3f1a37cd297142a698129cd3c8`, 16 commits ahead of the review base. The authorized scope forbids conflict edits, so delivery is blocked for an authorized source owner to reconcile the base, then validate, review, rebind, and merge the repaired head.
