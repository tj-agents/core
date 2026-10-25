# Diagnose sandbox setup read failure

## Authority

Tommy explicitly requested a separate handoff on 2026-10-10 to determine why sandboxed reads of a known text file and repository skill files are recorded as `exit -1` before the requested command runs.

Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SandboxSetupReadFailure`
Branch: `Fix/SandboxSetupReadFailure`
Investigation lane: L3, because the execution-host failure source was unresolved. Resolved from the
installed engineering package's `.agents/lanes/codex.json`: `gpt-6.1-sol`, high reasoning effort.

## Outcome

Restore ordinary sandboxed execution through the supported normal CLI launch path, so a fresh worker can
read its goal, a canonical skill and a text prompt and continue its task. Preserve sandbox settings, ACLs,
hook trust and live peers. The earlier isolated-runtime verification is useful evidence, but it does not
establish adoption by ordinary launches. The renewed 2026-10-11 request prioritizes this as a P1 capability
blocker and explicitly requests one native handoff before the broader orchestration work.

## Scope

Reconcile the already proven upstream runtime repair with current ordinary-launch selection and recover
the supported path. Reuse completed diagnosis and installed runtime evidence. Source changes are within
scope when they causally repair core's runtime selection/recovery; include required tests, catalog and
manifest companions, focused review and delivery under the repository's standing authority. Reconcile
the preserved Fix/CodexPreflightRecovery work before editing overlapping preflight paths. Do not implement
orchestration, lane redesign, unrelated cleanup or a new self-improvement system in this repair.

The prior approval installed a side-by-side runtime, preserving global PATH and profile selection. Do not
invent authorization for a different installation or bypass. If restoring the ordinary path requires a
separate machine/profile approval, first prepare the exact reversible change and its validation, record
the real remaining gate, and continue independent source repair. Do not ask again for already approved
installation/use of the isolated candidate or routine in-scope source edits. No sandbox/hook bypass.

## Next Steps

Pickup acknowledged on 2026-10-11 by session `01a12b23-e6a0-7c53-b069-3b2267bd12d1`,
through `normal-launch-recovery-handoff.txt`, from this exact checkout and branch. This session is the
sole repair writer. `CODEX_VERSION` and `codex --version` both report `0.163.0-alpha.1`; command lookup
selects the approved isolated runtime. Ordinary sandboxed reads of this goal, the canonical
`.agents/engineering/workflow/plan-execution/SKILL.md` and the original sibling-checkout text prompt
all exited 0. Matching refresh records name the isolated fixed helper and report `errors=[]`.

Current phase: L5 final documentation reconciliation, followed by L4 documentation review and
L7 delivery. These are bounded follow-ups; no model switch is claimed. Tommy explicitly authorizes
committing, publishing and merging this branch without further permission. Tommy subsequently
authorized MISTAKES.md now; it and its README link are written. A dedicated recording skill and
handoff-policy implementation remain deferred.

PR: not opened
Delivery slice: this existing branch, against main, containing only the recovery record and deferred
workflow debt. No core runtime code changed; the applied runtime/profile/catalog repair is local
machine state outside Git. Exclude all untracked machine-specific scripts, logs and JSON from the PR.

The previously failing scoped Git operation now passed in this same conversation. `git add` and
`git commit` ran through normal automatic approval review with exit 0, producing checkpoint
`5df3d81` (tool chunk `f3b519`). No approval, sandbox or hook control was changed. The cause of the
old/fresh-host difference is not established; retained loaded configuration remains a hypothesis.
The approval-review HTTP 400 recurred during final review and blocked scoped native-review and
GitHub CLI actions before execution. A documentation patch reported the same error: inspection
confirmed the handoff pointer changed, while this goal's larger correction did not. The successful
Git checkpoint proves that operation passed, not recovery of every later action in this running host.

Next actions: finish the remaining documentation corrections, checkpoint them, review the delta
from b6830f90c0e2320b0d375ea4d824c49b849bab0e, publish with plain Git/gh, then
merge this documentation-only slice under `engineering:merge-docs` once its gates pass. Remain the
foreground owner through delivery; initialize supported continuation if a delayed external result
requires it. Report the actual PR and merge SHA. GitHub confirms configurable auto-merge PR #188
is already merged and main declares `auto_merge: true`.

## Approval-review P1 clarification (2026-10-11)

The observed failure is the automatic review API rejecting
`input[1].internal_chat_message_metadata_passthrough.content_item_metadata`. Review fails before the
requested escalated process starts; Git therefore cannot write the external linked-worktree index.
The initial recovery catalog changed only the investigation model's Responses compatibility, while
the later normal-launch catalog covers the reviewer and other selected models. Fresh launch evidence
shows that a benign elevated action passed; a later scoped Git checkpoint also passed. These observations
do not establish completed GitHub delivery or recovery of every action in this running host.
A retained loaded configuration is a plausible explanation for the
host difference; a universal merge failure or CI-waiter defect is not established.

Retain the existing goal and merge authority. Remaining acceptance is corrected documentation,
incremental review, successful plain Git/gh publication and the authorized merge at the reviewed head.
Record actual approval and process results; do not substitute normal sandbox reads or bookkeeping for
that end-to-end delivery observation. No control bypass or separate standards project is authorized.

## Incident documentation (2026-10-11)

Tommy subsequently authorized the root `MISTAKES.md` incident record now, with a dedicated skill
deferred. Its seven entries identify the observed mistake, known cause, intended correction and
resolution condition. `docs/workflows/TECH_DEBT.md` links to that owner and retains the deferred
prevention work. The upstream sandbox runtime defect retains its existing machine debt owner;
exact repair and approval-review failure evidence remain in this goal.

Documentation phase: L5 tiny inline reconciliation; no new host, standards repair, recording system,
PR or scheduler is started. User authority remains intact and the existing execution gate is unchanged.

## Continuation recovery attempt (2026-10-11)

The earlier terminal report left delivery without an initialized continuation owner. This is recorded
in `MISTAKES.md` as M003, with prevention work in `docs/workflows/TECH_DEBT.md`.
The installed Codex `persistent-workflow` adapter and its shared `persistent-delivery` contract were
loaded. There is no PR or CI run to bind yet; the runtime supports initialization before a PR exists.

Actual installed `continuation_runtime.py init`, targeting this same canonical goal and the existing
commit/review/publish/merge authorization, returned exit 1: Permission denied writing the canonical
`.agents/continuation/owner.lock`. A normal scoped escalation then failed automatic approval review
before process launch with the same unsupported Responses metadata HTTP 400. No owner was initialized,
so foreground claim and scheduler registration were not attempted. No background waiter is running;
CI-waiter runtime behavior has not been tested or declared broken.

Blocked action: initialize and claim this goal's supported continuation, register its normal Windows
scheduler adapter with the verified fixed native executable, and observe a wake before yielding.
Resolver: a fresh normal host whose automatic reviewer can authorize the unchanged canonical state
write. Resume condition: successful initialization and foreground claim; then register, yield and
observe the actual wake. Preserve this goal, branch, merge authority and deferred standards scope.

## Status and next use

Delivery pending: normal-launch sandbox reads and the earlier scoped Git checkpoint passed;
automatic approval review subsequently reproduced the unsupported-metadata HTTP 400. Current
scoped Git inspection and GitHub CLI PR lookup both passed on 2026-10-11; no PR exists yet.
The frozen documentation review completed with three findings in
`reviews/Fix-SandboxSetupReadFailure.md`; all three corrections are now present locally.
Checkpoint, incremental review, PR publication and merge remain before the goal is terminal.
No continuation owner or wake is registered; this foreground owner is continuing delivery.

Verified phase: new ordinary PowerShell launches select the approved fixed runtime, and native
sandboxed reads plus the tested scoped elevated action pass. Historical completed phase: the approved isolated runtime
installation and fixed-runtime successor verification passed on 2026-10-11. Both original file reads
exited 0 and matching setup refreshes completed with errors=[].

Already running hosts keep their original executable. New PowerShell sessions use the repaired normal
profile and global catalog setting without invocation-specific runtime or catalog overrides. The
dependent-cleanup owner retains its separate goal and uses this ordinary entry point for its next
reopen; this repair does not kill or adopt that session. Registry PATH and the npm installation remain
unchanged. Profile selection now puts the approved side-by-side binary first in new PowerShell sessions.

The historical evidence below describes that earlier bounded verification. Its completion statements do
not supersede the renewed Outcome, Scope and Next Steps above.

## Host coverage

This documentation slice records Codex Windows runtime recovery and shared workflow debt. It changes
neither shared capability definitions nor host adapters. Deferred workflow-policy repair must assess
both hosts through .agents shared source and the appropriate .codex/.claude adapters.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": "plans/sandbox-setup-read-failure/GOAL.md and the upstream Codex sandbox/Responses client",
  "hosts": [
    {
      "host": "claude",
      "behavior": "The observed failures are in Codex; Claude runtime acceptance was not performed.",
      "source": ".agents owns the shared workflow debt; no Claude runtime source defect was established.",
      "mapping": ".claude adapters remain mapped to canonical .agents definitions; this slice changes only recovery records.",
      "verification": {"level": "source", "result": "limited", "evidence": "The frozen candidate changes only documentation and recovery-plan artifacts; no Claude executable or adapter changed."},
      "exception": {"constraint_evidence": "Reproductions name the Codex Windows sandbox helper and Responses metadata, with no equivalent Claude reproduction.", "supported_other_host_outcome": "Codex normal-launch sandbox reads passed; repository delivery is still limited by automatic approval review."}
    },
    {
      "host": "codex",
      "behavior": "Approved normal runtime/catalog selection restores sandbox reads; approval-review delivery acceptance remains incomplete.",
      "source": "Machine-local Codex 0.163.0-alpha.1 and normal-launch-models.json, outside Git.",
      "mapping": "Normal PowerShell profiles and global .codex/config.toml select the approved candidate; repository .codex adapters are unchanged.",
      "verification": {"level": "installed", "result": "limited", "evidence": "Verifier 01a12b41-5760-76e0-b2aa-9245ecfaf273 observed three exit-0 reads and errors=[]; checkpoint 5df3d81 passed; later escalations failed with the metadata HTTP 400."},
      "exception": {"constraint_evidence": "The current running host rejected native-review, GitHub CLI and goal-patch actions through automatic review; successful PR delivery was not observed.", "supported_other_host_outcome": "Claude source ownership is preserved; no Claude installed acceptance or equivalent failure is claimed."}
    }
  ]
}
```

## Prepared normal-launch activation (2026-10-11)

The change below is now approved and applied. Task-local preview exited 0 after validating every
original hash, preserving all other TOML settings and preparing ten catalog entries. Scoped normal
escalation then ran `activate_normal_launch.py --home C:/Users/TommySeery --apply` with exit 0.
The exact backup is
`C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/repair-evidence/normal-launch-activation-20261011T135434290168Z`.
Config still declares `approval_policy="on-request"`, `approvals_reviewer="auto_review"` and
`sandbox_mode="workspace-write"`. No review, sandbox or hook control was disabled. The new normal
catalog exists; the old invocation catalog remains intact. Fresh native validation is active.
`launch_normal_validation.ps1` ran in a new profile-loaded Windows PowerShell process after removing
the inherited fixed-runtime PATH entry. It verified the normal profile and application lookup select
the approved fixed executable. The installed packaged launcher completed its normal preflight and
exited 0, submitting exactly one native verifier on L3. Submission output is
`normal-launch-submission.log`; it is launch evidence, not acceptance yet.

Verification phase: L3, because fresh normal-profile selection and native approval-review acceptance
still require actual observation. One verifier may write only `normal-launch-verification.json`; this
parent remains sole repair/goal writer. The task-local launcher first strips inherited fixed-runtime
PATH selection, loads a real new PowerShell profile and verifies the normal terminal adapter, then
invokes the installed packaged handoff launcher once. No second tab is permitted after submission.

The installed machine 2.1.16 `resources/machine/scripts/agent_cli.py` discovers native PATH entries,
npm payloads beside the PATH shim and Windows desktop caches. It does not scan the isolated runtime
directory. Its current resolver selects the fixed runtime because this successor's invocation PATH
already includes its `bin` directory. Today's ordinary-launch setup records at 14:23:39, 14:23:45 and
14:24:05 local instead name the npm helper below `AppData/Local/nvm/v20.19.5`. That package is not
readable from this sandbox, so its version was not freshly re-probed; historical 0.162.0 evidence is
preserved above. No new causal core source defect is established. The independent preflight-recovery
goal and existing runtime-health debt retain their source ownership.

The saved global model and automatic approval reviewer both have `use_responses_lite=true` in the
installed invocation catalog; only the investigation model and one older model have it false. Automatic
approval review reproduced HTTP 400 for `internal_chat_message_metadata_passthrough.content_item_metadata`.
Turning off unsupported Responses metadata must cover the reviewer as well as normal model selection;
automatic review itself remains enabled. Compatibility for those additional models is proposed, not yet
verified. The tool reported an approval-review failure on acknowledgement edits, but a subsequent Git
diff independently proves the edits were written; neither successful approval nor a rollback is claimed.

Exact activation, subject to Tommy's approval:

1. Preserve byte-for-byte backups of both profiles and `.codex/config.toml`. Recheck their hashes below;
   if another owner changes them, reconcile the delta before applying anything.
2. Immediately before the existing base-agents Codex launcher block at line 157 in both
   `C:/Users/TommySeery/Documents/PowerShell/Microsoft.PowerShell_profile.ps1` and
   `C:/Users/TommySeery/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1`, insert:

   ```powershell
   $env:Path = 'C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/bin;' + $env:Path
   ```

   This affects new PowerShell process environments and preserves the installed normal launcher.
   The registry PATH and existing processes are not edited. Profile inspection found no existing
   assignment to `$env:Path` in either file.
3. Create `C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/normal-launch-models.json`
   from the existing `responses-compatible-models.json`: preserve every field and model entry, changing
   only each entry's `use_responses_lite` to `false`. Write UTF-8 JSON. Do not overwrite an unexpected
   existing target. The previously approved invocation catalog remains intact.
4. Add this top-level setting to `C:/Users/TommySeery/.codex/config.toml`, before any TOML table:

   ```toml
   model_catalog_json = "C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/normal-launch-models.json"
   ```

   Preserve the chosen model, effort, approval reviewer, sandbox and all other settings.
5. In one new PowerShell session with its normal profile, verify application lookup and the installed
   resolver both select the fixed native runtime. Launch one native worker through the packaged normal
   handoff launcher with its real plugin-refresh and hook-trust preflight. The verifier owns no repair
   writes. Observe its actual default-sandbox command exits for this goal, the canonical skill and the
   original text prompt, plus matching fixed-helper `errors=[]` records. It must also complete a benign
   review-requiring action under `auto_review` in a disposable directory; shell reads alone do not prove
   this additional compatibility repair. Verify the configured default model can start as well.
6. After success, record normal adoption and the worker's next action here. On failure, restore the
   exact profile/config backups and remove only the newly created catalog, retaining the evidence.
   Keep the repair open with the actual next action; never disable or bypass review, sandbox or trust.

Pre-change SHA-256 snapshots:

| File | SHA-256 |
|---|---|
| PowerShell profile | `9db2eff35f03bdbe6c3cc965797379a7d82a2f45db31fdc2821b61ed7663e40e` |
| WindowsPowerShell profile | `f787b9561618515dc6b94e2bf9afb893ce6856e47c592bdc45e0bb897f724130` |
| Codex config | `bb9685fe9fdc002e5dab711823e9f4a8b242c3cd86d518ece508922e3064368c` |
| Existing invocation catalog | `c155e273fe97a8cd2fa24bac75482a264fdab658d7061d770aeebdaf2a114620` |

Approved action: activate default fixed-runtime selection and broaden model/reviewer compatibility.
Execution gate resolved: machine writes passed normal scoped escalation. The fresh native automatic
review action also exited 0 with the unchanged reviewer. Earlier HTTP 400 and permission errors remain
historical evidence; no permission or review bypass was used.

Read-only peer inspection found this successor and the renewed dependent-cleanup worker live, with all
prior sandbox-repair and preflight-recovery sessions stopped. Three shared node runtime processes remain
active. No peer was stopped by this repair. The preflight-recovery checkout is preserved and clean.
No repository runtime code changed; source tests and a code PR would not establish machine adoption.

## Normal-launch completion (2026-10-11)

Native verifier `01a12b41-5760-76e0-b2aa-9245ecfaf273`, launched once through the packaged normal
launcher after a fresh PowerShell profile, reports `0.163.0-alpha.1`. All required ordinary sandboxed
reads exited 0: this goal (chunk `ca794e`), the canonical plan-execution skill (chunk `8fc1ec`) and the
original dependent-cleanup text prompt (chunk `21d520`). Its benign scoped elevated read passed the
automatic reviewer with exit 0 (chunk `67f503`), with `approval_policy=on-request`,
`approvals_reviewer=auto_review` and `sandbox_mode=workspace-write` unchanged.

The matching setup interval is 2026-10-11T13:58:15.179Z through 13:58:20.297Z. Helper records name the
approved isolated `codex-windows-sandbox-setup.exe`; refresh results contain `errors=[]`. Concurrent
commands share the log window, so their individual tool exits establish each read result. Four shared
node runtime processes remained active across the verifier's two observations; it issued no process
control action. Its recorded evidence has `verified=true` and `failures=[]`.

A separate normal-profile configured-default-model probe started native thread
`01a12b43-3ab9-72f0-ae40-1121482bd56e`, returned exactly `DEFAULT_MODEL_READY` and exited 0. No model,
catalog, approval or sandbox override was passed to that probe. The investigation model, configured
default model and automatic reviewer are actually verified; availability of every other model is not
claimed merely because the catalog has ten entries.

Persistent acceptance evidence and task-local tooling are archived at
`C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/repair-evidence/normal-launch-adoption-20261011T135434Z`.
That directory owns `normal-launch-verification.json`, `normal-launch-submission.log`,
`default-model-probe.log` and `default-model-response.txt`. Machine-specific state stays outside Git.
The separate activation backup above supplies exact rollback bytes. Do not rerun the original
activation script on changed files; its hashes intentionally fail after activation.

GitHub directly confirms PR #188 is merged at `8a2c87945c3665ba68ca012e1d045e42a22db1ec`; the remote
default declaration enables `auto_merge: true` under green required checks and independent review.
This older evidence checkout lacks the new declaration field. No source repair PR was created for
machine activation, and no further merge permission was requested after Tommy's instruction.

Acceptance review: reconcile the independent native evidence, normal-launch log, default-model probe,
preserved settings and actual approved machine edits. All renewed acceptance criteria pass. The
pre-existing core preflight-recovery goal and runtime-health debt retain their own resolution
conditions; their broader source work was neither duplicated nor claimed complete here.

Terminal cleanup observation: the completed verifier's canonical peer close refused
`Windows Terminal target is absent or ambiguous`. Actual-tab inventory returned only registry rows
with `actual=false`, including both this parent and that verifier. No process was killed to bypass the
refusal. Terminal cleanup requires the machine host to expose a uniquely matched actual attachment;
its observable resume condition is a verified actual tab for the recorded session. The recovery
acceptance and evidence are complete independently of this terminal-UI limitation. This checkout is
retained as the durable goal owner; no worktree cleanup or deletion is authorized by the machine fix.

Checkpoint observation: this already-running parent's automatic reviewer still rejects unsupported
Responses metadata. The fresh normal-launch reviewer passed; existing hosts retain their original
loaded model catalog until reopening. The exact two-file Git checkpoint was not executed: automatic approval review rejected its payload
before process launch. A captured normal PowerShell child was prevented by this sandbox's script
execution policy; a captured native child could not resolve its home under the sandbox identity.
Neither child started a worker or changed approval controls. These local checkpoint attempts do not
invalidate the successful fresh normal-host acceptance. Resolver: reopen through the repaired ordinary
profile; resume condition: that host's automatic reviewer accepts the unchanged two-file checkpoint.
No further task or independent terminal is launched under Tommy's explicit scope restriction.

## Deferred handoff mistake (2026-10-11)

Tommy explicitly limited this session to completing the blocking sandbox repair and recording the
unnecessary verifier handoff as debt. No standards repair, successor or MISTAKES.md system is started.
The owning entry is `docs/workflows/TECH_DEBT.md`, under "Same-goal verification was launched as a
handoff". It records the captured-child/subagent alternative and an objective resolution condition.
Phase: L5 small documentation reconciliation, followed by L7 local checkpoint; tiny inline follow-ups.

## Cause and owner

Codex CLI 0.162.0's Windows sandbox setup attempts to open a running computer-use runtime executable
with `MAXIMUM_ALLOWED` during a root-only ACL repair. Windows rejects that access with
`ERROR_SHARING_VIOLATION` (32). Setup exits with status 1 before the requested PowerShell process starts;
the host reports `helper_unknown_error: setup refresh had errors`. A recorded `exit -1` is therefore a
process-launch failure, not a `Get-Content` exit status.

The failing binary is OpenAI's `codex-windows-sandbox-setup.exe`, shipped with the installed npm
`@openai/codex` runtime. The source owner is `openai/codex`, specifically
`codex-rs/windows-sandbox-rs/src/acl.rs`, function `ensure_allow_mask_aces_with_inheritance_impl`.
No core source defect was established. The existing machine debt entry
[A locked Codex runtime executable can disable every sandboxed command](../../.agents/machine/TECH_DEBT.md#a-locked-codex-runtime-executable-can-disable-every-sandboxed-command)
already owns the local dependency on host recovery support.

## Local evidence

- Native executable `C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe --version`
  returned `codex-cli 0.162.0`; the npm package manifest also reports `0.162.0`.
- Sandboxed `Get-Content -LiteralPath '.agents/continuation/sandbox-setup-read-failure-prompt.txt'`
  failed before process creation. The same command with scoped `require_escalated` execution exited 0.
- A second sandboxed reproduction,
  `Get-Content -Raw -LiteralPath 'plans/sandbox-setup-read-failure/GOAL.md'`, failed at the same
  process-creation gate. Its elevated equivalent exited 0 and returned the goal contents.
- `C:/Users/TommySeery/.codex/.sandbox/setup_error.json` contains
  `{"code":"helper_unknown_error","message":"setup refresh had errors"}`.
- `C:/Users/TommySeery/.codex/.sandbox/sandbox.2026-10-10.log` records the prompt-read attempt at
  16:09:44 local / 15:09:44 UTC, setup spawning at 16:09:44.736, the runtime failure at
  15:09:45.020205700 UTC, and helper exit status 1 at 16:09:45.935 local.
- The exact fatal message names
  `C:/Users/TommySeery/AppData/Local/OpenAI/Codex/runtimes/cua_node/426e88130fe66c7e/bin/node_repl.exe`:
  `runtime read/execute validation failed ... open ACL target for root-only update ... (os error 32)`.
  The earlier user-profile read-attributes warning explicitly continues setup; the runtime validation
  failure is the error that causes the helper to exit. Read-ACL-only work completes separately.
- A process snapshot found 29 `node_repl.exe` processes executing that exact runtime path. Their
  immediate parents were `codex.exe` processes from installed OpenAI runtimes. This identifies an active
  shared runtime, not one orphan process that can safely be terminated without affecting other sessions.
- A non-mutating `CreateFileW` probe on that executable used `OPEN_EXISTING`,
  `FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE`, and `FILE_FLAG_BACKUP_SEMANTICS`.
  `MAXIMUM_ALLOWED` failed with error 32; `READ_CONTROL | WRITE_DAC` succeeded. Every successful
  handle was closed. No ACL or file content was changed. A separate probe also found read access
  succeeds and generic read/write access fails with error 32.
- Available SessionStart hook output delivered the standards normally. The fatal log path is in the
  execution host's setup helper, not in a core or installed-plugin hook.

## Upstream repair and release boundary

[OpenAI PR #51822](https://github.com/openai/codex/pull/51822) merged on 2026-10-07. It restricts
`MAXIMUM_ALLOWED` opens to directories and requests `READ_CONTROL | WRITE_DAC` for files only when
repair is needed, preserving sandbox permissions and denials. Its Windows regression test keeps the
runtime executable open during repair and revalidation.

Source inspection on 2026-10-10 confirms the defective unconditional root-only open in
[0.162.0](https://github.com/openai/codex/blob/rust-v0.162.0/codex-rs/windows-sandbox-rs/src/acl.rs#L528)
and [0.162.1](https://github.com/openai/codex/blob/rust-v0.162.1/codex-rs/windows-sandbox-rs/src/acl.rs#L528).
The directory check exists in
[0.163.0-alpha.1](https://github.com/openai/codex/blob/rust-v0.163.0-alpha.1/codex-rs/windows-sandbox-rs/src/acl.rs#L530).
These are content checks; a higher version or newer release date alone does not prove inclusion.

## Recovery boundary

Tommy approved the isolated official candidate installation with "yeah go?" on 2026-10-11. Installation and actual fresh-host acceptance are complete. No installation approval remains pending. Existing hosts cannot hot-swap their running binary; their next session must explicitly select the installed runtime.

No sandbox settings, ACL policy, hook trust or existing runtime binaries were manually changed. No peer process was terminated by this repair.

## Renewed ownership and progress

Tommy explicitly renewed this same repair through `sandbox-repair-followup-prompt.txt` on 2026-10-10. Peer registry verification finds prior session `01a1265c-a31b-7431-a8b3-aa47101ff0c9` not live and current repair session `01a127ec-ae44-7353-95d7-436f4fccfd74` live in this checkout. The parent remains sole writer of `Fix-DependentPrBranchCleanup`; this task neither edits that checkout nor adopts its goal.

Phase: L3 diagnosis and recovery preparation, using the canonical Codex lane resolution already recorded above. The existing investigation goal remains the progress owner.

- Ordinary `exec_command` still fails before PowerShell creation with `helper_unknown_error: setup refresh had errors`. Node REPL filesystem reads and native processes remain usable under their existing controls.
- A scoped elevated diagnostic was approved and exited 0; there was no automatic approval rejection. It confirms the active npm package and native executable still report `0.162.0`.
- The current host PID is `53192`, using the npm runtime. The matching setup logs name its `codex-resources/codex-windows-sandbox-setup.exe` and the locked shared `node_repl.exe`.
- The repository runtime resolver, run in the normal machine environment, selects `0.162.0`. Node REPL children intentionally lack `LOCALAPPDATA` and the Codex/npm PATH entries, so their empty candidate inventory does not establish a launcher defect.
- The desktop runtime checked directly reports `0.151.0-alpha.7.1`; it is below the launcher minimum and is not a verified fixed alternative.
- Official npm `latest` remains `0.162.1`. Direct source checks still find the unconditional file `MAXIMUM_ALLOWED` open there, and the directory-only guard in official `0.163.0-alpha.1`.

The installed candidate inventory is complete: npm `0.162.0`, desktop `0.148.0-alpha.21`, and desktop `0.151.0-alpha.7.1`. Both desktop candidates fall below the launcher minimum `0.154.0`. The same resolver implementation on current `origin/main` ranks these candidates by semantic version. No eligible installed fixed runtime exists; no causal core-owned launcher selection or recovery defect was established, so no runtime source or regression-test change was made. The existing machine debt entry continues to own future launcher health recovery.

## Prepared official candidate

- Release: [OpenAI Codex 0.163.0-alpha.1](https://github.com/openai/codex/releases/tag/rust-v0.163.0-alpha.1), a prerelease rather than stable.
- Platform package: `@openai/codex@0.163.0-alpha.1-win32-x64`, selected by the official top-level `@openai/codex@0.163.0-alpha.1` manifest.
- Archive: `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-sandbox-repair-sG4Nyj/codex-0.163.0-alpha.1-win32-x64.tgz`. All 47 regular-file/directory entries were staged before approval; the vendor runtime is now installed at the approved isolated path, without changing PATH.
- Archive SHA-256: `59486e550eba4ffe7bcaed01e5925c97fba59345a590896b884a72c85b9b62ac`.
- Registry SHA-512 integrity matched, and both npm registry ECDSA signatures verified against the registry key `SHA256:DhQ8wR5APBvFHLF/+Tc+AYvPOdTpcIDqOhxsBHRwC7U`.
- The published SLSA subject digest matches the same package bytes. Its DSSE signature verifies with the bundled certificate naming OpenAI's `rust-release.yml` workflow and `rust-v0.163.0-alpha.1` tag. Independent Sigstore certificate-chain/transparency-log verification was not performed; this is not claimed as complete Sigstore verification.
- Source commit: `cb36b210bcb28dba454289d9b1789351e40821fa`. The [immutable ACL source](https://raw.githubusercontent.com/openai/codex/cb36b210bcb28dba454289d9b1789351e40821fa/codex-rs/windows-sandbox-rs/src/acl.rs) contains both the directory-only `MAXIMUM_ALLOWED` guard and file-specific `READ_CONTROL | WRITE_DAC`. Source SHA-256: `2b4685cb4a3ed79e124c113b5ded7c4fcc6fd5456c7e44a73df145d0fd25c666`.
- Staged native CLI `--version` exited 0 with `codex-cli 0.163.0-alpha.1`, using an isolated temporary `CODEX_HOME` solely for that version probe.
- Native CLI SHA-256: `3ac95e7bbb5f51d9fcda76d013a04e22456bd67eafde88eb04feafd71590933f`. Setup helper SHA-256: `2e9d81d128494f8499d6de27cca354aa94dcd1a17314ed35f29c79c6ecd78932`.
- Full verification record: `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-sandbox-repair-sG4Nyj/verification.json`. Downloaded runtime payloads and machine-specific verification state remain outside Git.

## Approved machine action and recovery verification

The installation approval gate was resolved by Tommy's "yeah go?" on 2026-10-11.

The approved proposal selected a side-by-side installation at `C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1`; that path was absent before installation. Approval permits copying the complete authenticated vendor runtime there and using its native `bin/codex.exe` for a fresh repair verification session. The global npm runtime, desktop caches, existing PATH, sandbox configuration, ACL policy, hook trust and live peer processes remain preserved. Do not overwrite an unexpectedly existing target.

After approval, recheck archive/binary integrity, install the complete vendor payload at that exact path, verify `--version`, and select it for this repair using an invocation-scoped PATH and launcher minimum `0.163.0-alpha.1`. Perform any actual session transfer through the installed `engineering:handoff` workflow, with verified pickup and one writer; do not infer success from launcher submission. Preserve normal hook trust; do not use bypass or sandbox-disabling flags.

Acceptance requires a fresh fixed-runtime host to run ordinary `exec_command` with:

```powershell
Get-Content -Raw -LiteralPath 'plans/sandbox-setup-read-failure/GOAL.md'
```

It must exit 0 while the shared `node_repl.exe` processes remain active. Capture the matching setup-refresh log showing the fixed helper path and `errors=[]`, and verify that the parent and other peer sessions remain live. A standalone `codex sandbox` probe can provide supplementary evidence but does not replace success through the actual host command runner.

Approval, installation and fresh-host acceptance are complete under the existing sandbox settings.

The current foreground session remains sole writer. No unattended writer or wake has been registered. Recovery acceptance passed with observed ordinary command-runner success.


## Approved installation progress (2026-10-11)

Authority: Tommy's "yeah go?" approves the previously proposed side-by-side alpha installation and recovery test. This revokes the pending installation gate for the named candidate and path; it does not authorize replacing the global runtime, modifying desktop caches, changing global PATH, disabling sandboxing or bypassing hook trust.

Lane selection: installation is L5 (the archive, target and copy operation are already specified), performed as a small inline follow-up; recovery verification is L3 (actual host acceptance remains unresolved). Canonical lane resolution is unchanged. No in-session model switch is claimed.

The first ordinary shell read on resumption failed before process creation. The staged archive was rechecked and installed at the approved path; Git confirmed the same checkout and branch.

Installation evidence: `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-sandbox-repair-sG4Nyj/installation.json` records 45 vendor files installed at the approved exact path and verified byte-for-byte against the authenticated archive. The installed native binary `--version` returned `codex-cli 0.163.0-alpha.1` with exit 0. No existing runtime or global PATH was replaced.

The optional standalone `codex sandbox --cd ...` probe exited 2 before executing a command because this build requires an explicit permission profile or sandbox-state JSON; the saved user configuration uses legacy `sandbox_mode="workspace-write"`. No profile was invented and no sandbox control changed. The recovery test therefore proceeds through a fresh actual `codex exec` host using the unchanged saved configuration. The fresh child is read-only; it has no goal or repository writer ownership.

The first fresh fixed-runtime host started thread `01a12aa2-8990-73b0-97be-825c103620b1` but exited 1 before any tool execution: the Responses backend rejected `input[1].internal_chat_message_metadata_passthrough.content_item_metadata` (HTTP 400). No sandbox acceptance is claimed from that launch. Startup also logged upstream system-skill directory sharing/access errors; no local directory, ACL or trust was manually altered to address them.

Recovery diagnosis remains L3. Immutable upstream `client.rs` strips content-item metadata when `ModelInfo.use_responses_lite` is false. This account's selected model cache advertises it as true. Upstream exposes `model_catalog_json` as an authoritative process-local catalog using `StaticModelsManager`; it preserves auth filtering. A supported invocation-scoped catalog at `C:/Users/TOMMYS~1/AppData/Local/Temp/codex-sandbox-repair-sG4Nyj/responses-compatible-models.json` copies the existing catalog and changes only the selected model's `use_responses_lite` to false for ordinary Responses compatibility. Sandbox, approval, node tool review metadata, hooks, TLS, auth and global configuration are unchanged. The focused retest uses that official override and preserves original failed-launch evidence.

## Completed recovery acceptance (2026-10-11)

Fresh fixed-runtime thread `01a12aa5-e595-7542-934c-bad2fc45f33e` ran ordinary sandboxed PowerShell `Get-Content -Raw -LiteralPath 'plans/sandbox-setup-read-failure/GOAL.md'` with exit code 0. The native host also exited 0. The matching sandbox log records the installed `0.163.0-alpha.1/codex-resources/codex-windows-sandbox-setup.exe` and `setup refresh: processed 2 write roots (read roots delegated); errors=[]` at 2026-10-11T11:08:23.527575100 UTC.

The parent dependent-cleanup session and this repair session remained live; 20 pre-existing shared node runtime processes remained active. No process termination or restart was issued by the repair. Other peers can change independently, so unchanged status for every peer is not claimed.

The invocation-local compatibility catalog is saved at `C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/responses-compatible-models.json`. It changes only the selected model's Responses compatibility flag. Persistent verification, installation, acceptance summary and successful setup excerpt are in that runtime's `repair-evidence/` directory. The alpha's initial API-metadata failure was resolved for the tested invocation; global configuration remains unchanged.

From this checkout, open the fixed runtime with:

```powershell
$codexLane = (Get-Content -Raw -LiteralPath '.agents/lanes/codex.json' | ConvertFrom-Json).lanes.L3
& 'C:\Users\TommySeery\.local\share\codex\runtimes\0.163.0-alpha.1\bin\codex.exe' --model $codexLane.model --config ('model_reasoning_effort=' + $codexLane.reasoning_effort) --config 'model_catalog_json="C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/responses-compatible-models.json"' --cd 'C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-SandboxSetupReadFailure'
```

No core runtime source defect was established and no core code change was required. The approved installation and verification scope is complete. The originating repository session retains its own work and writer ownership.

## Historical session reopening blocker (2026-10-11; resolved)

The packaged launcher exited 1 before tab submission: marketplace refresh could not back up engineering@base-agents because Windows returned Access is denied (os error 5). No successor was submitted by that failed attempt. The predecessor retained this repair goal and writer ownership until the successful normal-preflight transfer below.

Automatic approval review rejected a proposed direct-native fallback because it would skip the failed packaged plugin-refresh and hook-trust preflight and that bypass was not specifically authorized. No alternate launch is permitted while that rejection stands. A direct-launch approval request was pending while the normal refresh failure was investigated. Normal preflight recovery subsequently resolved the launch gate; this verification used the normal launcher and required no direct-launch exception.

Blocked action: open a fixed-runtime successor through the normal launcher.
Resolver: plugin-cache recovery under existing safeguards, or Tommy explicitly authorizing the described direct launch.
Unblock action: successful normal preflight, or explicit direct-launch approval accepted by automatic review.
Resume condition: one native fixed-runtime tab is submitted, then its goal acknowledgement and both original file-type read results are observed.

## Normal preflight recovery

The full official `plugin marketplace upgrade --json` through the existing stable 0.162.0 native management CLI exited 0 with errors=[] and refreshed base-agents. No cache, ACL, hook or plugin configuration was manually bypassed. The prior packaged launcher attempt definitively failed before tab submission, so a single new attempt through the normal packaged launcher is authorized after this observed prerequisite recovery. The direct-native fallback remains unexecuted; no bypass of automatic review is used. Predecessor stops owned-path writes at packaged launcher invocation and observes pickup read-only.

## Fixed-runtime successor pickup (2026-10-11)

Session `01a12aec-7f71-7c73-aeaf-5fca3d754103` acknowledges the transfer through `fixed-runtime-handoff.txt` from this exact checkout and branch `Fix/SandboxSetupReadFailure`. The command runner reports `CODEX_VERSION=0.163.0-alpha.1`; ordinary sandboxed reads of the handoff and this goal exited 0. This successor became the sole writer of this goal. The sibling dependent-cleanup goal remains with its original owner.

Phase: L3 recovery verification, because actual execution on both original paths and matching setup-refresh evidence required host observation. The installed engineering package's `.agents/lanes/codex.json` resolves L3 to `gpt-6.1-sol` with high reasoning effort, matching this session's launch selection. No model switch is claimed.

## Original-path verification (2026-10-11)

Both commands ran through ordinary `exec_command` with its default sandbox permissions, without elevation or an alternate reader:

| Read | Actual exit code | Tool output |
|---|---|---|
| `Get-Content -Raw -LiteralPath 'C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-DependentPrBranchCleanup/plans/dependent-pr-branch-cleanup/sandbox-repair-followup-prompt.txt'` | 0 | Chunk `6729ac`; original prompt returned |
| `Get-Content -Raw -LiteralPath '.agents/engineering/workflow/plan-execution/SKILL.md'` | 0 | Chunk `b8e7fc`; complete canonical skill returned |

Matching evidence is in `C:/Users/TommySeery/.codex/.sandbox/sandbox.2026-10-11.log`. The command START records appear at 13:28:02.455 and 13:28:02.929 local (12:28:02 UTC). Their helper-spawn records at 13:28:03.109 and 13:28:03.720 local both name `C:/Users/TommySeery/.local/share/codex/runtimes/0.163.0-alpha.1/codex-resources/codex-windows-sandbox-setup.exe` and this exact checkout. The concurrent completion records have interleaved log text but contain both UTC timestamps, `2026-10-11T12:28:10.745911700+00:00` and `2026-10-11T12:28:10.745906500+00:00`, and two `setup refresh: processed 2 write roots (read roots delegated); errors=[]` results. Both subsequently select `codex-command-runner-0.163.0-alpha.1.exe` at 13:28:12.748 local. The command runner's independent exit results establish each read's success; the shared log does not provide a per-command identifier for ordering the simultaneous completions.

The same shared log also contains failures from the older npm helper in other sessions. Those records name the npm runtime and different setup invocations; they do not negate the fixed session's successful reads. Existing hosts still require reopening with the fixed runtime, as recorded above. Nonfatal profile ACL/visibility warnings continue without preventing these reads.

Read-only installed `agent:peer` verification returned live entries for the originating dependent-cleanup session `01a127b0-7047-7e30-af8c-c861898d7e5b` (PID 30996), the predecessor repair session `01a127ec-ae44-7353-95d7-436f4fccfd74` (PID 53192), and this successor (PID 49228). The predecessor remains an observer after writer transfer. Ordinary `Get-Process -Name node_repl` found 24 active shared runtime processes. No peer was stopped or restarted. No sandbox setting, hook trust, ACL policy, global runtime selection or sibling-checkout content was changed by this verification.

An optional sandboxed WMI process diagnostic was denied with `0x80041003`; it changed no controls or processes. Direct command-runner environment and installed peer inspection supplied runtime and liveness evidence. Incorrect guessed skill-file locations returned ordinary file-not-found errors; their actual adapter-linked canonical files were then read. These were diagnostic-command errors, not renewed sandbox setup failures.

Phase: L5 for the small evidence reconciliation, followed by L7 for the local Git checkpoint; both are tiny inline follow-ups under the lanes contract, with no claimed session model switch. The duplicate pickup block was consolidated into this single record. Review is a direct consistency check against observed command exits, log timestamps, live-peer evidence and the original authorization; no repository code was changed, so no code test suite or PR delivery is selected. The existing machine debt entry continues to own recovery support for older runtimes.

Outcome: the requested fixed-runtime host recovery and both original file-type reads are verified. The previous normal-launcher blocker is resolved by the successful normal-preflight launch and this observed pickup; no direct-launch bypass was used. Remaining action: local checkpoint and concise completion report. The checkout remains available as the durable evidence owner.
