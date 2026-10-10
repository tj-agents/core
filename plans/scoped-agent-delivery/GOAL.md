# Native Codex merge-gate enforcement and scoped delivery

## Outcome and authority

This goal owns the core source change that makes native Codex shell commands reach the existing merge-review and persistent-auto-merge gates. Both hosts must retain the shared review, security, identity, readiness and continuation checks. The source slice preserves every current fixed stop class and the current authorization schema. It does not install host profiles, change billing or repository protection, or grant stop-class exemptions.

The originating Rust discovery and twelve-repository authorization rollout remain with their parent. General both-host planning and review enforcement remain in the separately owned `Fix/BothHostAgentChanges` workstream, at `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-BothHostAgentChanges/plans/both-host-agent-changes/PLAN.md`; this goal does not absorb or change that scope. Repository-specific selection remains in the repo-owned rollout policies. Shared core code contains no tj-agents-only allowlist, Rust marketplace or stack detection.

## Owner and delivery boundary

- Checkout: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ScopedAgentDelivery`
- Branch: `Fix/ScopedAgentDelivery`
- Reviewed base: `49c618c5204140629df7a78dd7f8e47a0bfe749f`
- Reviewed source head: `3bda8e91428216c1a7321e05382877682860454c`
- Canonical goal: `plans/scoped-agent-delivery/GOAL.md`
- Review artifact: `reviews/Fix-ScopedAgentDelivery.md`, owned by the parent
- PR: not opened
- Implementation: completed by `/root/implement_scoped_agent_delivery`
- Review and delivery owner: originating `/root` session

The original reviewed source delta contained eight paths: the two shared merge gates, their two focused test modules, the Codex engineering hook manifest, the engineering harness declaration, the Codex Windows hook-command tests, and this goal. The current candidate delta against `33fb4155973b8ee1d26a8fd6f2a27d8428f6f166` contains those eight authored paths plus the shared shell extractor and its direct regression module. The native shell regression extends an existing original test path. `.agents/delivery-authorization.json` is already present on that base and is inherited published content, not an added path in this candidate. Generated `plugins/*` output and `.agents/catalog/catalog.json` remain uncommitted under core's source-only convention.

The original review artifact records complete approval and matching review and security watermarks at source head `3bda8e91428216c1a7321e05382877682860454c`; those review identities remain historical. Since that review, the branch was normally integrated with `origin/main` through `29827dfcfd81e7d59c75d9bf179c90e4d15dbdc8`, which contains the already-reviewed core #174 policy landing, then with `b4b576fa6a999fd43031e8c49aefaf32aa3a7d05`, merged core #175 at `3f06c88636ebb77fad3909ecfb367f0c3f50011c`, and published core #180 at `33fb4155973b8ee1d26a8fd6f2a27d8428f6f166`. #175's generic Claude-and-Codex coverage enforcement and #180's Windows owner-state race fix are inherited upstream; this goal retains its scoped native-gate implementation and does not absorb either workstream. Parent corrective review identified SD-01 and SD-02 in the canonical review artifact; their source and goal corrections are now recorded in this working tree, and fresh review/reconciliation of the exact candidate is pending. No PR has been opened.

## Completed source slice

- Native Codex shell payloads use the existing command extractor and canonical checkout envelope before reaching both shared merge gates. Ambiguous shell composition and unsupported or unresolved targets fail closed.
- Claude command parsing and gate behavior remain intact. The shared gates are declared for both hosts in the engineering harness; the Codex manifest wires the native hook calls.
- Permission-sensitive paths still require matching security review. Current-head review, required checks, readiness, and pending-auto-merge continuation binding remain enforced.
- Canonical checkout proof and literal command extraction reject ambiguous or unsupported target forms; the existing stop classes and authorization schema remain intact.

## Verification and review

The completed independent review is recorded at `3bda8e91428216c1a7321e05382877682860454c`; it approved the source candidate and found no changed-line defects. After the `33fb4155973b8ee1d26a8fd6f2a27d8428f6f166` integration, Windows source revalidation passed: Codex Windows hook commands (3), hook control (26), harness manifests (13), and paired instructions (1). A bounded Unix-shell argv recovery selects the script immediately after `-c` or `-lc` only for Bash, sh, zsh, and dash when present; it retains PowerShell's existing final-argument handling and safely joins a short Unix argv. Its direct extractor suite passed (26), its native review-gate regression reached the target repository's actual review check, merge-review passed 84 cases with one platform skip, and persistent-workflow passed 33 cases with eight POSIX-shim skips. The shipped host-coverage validator accepts this goal's single plan-stage record. Catalog-digest and generated-output checks also passed after refreshing generated outputs locally.

The reviewed tree intentionally contains pre-regeneration catalog metadata; the frozen CI workflow regenerates catalog digests and packages before verification. Exact-head Windows and Linux CI remain pending. Installed-profile activation remains unverified. Source and package checks describe source coverage only.

## Agent host assessment

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/merge_review_gate.py and .agents/hooks/persistent_workflow_merge_gate.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Preserve Claude shell-command parsing while the shared merge-review and persistent-workflow gates enforce current review, permission-sensitive security review, and pending-auto-merge continuation checks.",
      "source": ".agents/hooks/merge_review_gate.py and .agents/hooks/persistent_workflow_merge_gate.py",
      "mapping": ".agents/plugins/manifests/claude/engineering-hooks.json wires the shared gates; .agents/plugins/harness/engineering.json declares both gates for Claude and Codex.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "After the bounded Unix-shell argv recovery on the 33fb4155973b8ee1d26a8fd6f2a27d8428f6f166 base, shared gate suites passed: merge-review 84 cases (one platform skip) and persistent-workflow 33 cases (eight POSIX-shim skips). The direct shared extractor suite passed (26), including short Unix argv and preserved PowerShell final-argument behavior. Host-coverage plan validation, catalog, and generation checks passed. Exact-head Linux CI is pending; installed-profile activation is unverified."
      }
    },
    {
      "host": "codex",
      "behavior": "Extract native Codex shell payloads, prove the canonical checkout target, and run the same merge-review and persistent-workflow gate logic.",
      "source": ".agents/hooks/merge_review_gate.py, .agents/hooks/persistent_workflow_merge_gate.py, and tests/test_codex_windows_hook_commands.py",
      "mapping": ".agents/plugins/manifests/codex/engineering-hooks.json wires both shared gates; .agents/plugins/harness/engineering.json declares both gates for Claude and Codex.",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "After the bounded Unix-shell argv recovery on the 33fb4155973b8ee1d26a8fd6f2a27d8428f6f166 base, shared gate suites passed: merge-review 84 cases (one platform skip) and persistent-workflow 33 cases (eight POSIX-shim skips). Native Unix-shell regressions reached the review and continuation checks, and the direct shared extractor suite passed (26), including short Unix argv and preserved PowerShell final-argument behavior. Codex Windows hook commands (3), hook control (26), harness manifests (13), paired instructions (1), host-coverage plan validation, catalog, and generation checks passed. Exact-head Linux CI is pending; installed-profile activation is unverified."
      }
    }
  ]
}
```

## Next steps

1. **Source publication — `/root`:** reconcile the reviewed candidate with current `origin/main`, complete a fresh incremental review, publish a focused source PR, satisfy exact-head Windows and Linux CI, and merge through normal repository gates. After merge, verify the post-merge generation result and complete the authorized checkout and review cleanup.
2. **Approved stop-class second slice — not implemented:** on 2026-10-10 Tommy explicitly approved consideration of exemptions for `ci-workflow`, `migration`, `auth`, `money`, and `published-contract` across the twelve tj-agents repositories after reviews and required checks. Holds and policy self-changes still stop; other defaults are unchanged. This source slice preserves all fixed stops. A separate implementation requires its own owner, scope and review.

This goal's source slice is complete when the reviewed source PR passes exact-head CI, merges normally, post-merge generation is verified, and authorized cleanup is complete. The broader Rust discovery and repository rollout remain owned by the originating goal.

## Separate proposed scope: sensitive stop-class exemptions

The proposed generic `authorized_stop_classes` feature is separate from the completed source slice. Tommy explicitly approved this second slice on 2026-10-10 with the phrase “Approve for my tj-agents repos”: it may cover only `ci-workflow`, `migration`, `auth`, `money`, and `published-contract` across the twelve tj-agents repositories, and only after reviews and required checks. Holds and authorization-table self-changes remain stops; other defaults are unchanged. The approval does not mean implementation has started. Current fixed stop classes remain unchanged until a separate implementation is completed and reviewed.

The inert exact proposal is recorded at `C:/Users/TommySeery/source/repos/tj-agents/rust/.worktrees/Fix-RustStandardDiscovery/.agents/continuation/scoped-agent-delivery-proposal.patch`.

2026-10-10: automatic review rejected the proposed enforcement patch before it was applied: `This action was rejected due to unacceptable risk. Reason: This patch persistently changes shared merge-security enforcement, adds Codex hook coverage, and permits standing exemptions for CI, authorization, money, migration, and published-contract stop classes; the transcript does not explicitly authorize that exact broad security relaxation and blast radius. The agent must not attempt to achieve the same outcome via workaround, indirect execution, or policy circumvention. Proceed only with a materially safer alternative, or if the user explicitly approves the action after being informed of the risk. Otherwise, stop and request user input.` Status: historical automatic rejection, superseded only as to user approval by the explicit 2026-10-10 approval above; no enforcement source was changed.
