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

## Causal trace (2026-10-19, source dc1f7415 + local disk, read-only)

- Binding is launch-only on both hosts. Codex: `startup_binding.run_session` → `rolling_plugins._prepare`
  (depth-1 fetch of main) → `codex_runtime_binding.prepare_runtime` creates session-owned
  `cache/tj-run-<nonce>-<marketplace>/<plugin>/local` aliases and `runtime-receipt.json`; hooks then run
  through `codex_hook_snapshot.py`, which copies the alias root keyed by `sha256(root, package digest)`.
  The alias content never changes during the process, so the session is frozen at generation A.
  Claude: hooks are `${CLAUDE_PLUGIN_ROOT}`-relative and the root is the registry `installPath`
  (`cache/tj-agents/<plugin>/<revision>`) resolved once at process start; `/clear` keeps it.
- No mid-session generation check exists. Claude has one only at SessionStart
  (`prune_plugin_cache.superseded_session`/`run_notice`); Codex has none; the UserPromptSubmit chains
  carry no version logic. Refresh (`refresh_cli`, terminal launchers) updates only the next process.
- Observed d0aff: every core alias root marker says 669d90ef; the newest locally verified Core main is
  476e31ce (Codex native `tj-agents/machine` marker) and dc1f7415 (Claude registry). Nothing compared them.
- Duplicate base-agents/tj-agents aliases: config enables `*@base-agents`, while dotnet/react
  `harness.json` dependencies name `*@tj-agents`; `resolve` dedupes by identity string only, so both
  identities resolve. One `resolve` pass fetches each source once (`catalog_cache`), so both aliases bind
  the same revision and digest (snapshots 6dda1edd/a7a8fcb3 share digest 183fd63a). Expected under the
  current selection; it doubles hook execution (cf. B019) but did not cause generation disagreement.
- Native capability: Claude 2.1.282 ships `/reload-plugins` (binary strings, documentation claim;
  hook rebinding unverified). Codex has no in-process plugin reload; `codex resume <id>` through the
  launcher binds a fresh generation. Forced restart from a hook is out of scope.

## Repair design (smallest supported boundary)

1. Rolling owner records each host's verified-and-installed generations: after `materialize_native`
   succeeds, append `{repository, revision, first_installed_at}` to
   `<host plugins>/cache/.tj-agents-rolling/generations.json` (bounded history, atomic replace, written
   under the existing host lock). A failed/offline refresh or integrity failure writes nothing.
2. New machine `plugin_generation.py` UserPromptSubmit gate for both hosts (local reads only, no
   network): resolves this session's bound roots (Codex: digest-checked runtime receipt, else
   `PLUGIN_ROOT`; Claude: SessionStart snapshot of the registry with `CLAUDE_PLUGIN_ROOT` authoritative),
   compares each repository's bound revision with the newest recorded across both hosts, and emits
   additionalContext every stale prompt plus a user systemMessage once per new state. It names
   superseded, mixed (one repository at two revisions, incl. duplicate aliases) and unverifiable
   bindings; it never states "current" for an unrecorded revision.
3. Adoption guidance is host-truthful: Claude → `/reload-plugins` (the next prompt's check confirms or
   still reports A, then restart via `claude --resume <id>`); Codex → resume the conversation in a new
   launcher-bound process. Task ownership and loaded conversation context are unchanged.
4. Remove the SessionStart-only superseded notice from `prune_plugin_cache.py` so one owner reports it.
Avoids startup_binding.py/terminal launchers (open PR291) and PR306 paths.

## Implementation and acceptance evidence (2026-10-19)

- Source: `rolling_plugins.record_generations` appends verified installs to
  `<host plugins>/cache/.tj-agents-rolling/<host>/generations.json` only after `materialize_native`
  succeeds; `plugin_generation.py` is wired into both hosts' machine UserPromptSubmit chains (and Claude
  SessionStart for the loaded-package snapshot); the SessionStart-only superseded notice was removed.
- Record placement correction found natively: a lone `cache/.tj-agents-rolling/generations.json` was
  deleted by Claude at startup in an isolated profile; the host rolling root (beside the persisted
  `rolling-plugins.lock`) survives. Reload correction found natively: a moved `CLAUDE_PLUGIN_ROOT` now
  re-snapshots the session's packages instead of trusting the SessionStart snapshot.
- Native Claude 2.1.282, one long-lived `claude -p` stream-json process, isolated
  `CLAUDE_CODE_PLUGIN_CACHE_DIR`/state, real marketplace shape (`git-subdir` core main), machine hooks
  trimmed to the gate plus a root echo: prompts 1-2 ran from A; after B was installed mid-session,
  prompt 2 delivered "runs 111111111111, superseded by 222222222222" as model context and a user notice;
  `/reload-plugins` ("Reloaded: 1 plugin · 18 skills · 5 agents · 2 hooks") rebound
  `CLAUDE_PLUGIN_ROOT` to the verified B install; prompt 4 was silent. With a relative-path marketplace
  source, reload bound `…/machine/unknown` and the gate reported it unverifiable, not current.
- Codex: no in-process plugin reload exists. Real-disk evaluation of the live d0aff receipt (11 roots,
  digest verified) with a temp record of 669d90ef→476e31ce reports "runs 669d90ef0c6c, superseded by
  476e31cea988"; duplicate base-agents/tj-agents aliases at one revision are not mixed. Native Codex
  turn-level acceptance is limited: driving a launcher-bound interactive Codex across two turns is not
  automated here; the hook output contract is the one `session-context.py --prompt-context` already
  delivers to Codex, and `hook_dispatch` subprocess coverage runs on both platforms.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/scripts/plugin_generation.py and rolling_plugins.record_generations",
  "hosts": [
    {
      "host": "claude",
      "behavior": "UserPromptSubmit reports superseded, mixed or unverifiable tj-agents generations and the /reload-plugins or resume adoption path",
      "source": ".agents/plugins/manifests/claude/machine-hooks.json",
      "mapping": "machine SessionStart session-start snapshot and UserPromptSubmit prompt gate through hook_dispatch",
      "verification": {
        "level": "installed",
        "result": "passed",
        "evidence": "native claude 2.1.282 long-lived stream-json probe: A-to-B report at next prompt, /reload-plugins rebinds to verified B, then silent"
      }
    },
    {
      "host": "codex",
      "behavior": "UserPromptSubmit reports superseded, mixed or unverifiable tj-agents generations from the digest-checked runtime receipt and the resume adoption path",
      "source": ".agents/plugins/manifests/codex/machine-hooks.json",
      "mapping": "machine UserPromptSubmit prompt gate through hook_dispatch and codex_hook_snapshot",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "unit and hook_dispatch subprocess tests plus real-disk evaluation of live session d0aff receipt"
      },
      "exception": {
        "constraint_evidence": "Codex has no in-process plugin reload and no automated two-turn launcher-bound native session driver exists in this repository",
        "supported_other_host_outcome": "Claude native long-lived acceptance passed with the same shared gate and record"
      }
    }
  ]
}
```
