# Repair unreliable interactive handoff startup

Tommy explicitly authorized this causal repair on 19 October 2026 after two Claude handoffs opened a black terminal and failed. The originating owner is codex:01a14f1d-abd0-74e0-9b75-b814a208ea87. Source checkout: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-HandoffStartupReliability; branch Fix/HandoffStartupReliability; baseline 281303c399046273be7b9d129daf8a9d4bde4d5b. One writer; bounded read-only audits do not own delivery. Diagnosis lane L3: terminal, native startup, workspace trust and hook entry remain unresolved alternatives.

## Authorized outcome

Identify and correct the mechanism behind repeated unusable handoffs, retain useful failure evidence and validate the actual interactive launch and task pickup. Compare working public implementations before choosing a correction. Preserve security, account separation and existing publication gates. Do not promise that external terminals or native hosts can never fail. Finish regression, independent review, Windows/Linux checks and authorized Core delivery. The separate broader hook/capability isolation cleanup is deferred at Tommy's explicit direction.

After the correction passes real acceptance, finish the requested Claude capability-isolation handoff, then transfer the original work-item goal to one fresh context. Original goal: C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-TrackerAwareSkills/plans/tracker-aware-skills/GOAL.md. Preserve its manual PR298 hold, frozen candidates and separate consumer-migration owner. Do not implement tracker changes in this repair checkout.

## Evidence

- Both packaged handoff-claude attempts exited 1 with native Claude not acknowledging SessionStart before its startup deadline. Receipts: C:/Users/TommySeery/AppData/Local/Temp/tj-agents-handoff-uzg732g8/status.json and C:/Users/TommySeery/AppData/Local/Temp/tj-agents-handoff-c5n2vojk/status.json. No successor pickup was established; no blind retry is authorized by a timeout alone.
- Native Claude version observed 2.1.282. A wrapper init-only probe acknowledged at187.28 seconds after182.16 seconds preparation. This does not prove an interactive session or task pickup.
- Direct bounded interactive debug ended before any observed SessionStart at installed-plugin enumeration/browser registration; the earlier summary saying this proved successful interactive startup was too strong.
- Exact Windows Terminal bounded diagnostic has no task prompt and tools disabled. Receipt C:/Users/TommySeery/AppData/Local/Temp/handoff-reliability-diagnostic/interactive-result.json. Its wrapper entered with all three standard streams reporting isatty true, no CLAUDE_CONFIG_DIR or CLAUDE_CODE_PLUGIN_CACHE_DIR override, TERM=xterm-256color and FORCE_COLOR=1. A timer limits its exact native child to25 seconds; the startup wrapper also cleans its own child on missing acknowledgement. No repair writer was launched.
- Read-only native consent metadata showed no exact Fix-RepositoryCapabilityIsolation entry in ~/.claude.json. This is a lead, not a confirmed causal diagnosis. Official Claude docs say interactive settings hooks wait for workspace trust, whereas noninteractive execution treats the workspace as trusted. Do not mutate trust to make the test pass.
- Static audits found that existing handoff/startup tests exercise receipts, mock arguments and profile routing, without native packaged interactive terminal acceptance.

## Existing solutions assessment

Tommy explicitly reopened this assessment. Claude Squad starts native agents in a PTY-backed tmux session, polls exact session existence, captures pane output and cleans partial failures. Workmux uses a separate bounded pane-readiness handshake before injecting commands and supports prompt files/native agent command injection. Adopt useful mechanisms only where they correct measured behavior; neither repository establishes Windows Terminal acceptance for us. Keep shell-ready, process-started, hook-acknowledged and task-picked-up facts separate.

Primary references inspected:
- https://github.com/smtg-ai/claude-squad/blob/main/session/tmux/tmux.go
- https://github.com/raine/workmux/blob/main/src/multiplexer/handshake.rs
- https://github.com/raine/workmux/blob/main/src/multiplexer/agent.rs
- https://code.claude.com/docs/en/cli-reference
- https://code.claude.com/docs/en/hooks#workspace-trust
- https://learn.microsoft.com/windows/terminal/command-line-arguments

## Next Steps

1. Read the already running bounded diagnostic receipt and narrowly filtered native debug. Do not launch another probe while its owner/cleanup is unresolved. Distinguish preflight, native terminal/trust setup and actual hook entry. Verify current installed source identities because the parent session is not generation-bound.
2. Choose the smallest causal source correction from that discriminator. Preserve security gates; do not disable hooks, auto-accept workspace trust, hide errors or merely increase timeouts.
3. Add focused failing-before/passing-after regressions, then run python -m unittest tests.test_handoff_startup tests.test_launch_claude tests.test_terminal_launchers tests.test_startup_binding and the affected agent_cli tests. Add opt-in real packaged interactive acceptance; init-only is a control, not acceptance.
4. Obtain independent review, required Windows/Linux checks and permitted Core source delivery. Verify visible native startup, exact attempt identity and actual goal pickup before reporting a completed handoff.
5. Resume the original handoff sequence above. Broader hook cleanup remains separately deferred.

## Verified investigation and source checkpoint

The exact wrapper interactive probe acknowledged SessionStart9.02 seconds after native launch, after187.02 seconds of preparation. Its exact native child was cleaned and wrapper exited; it did not own a task. Tommy separately confirmed the Bounded handoff argument diagnostic actually replied DIAGNOSTIC using the same explicit L3 model/effort and initial-prompt mechanism as the failed handoff. Its exact child was also cleaned. Missing saved trust metadata is therefore insufficient to diagnose this failure; the earlier trust lead remains unconfirmed. Hooks, model and prompt can work. The intermittent original failure remains open.

The first bounded source correction makes preparation visible, retains a native Claude debug destination in the attempt receipt and always prints both hosts' receipt paths on failure. It changes neither the startup timeout nor hook confirmation/cleanup requirements. This corrects confirmed observability defects; it is not a claim that the intermittent cause has been removed.

Windows focused result:220 tests,24 platform/environment skips,196 passed. Command: python -B -m unittest tests.test_handoff_startup tests.test_launch_claude tests.test_launch_codex tests.test_terminal_launchers tests.test_startup_binding tests.test_agent_cli. Private captured result: .git/agent-workflow/runs/handoff-startup-reliability/artifacts/357dfbf14228879e-focused-launchers.log. Two phase/diagnostic regressions fail against untouched baseline as expected. Source generation succeeds after the prescribed uncommitted catalog-digest refresh. Workflow skills accepts the supported explicit canonical lifecycle path bugfix=.agents/engineering/workflow/bugfix/SKILL.md; its name-only legacy default points at an absent old layout, so do not create a duplicate layout to satisfy it.

Current next action: freeze/review this diagnostics candidate, run required remote coverage and observe a real task pickup with retained diagnostics. Preserve B024 as unresolved until the intermittent cause is measured and corrected. Broader hook cleanup stays deferred. PR: not opened.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": "Core Machine startup_binding.py and the Claude/Codex handoff launchers",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Display preparation phases and retain an exact failed-attempt receipt; Claude additionally retains native startup debug output.",
      "source": ".agents/machine/scripts/startup_binding.py and .agents/machine/utility/handoff-claude/scripts/launch_claude.py",
      "mapping": "Generated machine skills entry and shared runtime resource",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "220 focused Windows launcher/binding tests pass with24 platform/environment skips; both hosts failure receipt assertions and source generation pass. Native diagnostics before this source change proved interactive startup only; new-source native acceptance and Linux CI remain pending."
      }
    },
    {
      "host": "codex",
      "behavior": "Display preparation phases and retain an exact failed-attempt receipt; Claude additionally retains native startup debug output.",
      "source": ".agents/machine/scripts/startup_binding.py and .agents/machine/utility/handoff-codex/scripts/launch_codex.py",
      "mapping": "Generated machine codex-skills entry and shared runtime resource",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "220 focused Windows launcher/binding tests pass with24 platform/environment skips; both hosts failure receipt assertions and source generation pass. Native diagnostics before this source change proved interactive startup only; new-source native acceptance and Linux CI remain pending."
      }
    }
  ]
}
```

## Deadline starvation reproduced and corrected

A real-child regression reproduces a healthy native startup being terminated when plugin preparation leaves only 0.01 seconds on its deadline. The child writes the exact acknowledgement after 0.15 seconds. Before the correction it fails with the same missing-SessionStart error as the original launches. The correction gives native acknowledgement its own existing 20-second budget after launch; preparation remains bounded at 300 seconds and outer handoff observation remains 480 seconds. No hook or trust check is bypassed and no configured timeout value is increased.

Focused verification after the correction: 221 tests in 14.396 seconds, 24 platform/environment skips, all others pass. Evidence: .git/agent-workflow/runs/handoff-startup-reliability/artifacts/deadline-fix-tests.log. Native normal-tools diagnostic session 00b29f92-3654-48b3-ac3f-a802d6eda8e1 acknowledged 7.44 seconds after launch and its native transcript contains the actual response NORMAL_TOOLS_DIAGNOSTIC. Its exact child was cleaned. This establishes a concrete failure mechanism and a successful normal-tools path; original receipts lack phase timing, so attribution of both historical failures remains unproven.

The first frozen review completed with one verified Codex phase finding. Its correction reports the true runtime/acknowledgement phase and passes the focused suite. Native review evidence is retained privately. The configured workflow reviewer model was unavailable; parent fallback completed that bounded frozen check. Incremental review must cover both the phase correction and deadline correction against 828a85cc4a6ea4c46a5f19a12c07c935819101f9.

The prior incremental preparation was cancelled but its Python child survived the shell cancellation; its exact command, PID and creation time were verified before stopping only that child. The following preparation failed because the cancelled helper had left a bundle without an authoritative descriptor. No native task owner was duplicated. Do not confuse shell cancellation with verified child termination. Current next action: finish incremental review, remote validation and a single verified real goal pickup. Broad capability/hook cleanup remains deferred.

PR: not opened
