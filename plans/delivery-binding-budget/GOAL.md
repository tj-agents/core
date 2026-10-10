# Bind delivery ownership within the existing command budget

## Outcome and authority

Repair the shared delivery binder's redundant process startup and its weak hold-label test oracle. Keep the existing ten-second deadline, current review/check gates, policy authority and both-host behavior. Standing engineering:session-guidance authorizes this bounded source repair through tested, reviewed, normally merged publication. The user requires all agent fixes to cover Claude and Codex. Parent retains the whole tj-agents rollout; this successor owns only this side source workstream.

## Ownership

Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DeliveryBindingBudget
Branch: Fix/DeliveryBindingBudget
Base: 8b656fb197771916c58aea4418934aaa7648b1c0

Own only .agents/workflows/workflow_ops.py, .agents/hooks/tests/test_workflow_ops.py, .agents/hooks/tests/test_delivery_binding_gate.py and this goal. Generated output is refreshed for checks and left unstaged per Core. Do not edit binding-hook source, hook_runtime, continuation_runtime, Stop, configuration/preference/permission/validator behavior, manifests or any other checkout. Expected source/test changes250-450 plus this goal; measure the actual complete authored slice against main and stop for parent split assessment before exceeding1000 substantive lines.

Live Feature/ConfigurableAutoMerge owns its atomic preference/guard/validator layer at a41bdace. Exact c73d33b..a41 hunk inspection proves the generic root/common/state/run/telemetry/origin lookups and existing Windows fixture/hold method are unchanged. Compose only these disjoint generic regions in this separate checkout; retain its prospective auto_merge binding field and readiness dispatch. Never copy its files over main or infer release from lease age. Core184 source is merged8582a40; its owner still owns causal CI/cleanup. Heartbeat repair and paused extractor preparation have distinct owners. Do not contact or adopt them.

## Reproduced cause

An authenticated unchanged-method trace captured delivery-bind exceeding10.055s during mock gh pr view before atomic binding write. Same missing-binding error reproduced on exact base; new launcher parsing is not reached by this string payload. Existing test discarded hook result, and a timeout after writing binding still passed its artifact assertion. Five Git plus two GH launches occur inside the binder: separate root/common setup, origin twice, then another common lookup for telemetry. Passing binder had only0.428s margin. No harmless-flake classification or timeout increase is justified.

Original evidence SHA is `f467bc5d79d34a929b7c7f8e3da0e371b96bc812777881115d223977d942eda9`. Prior WinError32 lock owner is unproven. Owned-tree timeout drainage is a separate follow-on, outside this lease.

## Accepted implementation

Construct a private invocation-local immutable Git context for delivery-bind only: one git rev-parse --path-format=absolute --show-toplevel --git-common-dir yields exactly two nonempty absolute records, resolved and validated. Keep existing public root/common helpers and other dispatch behavior. No external context/authority flag, module-global cache, stale binding repo or caller-supplied root shortcut.

Thread optional context through existing state_root/run_root/append_event/delivery_bind, defaulting to old independent resolution. Require matching resolved root. Reuse its common directory while retaining initial and telemetry run-id/traversal/redirect/containment checks; do not cache a prevalidated final run path. Derive origin once inside each delivery_bind and consume it in a private paginated-path helper and scoped/binding identity. Public changed_paths retains its current signature and fresh origin derivation. Retain fresh PR body/head/branch/state/labels, complete changedFiles/path validation, current policy/scoped approval/review and all Core183 authorized-stop-class behavior. Five Git launches become two; both GH reads remain.

Use exact cmd built-in first/second operand dispatch in the Windows GH fixture, avoiding echo/findstr nested pipelines. api plus --paginate returns the same complete diff; pr plus view returns summary; unsupported shapes fail. Keep Linux behavior equivalent. Strengthen original hold method: require returncode2 AND 'now has a delivery owner' stderr AND human-gate/ABSENT reason before retaining existing binding-absence-authority assertion. Code2 alone also means failure and is insufficient. No binder mock, skipped assertions or inflated budget.

## Implemented source mechanism

This execution record is self-contained. The private context and same-target consumer are authored in [`.agents/workflows/workflow_ops.py`](../../.agents/workflows/workflow_ops.py); the fresh-origin regression is in [`.agents/hooks/tests/test_delivery_binding_gate.py`](../../.agents/hooks/tests/test_delivery_binding_gate.py). They do not depend on a disposable design artifact or another checkout.

The private context remains invocation-local and immutable:

```python
@dataclass(frozen=True)
class _DeliveryBindContext:
    root: Path
    common_git_directory: Path


def _delivery_bind_context(start):
    completed = run_process(
        [
            "git",
            "rev-parse",
            "--path-format=absolute",
            "--show-toplevel",
            "--git-common-dir",
        ],
        start,
    )
    records = completed.stdout.splitlines()
    if len(records) != 2 or any(not record.strip() for record in records):
        raise WorkflowOperationError("git did not return the delivery binding repository context")
    root, common = (Path(record) for record in records)
    if not root.is_absolute() or not common.is_absolute():
        raise WorkflowOperationError("git returned a non-absolute delivery binding repository context")
    root = root.resolve()
    common = common.resolve()
    if not root.is_dir() or not common.is_dir():
        raise WorkflowOperationError("git returned an unusable delivery binding repository context")
    return _DeliveryBindContext(root, common)
```

BB01 captures the origin before the summary and passes that exact captured value to both authoritative consumers:

```python
def delivery_bind(root, workflow_run_id, pr, completion_condition, handoff, approval_record=None,
                  context=None):
    _matching_delivery_bind_context(root, context)
    repository = repository_slug(root)
    value = pull_request_state(root, pr, repository)
    validation = validate_pr_body(value.get("body"))
    if not validation["valid"]:
        raise WorkflowOperationError("; ".join(validation["errors"]))
```

```python
    reported = [str(item.get("path")) for item in value.get("files") or [] if item.get("path")]
    changed = _changed_paths_for_repository(root, repository, number, reported, value.get("changedFiles"))
    labels = [str(item.get("name")) for item in value.get("labels") or [] if item.get("name")]
    approval = scoped_approval(root, repository, number, branch, approval_record)
```

[`AGENTS.md`](../../AGENTS.md) makes `.agents/` the canonical authored source and requires generated plugin output to remain uncommitted. [`CODE_CONVENTIONS.md`](../../CODE_CONVENTIONS.md) requires cross-platform Python standard-library runtime code and argument-list subprocesses. [`PACKAGING.md`](../../PACKAGING.md) requires package generation and harness-manifest checks; generated output validates this source but is not part of this candidate commit.

## Next Steps

Scope: this bounded source defect through verified publication and own safe cleanup.
Current slice: BB01 serial source correction after parent review at `98658d9672fceb2c9cbfc347f8b4fa78147f4e36` requested changes.
Remaining scope: parent-owned fresh incremental review, exact CI, normal merge, causal generated publication and cleanup after this corrected candidate releases.
Done when: truthful real subprocess hold fixture binds an owner within unchanged10s and preserves absent authority for a hold; context cannot redirect state or reuse stale permission; source review/CI/publication pass. Source delivery does not prove normal-profile activation or complete the parent rollout.

## BB01 qualification and release boundary

`test_workflow_ops.py` passed 90 tests during the prior candidate qualification. BB01 changes only the existing delivery-bind summary call to pass its already-captured repository; its focused regression and the complete `test_delivery_binding_gate.py` suite passed 35 tests in 53.789 seconds. The gate suite covers the shared Claude and Codex payload paths and the truthful hold-label subprocess. The unchanged ten-second budget remains in force.

The parent synchronized the source candidate to `eeb369732b34334be41fd602dadcd186ba565c19` before the reviewed head `98658d9672fceb2c9cbfc347f8b4fa78147f4e36`; the source/test diff from `8b656fb197771916c58aea4418934aaa7648b1c0` to that synchronized base was empty. Core184 is already causally published and its checkout retired. This collaboration writer now prepares only the corrected local source commit; the parent resumes fresh incremental review, delivery, publication, and cleanup after release.

1. Before edits, acknowledge pickup here with exact native session identity. Read Core AGENTS/CODE_CONVENTIONS and installed bugfix/lanes/persistent-workflow. Ordinary exec setup currently fails before launch; use sandbox_permissions=require_escalated,login=false. If that supported execution path is unavailable, explicitly record failed-before-edits/no-claim and the precise gate; do not ask the user to retry or leave parent ownership ambiguous.
2. Implement only accepted regions; meaningful tests cover real linked-worktree/spaces/non-ASCII Git context, malformed/mismatched context, initial and telemetry containment/redirect revalidation, fresh policy/origin/head/labels across invocations and truthful held-label actual subprocess. Keep all affected existing scoped-authority checks. Capture measured actual binder duration/headroom with existing deadline, not count-only success. Reconcile any current-main delta; no blind replacement or broad base sync.
3. Run affected focused suites and actual repository generation/harness/package checks. Diagnose every failure causally, no timeouts/check weakening. Record actual both-host source verification here, run real plan-host check, measure all authored files and commit stable source. Leave generated output unstaged.
4. Release the corrected local commit to the parent with the focused regression, full gate suite, generated-check evidence, actual diff measurement, and limits. The parent owns fresh incremental review, delivery, publication, and cleanup.
5. Core184 is already causally published and its checkout is retired. This source candidate does not claim installed activation, PR creation, review approval, CI completion, merge, publication, or cleanup.

## Host coverage

```agent-host-coverage
{"schema_version":1,"shared_source":".agents/workflows/workflow_ops.py","hosts":[{"host":"claude","behavior":"Bind delivery ownership within the unchanged deadline with fresh authority and retained state-path checks.","source":".agents/workflows/workflow_ops.py","mapping":"Shared workflow runtime consumed by Claude delivery_binding_gate through engineering harness sources.","verification":{"level":"source","result":"passed","evidence":"test_delivery_binding_gate.py: 35 passed, including Claude payload coverage and truthful hold binding; measured direct binder: 1.711s of 10s."}},{"host":"codex","behavior":"Bind delivery ownership within the unchanged deadline with fresh authority and retained state-path checks.","source":".agents/workflows/workflow_ops.py","mapping":"Same canonical binder consumed by Codex delivery binding hook.","verification":{"level":"source","result":"passed","evidence":"test_delivery_binding_gate.py: 35 passed, including Codex payload coverage and truthful hold binding; measured direct binder: 1.711s of 10s."}}]}
```

## Verified failed-before-launch recovery

The parent invoked the supported native handoff launcher exactly once. It exited1 in sync_codex_standards: the base-agents marketplace clone exceeded its existing30s limit before launch_tab was called. No submission receipt or native successor exists. Read-only reconciliation finds only this untracked goal and no continuation owner or source edits. Do not retry the native launch or bypass hook trust.

Parent recovers the unclaimed implementation through one bounded L4 collaboration worker implement_delivery_binding_budget. It is the sole source writer for the three accepted runtime/test paths and this goal until stable candidate release. Implement and qualify the accepted design, commit authored source and release to parent before review/push/PR/merge. Parent owns independent frozen review, exact-head delivery, causal publication and cleanup; the overall rollout stays foreground-owned. Use require_escalated/login=false for every exec_command, because normal setup fails before command launch. You are not alone: preserve all other owner edits and do not revert or copy another checkout. Record every failing test causally; isolated reruns alone do not establish provenance.

## Implementation pickup

`/root/implement_delivery_binding_budget` claimed the sole bounded collaboration-writer lease within parent native Codex session `01a122c4-e884-7402-a873-9fa7449e5c37` on 2026-10-10; it created no continuation owner. The worktree was on `Fix/DeliveryBindingBudget` with only this untracked goal directory before the claim; no accepted source path had local edits.

## BB01 correction pickup

`/root/implement_delivery_binding_budget` renewed the sole bounded collaboration-writer lease within the same parent native Codex session on 2026-10-10 to resolve frozen finding BB01 from `reviews/Fix-DeliveryBindingBudget.md`. This is a serial correction, not an independent native session or continuation owner. The parent retains the work order, review, delivery, publication, and cleanup; this writer owns only `.agents/workflows/workflow_ops.py`, `.agents/hooks/tests/test_delivery_binding_gate.py`, and this goal until its corrected stable commit is released.
