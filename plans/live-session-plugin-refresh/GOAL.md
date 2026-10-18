# Keep long-running agent sessions aware of published plugin updates

## Authorization and ownership

Tommy requested a permanent repair on 18 October 2026 and explicitly chose Claude for this handoff.
This is an implementation handoff, including focused tests, independent review, required CI, source PR,
merge and causal package publication under Core's existing delivery authorization.
One successor and one local writer; parent codex:01a1415f-6448-7123-8b17-c7fb67aee637 retains the
separate concurrent-session-close repair, PR306. Do not adopt, close or rewrite that task.
Checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-LiveSessionPluginRefresh
Branch: Fix/LiveSessionPluginRefresh. Fetched baseline: dc1f7415ecb1aaf86d6ae4329d22f9ab34164ca6.
Work item: lifecycle/live-session-plugin-refresh. Source owner: tj-agents/core machine rolling/plugin
coordination and hook/skill generation selection. Lane L3: unresolved live-host update mechanism.
Tommy explicitly selected Claude; do not bounce this non-frontier task back to Codex.
Read the actual checkout's settings and applicable instructions; explicit user limits remain controlling.

## Observed evidence

The originating session d0affffee0995d0898222ed71d806c73 was already running when newer Core changes
were published. Its advertised machine handoff launcher still lacks await_handoff_startup, although
PR297 already published that fix. Its developer hook guidance still comes from two session-bound
hook-snapshots, 6dda1edd... and a7a8fcb3..., under .tj-agents-rolling/codex/sessions/<session>/.
The old advertised path is:
C:/Users/TommySeery/.codex/plugins/cache/tj-run-d0affffee0995d0898222ed71d806c73-base-agents/machine/local/codex-skills/handoff-claude/scripts/launch_claude.py
Current source includes the startup-confirmation fix. The terminal profile now refreshes plugins
before starting a CLI, but this has not made an existing session's advertised tools/hooks current.
Both base-agents and tj-agents hook packages are active in the originating session. Explain whether
that duplication is expected or contributes to generation disagreement; do not assume its cause.

This evidence establishes stale consumption, not which boundary can safely hot-reload.
Do not claim that already-loaded conversation instructions can be erased or that a source merge
automatically changes a live host. Distinguish source publication, cache refresh, selected package,
host acceptance, new skill loading and previously loaded context.

## Scope and boundaries

Trace and repair update awareness/adoption for long-running Codex and Claude sessions. Prove which
host-supported boundary can adopt a coherent new generation automatically; where native hot reload
is unsupported, implement an explicit, bounded checkpoint/resume or update-required transition with
truthful notification and preserved task ownership. Avoid silent mixed generations, forced process
termination and repeating expensive network refresh on every tool call.
The user wants updates to take effect automatically with clear evidence, not manual instructions to
remember a restart. Keep integrity checks and one-writer/handoff guarantees.
Extend the existing rolling/refresh owner rather than inventing parallel version/config systems.

Paths owned by the parent and excluded from successor writes until PR306 lands:
.agents/machine/utility/close/scripts/close_session.py
.agents/hooks/tests/test_session_close_operation.py
plans/concurrent-session-close/
Do not duplicate the close repair. PR306 also updates the stale routing example that blocked current
Windows CI; use its landed correction rather than creating a competing example patch.
Other launcher/refresh work exists: PR291 Fix/SelfHealingLauncherRefresh and older
Fix/RollingDependencyActivation. Inspect their canonical goals and native owner status before edits
that overlap them; contribute/reconcile rather than take over another delivery.
No employer/product repository changes or blind consumer profile installation. Do not mutate this
predecessor's frozen snapshots in place as a shortcut. No new scheduler or unrelated lifecycle rewrite.

## Acceptance

A reproducible before/after case starts a host on generation A, publishes/selects B, and observes the
next supported foreground boundary. Record selected generation, delivered hook/skill identity,
notification/adoption and preserved original task. Test both hosts at source level and perform
native acceptance where supported; label any host limitation honestly.
Prove stale/mixed snapshots and duplicate marketplace aliases cannot silently masquerade as current.
Include regression coverage for offline/update failure, integrity failure, and an in-flight turn.
Keep the candidate bounded, review it, pass required Windows/Linux CI and verify causal publication.
A source-only claim of live adoption is insufficient.

## Next Steps

1. Read this goal and claim lifecycle/live-session-plugin-refresh with your exact Claude native identity
   using .agents/machine/scripts/work_item_sessions.py claim, role owner, status active and this plan path.
   Acknowledge pickup in this goal before deliverable writes. Parent stops side-workstream writes at launch.
2. Inspect current rolling_plugins.py, startup_binding.py, codex_hook_snapshot.py, tier_gate.py,
   verified_convergence.py and both native terminal launchers. Check current live-owner conflicts and
   existing refresh contracts first. Record a concise causal trace and the smallest supported repair.
3. Reconcile primary Core BUGS.md B020, implement the bounded correction, test, review and deliver.
   Use existing delivery/continuation monitoring for future gates; do not stop merely after opening a PR.
4. Return exact delivery and native-acceptance evidence. Keep this goal current; do not rewrite the
   parent's separate PR306 goal. A definite launch failure or unknown existing owner remains a concrete
   resolver/resume condition, never authority to start a second writer.

## Progress

- 2026-10-18 pickup: claude:a727fe94-883c-4713-b4f9-13351c5374aa claimed
  lifecycle/live-session-plugin-refresh as owner/active at baseline 1518a351 (origin/main dc1f7415, no
  newer main commits). Next action: step 2 causal trace.
