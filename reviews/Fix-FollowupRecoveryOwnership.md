# Code review ? Fix/FollowupRecoveryOwnership

**Review status:** `complete`
**Reviewed up to commit:** `9954043c5d7b34c59e70cc1df193e370c3f759b6`  `(2026-10-12)`
**Judgment:** `approved`

## Review pass ? 2026-10-11 ? full

**Candidate base:** `73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c`
**Candidate head:** `59de0bd924559dcb48836754a1ed732254ed1202`
**Candidate branch:** `Fix/FollowupRecoveryOwnership`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:339f8c393ee33cebf247e8d1a192d43bdaa835acf6142a40eab2d1945f1314c8 (7 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\tzyPvah1DykxRepYz-QugN\di1TmWEf29ff5DNWS3sR_X`
**Candidate bundle identity:** `sha256:f35314554250befe23f2cfb10d8d7f94f99eab324258c4e9ad528393f181f4ce`
**Work-order path:** `reviews/Fix-FollowupRecoveryOwnership.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R1 ? MEDIUM ? native/workflow** ? `.agents/machine/utility/open-codex/SKILL.md:17`
  The recovery route requires ownership acknowledgment/release and child-writer reconciliation, but its invocation supplies only `Continue the requested work.` Give recovery callers an explicit `--prompt` payload that requests those actions before conflicting source writes.

Native reviewer: supported declared fallback, artifact `447c323bfe24d9ee-native-review-fallback.log`. Its read-only test attempts lacked writable temporary directories and refreshed generated payloads; they are not validation evidence. The independently validated Workflow v2 lens `recovery-workflow-fallback-1` corroborated R1 (confidence 96). Parent verified changed-line citations, immutable identities and acceptance evidence and deduplicated the findings. Tier gate returned no applicable stack conventions; frozen routes and security classification were empty. Source coverage check passed. No other actionable findings retained.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/utility/followup-codex/SKILL.md and .agents/machine/utility/open-codex/SKILL.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Assess supported exact Codex owner recovery before manual coordination fallback",
      "source": ".claude/skills/followup-codex/SKILL.md and .claude/skills/open-codex/SKILL.md",
      "mapping": ".agents/plugins/sources.json machine canonical and Claude adapter mappings",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Captured Windows recovery (18), harness (15) and repo-config (38) tests passed; both-host generation/catalog/declaration/packaging/adapter/docs checks passed in followup-recovery -r3 artifacts. Source verification only; no consumer installation."
      }
    },
    {
      "host": "codex",
      "behavior": "Assess supported exact Codex owner recovery before manual coordination fallback",
      "source": ".codex/skills/followup-codex/SKILL.md and .codex/skills/open-codex/SKILL.md",
      "mapping": ".agents/plugins/sources.json machine canonical and Codex adapter mappings",
      "verification": {
        "level": "source",
        "result": "passed",
        "evidence": "Captured Windows recovery (18), harness (15) and repo-config (38) tests passed; both-host generation/catalog/declaration/packaging/adapter/docs checks passed in followup-recovery -r3 artifacts. Source verification only; no consumer installation."
      }
    }
  ],
  "candidate_head": "9954043c5d7b34c59e70cc1df193e370c3f759b6"
}
```

R1 disposition: both canonical skills now supply a concrete blocker-specific recovery prompt requiring acknowledgment/release, child-writer reconciliation and status reporting before conflicting source writes. Guidance packaging/generation/catalog/adapter and documentation checks passed; fixing commit 36d7374d81cf4620a11c41b7bb31e15b046b8711.

## Review pass ? 2026-10-12 ? incremental

**Candidate base:** `59de0bd924559dcb48836754a1ed732254ed1202`
**Candidate head:** `36d7374d81cf4620a11c41b7bb31e15b046b8711`
**Candidate branch:** `Fix/FollowupRecoveryOwnership`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:0cb3f40dd9227650f72a6697c03f2ae26106879df79116a7cfc66fb77314d8b6 (3 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\7h4VeQSua0ZHbdFbxRqdOW\qK6xLwroT-mbTW2qTRj3g7`
**Candidate bundle identity:** `sha256:36c8569bd6d536560ada2bf1cc5fdaee2d6b6dcf6328543679b2b618119169c8`
**Work-order path:** `reviews/Fix-FollowupRecoveryOwnership.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **R2 ? MEDIUM ? native** ? `.agents/machine/utility/followup-codex/SKILL.md:61`
  Substituting the actual blocker into a single-quoted shell argument can terminate the quote when failure text contains an apostrophe or shell syntax. Write the recovery instruction to a private UTF-8 file and use the already supported `--prompt-path` argument, preserving exact-owner and acknowledgment safeguards.

Native fallback completed (artifact `fb3bc9b07627e567-native-review-r1.log`). Fresh validated Workflow v2 lens `recovery-workflow-r1-1` found no additional defect. Parent verified R2 against the changed shell example and existing agent_recovery.py prompt-path support. Source coverage passed at this head; frozen routes/security classification and tier conventions remain empty.

- [x] **R3 ? HIGH ? exact-head CI** ? `.agents/plugins/harness/machine.json:89`
  The new Claude allow entries put argument tokens after the Python script path, which the unchanged consumer validator rejects. Linux CI run 38183104061/job 114599653219 fails repository-configuration tests with that error. Use the existing canonical script-boundary wildcard declaration, retain supported Codex prefixes, and verify the complete machine requirement with the shared validator. Describe prefix scope honestly rather than claiming semantic argument enforcement.

Failure provenance: latest examined successful main run 38170019843 at d3fc4d49ca412d9e9811faa3b07aed4d43ff0f70 executed verify-linux successfully (2026-10-11 19:55:07?19:59:05 UTC) and verify-windows successfully (19:55:06?20:09:13). The owning validator and CI invocation are unchanged across those heads. The candidate manifest introduces the rejected shape; this is a deterministic declaration regression, not a timing failure. Captured failed Linux job: 29baf85f3ea37738-linux-job-log-207.log.

R2 disposition: private UTF-8 recovery instruction with existing --prompt-path, no simultaneous --prompt or dynamic blocker in shell source. Captured recovery-prompt-file-tests passed (18 tests), including real prompt-file adaptation and unchanged file bytes with shell-significant text.

R3 disposition: Claude declarations use the existing exact script boundary (8 raw/16 rendered entries); the Codex initial command prefix is retained. Neither declaration is described as semantic argument enforcement. Complete machine requirements now pass the unchanged consumer validator; 15 harness and 38 previously failing repo-config tests passed. Generation/catalog/declaration/packaging/adapter/docs checks passed, logs under corresponding -r3 labels.


## Review pass - 2026-10-12 - incremental

**Candidate base:** `36d7374d81cf4620a11c41b7bb31e15b046b8711`
**Candidate head:** `9954043c5d7b34c59e70cc1df193e370c3f759b6`
**Candidate branch:** `Fix/FollowupRecoveryOwnership`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:67236e0d8e53e7b877ee0248e9560ee5c2ffe853ac50568e926386944f65a7c1 (6 paths)`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\5iphtq8i-RlrysAxE_RJpv\MvK_kRmG99fgcFVwwuXVrl`
**Candidate bundle identity:** `sha256:d7b0a1b5595a15f9031fd8c4cb7af683de3383572ea09b9ec584480736971389`
**Work-order path:** `reviews/Fix-FollowupRecoveryOwnership.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Phase lanes: independent review L4 (specified repair, testable correctness); publication L7 (mechanical exact-head push). Native specialist unavailable on this account; use declared supported fallback and fresh read-only workflow lens. Windows old-run failure confirmed the same manifest-consumer error as Linux, captured 2d217baaed48d64b-windows-job-log-207.log.


### Findings

No new retained findings. Native fallback artifact c276b133aa3d286b-native-review-r23.log completed. Fresh workflow lens recovery-workflow-r23-1 result validated against Workflow v2 after one acceptance-condition correction; exact result saved as workflow-review-r23.json. Parent verified identities, citations, confidence, supported acceptance and decision boundary. Host coverage passed; frozen routes/tier conventions/security classification empty. Remote base unchanged and exact-head reconciliation passed.

Native permission concern disposition: not retained as a defect. The cited harness AGENTS contract requires coverage of exact instructed commands; it does not require exclusive host/operation parsing. Existing canonical script wildcard inventory and unchanged consumer grammar establish the same script trust boundary. Generic recovery operations are already shipped utility behavior; manifest approval is not task authority. This candidate deliberately describes actual prefix breadth and tests it. A new confining adapter would add a requirement and runtime not established by this contract. Independent bounded investigation corroborated the contract interpretation.

The workflow lens full exported-tree harness attempt saw the unrefreshed generated catalog; repository CI refreshes it before checking and captured local regenerated checks passed. That attempt is not a new source defect or a full-suite validation pass. Two test-subprocess pyc files were the only tree drift; parent compared every authored file to tree.tar, removed only those extras and successfully revalidated the exact descriptor. Earlier finding text, severities, identities and completed pass judgments remain unchanged.
