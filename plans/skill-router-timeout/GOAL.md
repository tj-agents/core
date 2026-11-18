# Skill router pre-tool timeouts

## Goal
Diagnose and repair repeated Codex PreToolUse skill_router.py child-execution/output-collection timeouts without weakening enforcement. Establish whether the router, native hook transport, or an inherited handle causes the timeout; preserve explicit policy blocks.

## Authority and ownership
Bounded side workstream under engineering:session-guidance standing standards-defect authorization. Own only C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-SkillRouterTimeout, branch Fix/SkillRouterTimeout, base 832e9e4. L3 because cause remains unresolved; no L1/frontier. Authorizes source implementation, testing, PR and merge after repository gates; no generated-cache edits, consuming-profile installation, unrelated session termination or broad reinstall. The originating sandbox task remains with session 01a11d56-65b2-70e2-975a-e34fed41be99.

## Evidence
Two native pre-tool requests were blocked with: Command blocked by PreToolUse hook: The Codex pre-tool hook C:/Users/TommySeery/.codex/plugins/data/base-base-agents/hook-snapshots/7e12f16de7b4b4fef9fbd6a47f50a00b5671f373077c53f1d5415adee233c93a/hooks/skill_router.py timed out during child execution/output collection. One was a multiline git/rustfmt/add/commit exec command; shorter equivalent commands succeeded. One was a roughly 4KB apply_patch adding a harmless fixture-rehearsal script under a standalone task directory (no ancestor Git/routes expected). Tools otherwise worked; same-time native sandbox failed on MAXIMUM_ALLOWED against live node_repl.exe, separately diagnosed upstream #51822. Do not assume causal relationship. Main task evidence lives read-only at C:/Users/TommySeery/source/repos/.tmp/interview-handoffs-2026-10-08/codex-setup/GOAL.md and evidence/. Installed CLI0.161.0; hook source snapshot above. Router main does written-target extraction then find_repo_root, returns early with no routes, plugin discovery uses bounded8sec subprocess. No router-specific payload or profiling captured yet. Main session preserved all caches and config. Existing Fix/CLIRefreshTimeouts PR81 concerns startup plugin refresh, not this observed PreToolUse symptom; reconcile overlap before changes.

## Completion
Produce bounded reproducer with exact input and timing, identify the actual owning mechanism, make the smallest source repair if a standards defect is proven, validate relevant regression and enforcement tests, review and deliver under source repository gates. If native transport is the owner, preserve precise evidence and objective upstream resolver rather than altering standards policy to hide it. Do not infer hook failure is fixed merely because native sandbox repair succeeds.

## Next Steps
1. Acknowledge pickup and actual session identity here; read AGENTS.md, owning bugfix and lanes. Verify branch/base and clean state. Inspect current source and real hook invocation plumbing, reconstruct the two inputs from originating transcript read-only if needed (no credentials).
2. Establish whether timeout is router computation, native stdin/output deadlock, or native sandbox. Compare no-repository early return and realistic large shell/patch payloads with bounded tests. Preserve safety and explicit blocks; do not edit installed cache.
3. Implement only proven owner fix, test focused regression plus policy retention, and apply repository review/PR/merge gates under standing authorization. Checkpoint concrete outcome or resolver here.

## Progress
Prepared by originating session on2026-10-08; one launcher submission will be attempted. Successor owns this side workstream after launch. Main owner will not write this checkout after submission.
Launcher attempt failed before native session creation: plugin add engineering@base-agents --json failed to back up plugin cache: Access is denied (os error 5). No successor exists or acknowledged pickup. No retries, cache edits or profile installation authorized here. Resume gate: source-owner launcher/plugin refresh access diagnosis restores normal launch, then launch this saved task once; originating sandbox task continues independently.
