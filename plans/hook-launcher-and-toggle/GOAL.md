# Transparent hook launcher and reversible hook controls

## Authorization and ownership

Tommy requested a handoff to improve the hook launcher after Bitdefender blocked it, then asked to disable hooks immediately and ship a convenient toggle. This is an authorized independent side workstream. The originating session retains the cris-authz PR 26 explanation. This successor owns only this checkout; preserve other sessions and unrelated changes.

Repository: C:\Users\TommySeery\source\repos\tj-agents\core
Worktree: C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-HookLauncherAndToggle
Branch: Fix/HookLauncherAndToggle
Base: fetched origin/main, 15911bd964a124b295b936a1769feae0e90cdcd1
PR: https://github.com/tj-agents/core/pull/164
Lane: L3, bounded unresolved design concerning launcher trust and host controls.
Transfer: picked up by the Codex successor in this checkout on 2026-10-09; scope and branch confirmed before deliverable edits.

## Evidence

Tommy supplied a Bitdefender alert blocking PowerShell 7.6.6 pwsh.exe while it launched the Python hook bootstrap. The bootstrap was an inline Base64-encoded program decoded and executed immediately. The exact antivirus detection rule is unknown; this is not evidence of a work-repository restriction or malicious plugin behavior.

Installed base-agents base, engineering and machine plugin version: 2.1.16. Their manifests reference hooks/codex.json. The Windows commands contain the encoded bootstrap. The decoded program hashes plugin contents, validates package identity, copies a verified plugin into PLUGIN_DATA/hook-snapshots, verifies the snapshot and invokes the chosen script using runpy.

Installed examples are under C:\Users\TommySeery\.codex\plugins\cache\base-agents\base\2.1.16\hooks and the corresponding engineering directory. Inspect codex.json and codex_hook_snapshot.py. Locate their authored generator and tests in this checkout.

Read AGENTS.md, README.md, SOURCE_LAYOUT.md and PACKAGING.md. Author .agents source only; plugins output is generated and must not enter the substantive commit.

## Immediate mitigation already applied

C:\Users\TommySeery\.codex\config.toml has enabled = false for all existing hook state entries plus hook identities discovered in cached manifests of enabled plugins: 48 entries. TOML parse and all-disabled assertions passed. Plugins and skills remain enabled; trust hashes were preserved. This proves saved configuration, not that an open host hot-reloaded it.
Backup: C:\Users\TommySeery\.codex\config.toml.before-hooks-disabled-20261009-105429.bak

Keep hooks disabled. Do not automatically enable hooks or execute the blocked bootstrap, change antivirus settings or add exclusions. Preserve unrelated config. User action is required for any optional live verification that needs hooks enabled; continue independent checks.

## Completion expectation

Replace the opaque launcher with an auditable supported invocation while preserving integrity, identity, snapshot verification, quoting, cross-platform operation and failure semantics. Determine what the host actually trusts: moving the verifier into an unverified mutable file can weaken the trust boundary. Make tradeoffs explicit.

Ship discoverable hook status/off/on controls, globally and per repository where the host supports it. Verify host capabilities rather than inventing configuration keys. Off must prevent bootstrap launch, not exit after startup. Keep skills enabled. Preserve prior states and trust metadata; restoration must not blindly enable every hook. Handle new or updated plugin hook identities and document observed restart/hot-reload behavior.

Add meaningful tests for transparent invocation, tamper rejection, disablement before execution, exact state restoration and preservation of unrelated configuration. Use repository validation and generation checks. Default to zero code comments.

Complete and verify the local change under repository rules. Report security properties, limitations and actual validation; do not claim Bitdefender compatibility without observed evidence. Do not re-enable local hooks without Tommy requesting it. No authority to alter antivirus settings.

## Next Steps

Local implementation and targeted validation are complete. Tommy subsequently requested merge in the current conversation on 2026-10-09. PR 164 targets main at head 58a0ac01df6e8d6ed5fb3eb77ee0c850a4ef449e. Finish exact-head Windows/Linux CI, merge through the supported ordinary mode, follow the causally linked generated-package workflow, then complete safe checkout cleanup. Keep the active user profile disabled. The request asks whether hooks can later be restored; it does not establish live Bitdefender acceptance or authorize blanket enablement. No installation into the active plugin cache or live antivirus acceptance test was performed. Bounded investigation used L3; specified implementation used L4 workers with disjoint ownership. Only regenerated launchers were executed in disposable test profiles.

CI blocker: run 37923659507 failed Windows verify job 113797367485 at step 19, source layout and package tests; Linux and generated-path guard passed. Captured failure artifact: 6fd8b72b0b061380-windows-ci-failure.log. The concurrent-off scenario reproduced on unmodified code at iteration 47 of 50. A parent-approved L4 writer lease covers only ExclusiveLock acquisition and its regressions. Lock-file open and initialization now share the existing ten-second acquisition retry, with failed handles closed before another attempt. The collapsed CLI error does not establish which individual acquisition statement failed. Deterministic open/initialization permission-error tests and the existing two-process restoration test validate the repair. Obtain a current-head review and rebind PR 164 before monitoring replacement CI; no merge is permitted while checks are red.

The repository exposes no merge queue and has auto-merge disabled. The host exposes no native scheduled conversation task. The Windows continuation adapter launches a fresh external Codex context; the prior automatic approval review rejected exporting repository contents, so this delivery uses one reconnect-safe monitor in the current authorized session rather than that external context. Exact delivery approval is recorded at reviews/hook-launcher-merge-approval.json; no additional user confirmation is needed for the ordinary merge after green checks.

Tommy supplied the Bitdefender command-line alert directly and requested CODE_CONVENTIONS.md linked from AGENTS.md. He clarified that the general rule must be language-neutral, based on ordinary alternatives to dynamic source execution; Python-specific portability standards support the Windows/Linux transition. Native Codex trust hashes hook definitions, not referenced Python script bytes; the short readable authenticator protects the packaged verifier. Base64 and explicit exec are removed; authenticated bytes are staged before runpy, retaining snapshot integrity and recovery. Same-user temporary-file races, altered interpreters and modified trusted configuration remain outside the integrity guarantee.

Codex supports features.hooks=false globally and in trusted project config. This disables dispatch before interpreter launch and covers newly introduced identities; project hooks.state is not a supported disable layer. Reversible controls must preserve feature-key absence and per-hook disabled/trust states, and report precedence and restart limitations.

## Implementation and validation checkpoint

The canonical hook-control utility and both host adapters ship through the machine package. The thin codex-hooks terminal function offers status/off/on. Off saves the prior canonical gate and writes false; on restores only that prior gate. Hook states, trust metadata, legacy aliases and plugin enablement remain untouched. Unsupported TOML syntax fails before configuration or snapshot edits; native layer precedence and trusted-project requirements are documented.

Focused checks passed: 24 control regressions after the Windows acquisition repair, including deterministic transient open and initialization failures, and 50 consecutive repetitions of the original two-process scenario. Package generation passed after refreshing local test digests. Earlier launcher checks passed: 10 snapshot tests (4 symbolic-link cases skipped because Windows link creation is unavailable), 3 Windows hook-command tests, packaging, PowerShell 7/Windows PowerShell profile tests, generation, catalog, harness and tier checks. Generated plugins and catalog digests are test output and did not enter the authored commits; the generated-path guard passes.

Full runs exercised 790 source tests and 983 shared-runtime tests. They were initially red: the new Claude helper permissions used an unsupported argument wildcard, the source-layout inventory still expected 73 definitions, and two layout fixtures copied inconsistent metadata during the repair. The permissions now use the supported :* prefix, catalog metadata agrees, and source-layout coverage expects 74 definitions and asserts both packaged helper paths. After repair, all 38 repo-config tests, 32 harness tests and the 3 failed source-layout scenarios passed. No complete green rerun of both broad suites is claimed.

The broad runs also saw a router subprocess timeout and an employer-scope assertion failure on unchanged code. The router scenario passed alone in 0.992 seconds against its unchanged 20-second limit; the entire employer-scope file passed on fresh isolated fixtures. No timeout was increased or scenario skipped. The last branch-base CI run 37859967381 actually executed both test steps successfully in Windows verify and verify-linux. Windows source/runtime durations were 7m21s/8m10s; the local concurrent runs took about 49m/42m. Local contention is consistent with the isolated results, but no underlying timing fix is claimed.

Local commits: 9fbf9bf77f9cb5a69232ea37ac7a13a9d3c07a5c replaces the encoded launcher, adds reversible controls and documents conventions; 5fe9562110590edcf503ea9cf7c147772481169e rejects corrupted restoration metadata found during review. The subsequent merge request authorized publication through PR 164.

7d8b52f5fe3a5fbefb9632b35aba829674d26b5f corrects the helper permission prefixes. The final source-layout checkpoint adds explicit shipped-helper coverage.

The active user config now also contains features.hooks=false, set through the utility. Its 48 disabled states, entire hooks subtree and plugin settings were preserved. Native Codex features list reports hooks stable false without a command-line override. The restoration sidecar records the formerly absent broad gate; restoring it later would preserve the already-disabled individual entries. The original mitigation backup remains intact. Open hosts still require restart.

Native Codex 0.157.0 accepted the feature gate in disposable profiles and returned no discovered hooks while off, including after a new plugin identity was added. A trusted marker positive control did not run from thread/start even when the gate was on; this proves configuration/discovery behavior only, not actual dispatch suppression. Source supports the pre-launch gate. No model turn, actual user hook, old encoded bootstrap or antivirus change was used. Live antivirus acceptance and open-host reload remain unverified. Only docker-desktop is available under WSL, so Linux execution is left to the existing CI tier.

## Reviews

Local parent review covers the authored implementation and its restoration, permission and source-layout repairs. Its corrupted-snapshot finding was fixed and regression-tested; no unresolved findings remain. Canonical work order: reviews/Fix-HookLauncherAndToggle.md records the exact final reviewed commit.

Automatic approval review rejected external native codex review because repository contents could be transmitted to an external model service without specific authorization. No retry or alternate export was used. Review continued through the safe in-session parent fallback; no independent native review result is claimed.

## Delivery completion

```completion
{
  "outcome": "Merge the transparent hook launcher, reversible controls and Python conventions while keeping the user's hooks disabled",
  "acceptance": [
    {
      "id": "launcher-integrity",
      "criterion": "Remove encoded source execution while preserving authenticated loader and snapshot behavior",
      "evidence": [{"source": "9aab5b2eb37520e2-final-snapshot-tests.log and 60e240f6d2e0d034-final-windows-launcher-tests.log", "result": "Snapshot and Windows launcher tests passed; four Windows symlink cases were skipped"}],
      "owner": "current Codex session",
      "next_action": "none"
    },
    {
      "id": "controls-and-conventions",
      "criterion": "Package reversible controls and link general execution and portable Python conventions from AGENTS.md",
      "evidence": [{"source": "c6a0da37ac5982ab-reviewed-control-tests.log, 252d7fe3b235aec1-repaired-repo-config-tests.log, 267343762ac950d5-repaired-harness-tests.log and 84b1d7e55461b818-repaired-source-layout-tests.log", "result": "22 control, 38 repo-config, 32 harness and three repaired layout tests passed"}],
      "owner": "current Codex session",
      "next_action": "none"
    },
    {
      "id": "keep-disabled",
      "criterion": "Preserve the saved native hooks-off gate, all 48 disabled states, trust metadata and plugin settings",
      "evidence": [{"source": "Native features list and hook_control.py status against the active user profile", "result": "features.hooks is false; all 48 individual entries remain disabled; no enablement or antivirus change was performed"}],
      "owner": "current Codex session",
      "next_action": "none"
    },
    {
      "id": "exact-head-ci",
      "criterion": "Windows and Linux full PR checks pass at the reviewed head",
      "evidence": [],
      "owner": "current Codex session",
      "next_action": "Wait for run 37923659507 at head 58a0ac01df6e8d6ed5fb3eb77ee0c850a4ef449e"
    },
    {
      "id": "land-and-generate",
      "criterion": "Merge PR 164 and verify its causally linked package generation",
      "evidence": [],
      "owner": "current Codex session",
      "next_action": "Merge only after exact-head checks pass; follow the merge commit's main workflow"
    }
  ],
  "deliveries": [{"repository": "tj-agents/core", "pr": 164, "head": "58a0ac01df6e8d6ed5fb3eb77ee0c850a4ef449e"}],
  "open_tasks": []
}
```
