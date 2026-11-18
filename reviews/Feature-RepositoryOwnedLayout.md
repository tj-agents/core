# Code review — Feature/RepositoryOwnedLayout

**Review status:** `complete`
**Reviewed up to commit:** `4fd86e3772b004022eb924e638215b2158271381` `(2026-10-07)`
**Judgment:** `approved`

## Review pass — 2026-10-07 — docs

**Candidate base:** `61d4920477a313528f855babd2e4ee4ccdf3d8f6`
**Candidate head:** `fe7ddc87535fbe52693ef098e4edc3bc07c2b246`
**Candidate branch:** `Feature/RepositoryOwnedLayout`
**Candidate scope:** `plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md`
**Candidate path-set:** `sha256:0a55d8515be6359b468c4be34a313f0c9021da9dc8579f16814f8a6cfdc729ce` `(1 paths)`
**Candidate patch:** `sha256:2bd380b25b25d6783628393f85ccbb766119238286b1626b1110b056a6d1c00a`
**Candidate bundle:** `C:/Users/TommySeery/AppData/Local/Temp/review/mS7RZPUPbus2bffhy8mjBa/UpWLD8WaAnMGv5y_AbMpV1/Xj96b1Ih2s2HT_AvU319Ts`
**Candidate bundle identity:** `sha256:5f216c4fb0089ce7785c16e2a8d7ef4da560d4955e74146d1e1d6410fcaf319d`
**Work-order path:** `reviews/Feature-RepositoryOwnedLayout.md`
**Work-order mode:** `new`
**Pass judgment:** `changes-requested`

Design readiness review precedes implementation. Applicable sources: frozen AGENTS.md, README.md,
SOURCE_LAYOUT.md, PACKAGING.md, plans, lanes, open-worktree and git-branching. No routed technical
skills or security path was selected by the descriptor. Native review and one bounded allocator
followability/migration-safety lens run against the same frozen plan.

### Findings

- [x] **INST1 — MEDIUM — followability** — `plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md:282`
  Fetch without an explicit refspec can leave a selected stack-parent ref stale under narrowed remote
  configuration. Define the selected-ref fetch mapping and advertisement check, and test a stale ref
  excluded by the configured fetch mapping.
- [x] **INST2 — MEDIUM — consumption contract** — `plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md:244`
  Successful restoration leaves `base_ref`, `base_head` and `created` undefined. Define field meanings
  and concrete results for new, existing-local and remote-only creation before implementation.
- [x] **ACC1 — MEDIUM — native-general** — `plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md:267`
  A separate Git directory named `administration/.git` passes the proposed common-root checks and
  allocates outside the consumer checkout. Verify the primary worktree's top-level path equals the
  candidate common root, and add a relocated-Git-directory refusal regression.

All three were resolved in the corrected design: explicit selected-head advertisements and refspecs,
typed result examples for all three modes, and both inside-worktree/top-level identity guards. Hostile
inherited Git selector variables are also cleared following the existing cleanup-gate boundary.
The correcting commit carries the reconciled existing adoption ledger. Delta review remains required.

Native layer: `codex review --base 61d4920477a313528f855babd2e4ee4ccdf3d8f6`, resolved L2, completed
successfully against head `fe7ddc8`. Its temporary Git fixture reproduced ACC1. Independent critical
followability lens `allocator-design-lens` returned a valid Workflow v2 envelope with the exact frozen
identity and high-confidence INST1/INST2 evidence. Parent verified all three against frozen source.
Frozen-tree docs reachability passed with zero errors/warnings. Plan graph passed with one pre-existing
oversized adoption-ledger warning. An unrelated adoption-ledger formatting delta was excluded from this
bounded plan review; it did not change the candidate plan or HEAD.

## Review pass — 2026-10-07 — incremental

**Candidate base:** `fe7ddc87535fbe52693ef098e4edc3bc07c2b246`
**Candidate head:** `0df530ed75f66d7f73ad3bdb25d41d5f184630dd`
**Candidate branch:** `Feature/RepositoryOwnedLayout`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:d6403eb99aa792ed74cf93f76e215538f2dd595edad94c85ee967ff5cafe24fe` `(2 paths)`
**Candidate patch:** `sha256:538be8e9d4c3492c28bf803782f48deccef4f741fd1de971c31dcbdb4c4b3417`
**Candidate bundle:** `C:/Users/TommySeery/AppData/Local/Temp/review/mS7RZPUPbus2bffhy8mjBa/998CwYipz-NGunmQ4e9jxl/FXuDMeN-zpRmvZ4Y7Nt4N6`
**Candidate bundle identity:** `sha256:ed69d6e477a2e481b3989616dbf80064856487fd76413eaed7d5ce7979467ffc`
**Work-order path:** `reviews/Feature-RepositoryOwnedLayout.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **DOC1 ? MEDIUM ? native-general** ? `plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md:377`
  The new review-work-order pointer is absent from the committed tree. Replace it with durable,
  self-contained review outcome evidence in the goal while retaining the local work-order lifecycle.

Native delta review completed against `0df530e`. Its missing-adoption-Next-Steps finding was rejected:
`git show 0df530e:plans/repo-declared-config/REPO_DECLARED_CONFIG_PROGRESS.md` contains the section
and all four continuation fields at lines 24?36. No ledger repair is needed.

ACC1 remediation was incomplete: a parent-run real-Git fixture still accepted a separately relocated
primary because Git infers the common directory parent when probed there. Reopened and resolved with
a caller-side top-level/absolute-Git-directory check plus reciprocal linked-worktree registration.
The corrected fixture passes primary and linked acceptance and relocated-primary refusal. Git cannot
universally recognize that unsupported primary layout from a linked checkout; the design states that
limit explicitly. The original finding and completed pass judgment are unchanged.

DOC1 is resolved by recording review evidence directly in the goal. Both corrections require the next
incremental pass. Frozen docs reachability passed with zero errors and warnings. Plan graph and
whitespace checks passed before commit.

## Review pass — 2026-10-07 — incremental caller identity

**Candidate base:** `0df530ed75f66d7f73ad3bdb25d41d5f184630dd`
**Candidate head:** `77d6b7e660b24f6e5a6349f0904e72e71269e633`
**Candidate branch:** `Feature/RepositoryOwnedLayout`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:0a55d8515be6359b468c4be34a313f0c9021da9dc8579f16814f8a6cfdc729ce`
**Candidate patch:** `sha256:747c87b6550de4d242aba2259f33230bd2b343cfebf53a1467619a9cce864c0f`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\5AhRnWlgGW2zJxbmOMcHG0\UWVsGAt9Lva5gVOJbOyXA3`
**Candidate bundle identity:** `sha256:0fe54154c4128b1b564293ca9ca85125611034680f418dd41b5e7428146f4437`
**Work-order path:** `reviews/Feature-RepositoryOwnedLayout.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

### Findings

- [x] **ACC2 — MEDIUM — native-general** — `plans/repository-layout/REPOSITORY_LAYOUT_PROPOSAL.md:289`
  Relative Git worktree registrations resolve against the process cwd in the example. Resolve each
  pointer from its containing directory and test a relative registration invoked from a nested directory.

Resolved by joining the administrative gitdir target to caller_git before resolution. A real Git
--relative-paths fixture confirms a relative pointer resolves correctly from nested caller cwd.
Frozen-tree docs reachability and plan graph pass. The native fallback completed successfully.

Native specialist gpt-5.3-codex-spark was rejected by the host account before review. Retrying the same frozen pass with the host contract's gpt-5.6-terra fallback at medium effort. No source identity changed.

## Review pass — 2026-10-07 — incremental relative registration

**Candidate base:** `77d6b7e660b24f6e5a6349f0904e72e71269e633`
**Candidate head:** `ae60ebf46dba6d993c54407127ad1611a2dd150d`
**Candidate branch:** `Feature/RepositoryOwnedLayout`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:0a55d8515be6359b468c4be34a313f0c9021da9dc8579f16814f8a6cfdc729ce`
**Candidate patch:** `sha256:8b625db53acb11c04b3d2f09a9a3f4670370a96203bafe492fa3dbbc325280a5`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\Yri4SVUU43ZGrG1z4wyHRY\BfC2yUlDp1W3StPEi4B1G4`
**Candidate bundle identity:** `sha256:d6e0486ab2c1e1074e1928c936a0141c8891059bbd5f944151c9d6c5e99ac509`
**Work-order path:** `reviews/Feature-RepositoryOwnedLayout.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

### Findings

No new findings. Native gpt-5.6-terra review completed over the frozen one-path correction and confirmed both relative and absolute pointer behavior. Parent real-Git nested-relative fixture and frozen-tree docs reachability passed. The allocator design is ready for its specified L4 implementation. All completed review bundles are disposable; identity descriptors remain in Git-private state.

## Review pass — 2026-10-07 — incremental allocator implementation

**Candidate base:** `ae60ebf46dba6d993c54407127ad1611a2dd150d`
**Candidate head:** `6383bbca545f56544d28a16184aa11266dc33e17`
**Candidate branch:** `Feature/RepositoryOwnedLayout`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:072673583abf603a0ccd1a86229a2a2a16a2f4de49d55cffd9968e620421d763`
**Candidate patch:** `sha256:cb970b2931e70b00b753b7d9e6afd6c61358b8f3069eaaa52a8da4140c7da185`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\tDIONvKGqFZEKgbPQoDkxG\E_O8b-C7PEbTzMAgVLHKY1`
**Candidate bundle identity:** `sha256:8ed9c9dff8195c08ee41a3ed9bbf2aa7c63924fed6577d3ae320382cfec00343`
**Work-order path:** `reviews/Feature-RepositoryOwnedLayout.md`
**Work-order mode:** `append`
**Pass judgment:** `changes-requested`

The incremental range includes previously delivered main changes from synchronization at 99d2be1.
The prospective PR against locally observed origin/main f9f5183 contains the five allocator authored
paths plus the existing goal and adoption ledger. This pass is local preparation: a native side owner
reported automatic approval review denial of the core fetch outcome, and requested user permission
has not arrived. No new fetch, synchronization or delivery is performed by this review. Reconcile the
real current main and any intersecting rules before final PR delivery once that gate clears.

Descriptor-selected lenses: native-general and workflow; no security path or routed rule selected.
Native host review uses the configured gpt-5.6-terra fallback because gpt-5.3-codex-spark was proven
unavailable with this account. The independent workflow lens is bounded to allocator behavior,
packaging/permissions and failure preservation. Generated working output is not an authored candidate.
Focused tests: allocator 17 (one symlink skip), harness 10 (one Codex CLI skip), source layout 19;
harness and generated checks green. Plan graph and staged whitespace checks passed.

### Findings

One confirmed restoration defect requires repair.

Workflow specialist dispatch was rejected before execution because gpt-5.3-codex-spark is unavailable. Re-selected the supported read-only L4 fallback (gpt-5.6-terra/high) for that bounded lens; native review remains at medium. No findings were supplied between reviewers.

Parent-confirmed finding:
- [x] **ALLOC1 ? MEDIUM ? parent-real-Git** ? `.agents/engineering/operation/open-worktree/scripts/worktrees.py:343`
  Remote-only restoration with remote.origin.fetch limited to main fetches the requested object, creates
  its checkout, then fails to set upstream because the selected ref is not represented in the remote's
  configured mapping. The real fixture returned 2 with ?cannot set up tracking information? and left
  the new worktree present. Support the selected branch's tracking mapping before creation, preserve
  existing fetch configuration/exclusions, and add a narrowed-remote restoration regression.

Native review completed successfully with one generated-harness finding. Rejected: that path is an
upstream change brought into the incremental range by synchronization, and is absent from the actual
PR diff against f9f5183. The generated-path guard passes. The independent allocator workflow lens
validated the frozen bundle identity and returned no findings; parent checked its changed-source
citations and packaging conclusions. Frozen docs reachability returned zero errors and warnings.

ALLOC1 was reproduced independently using a real temporary remote with a main-only fetch mapping.
A second fixture proves that adding the exact selected branch mapping preserves the main mapping,
allows restoration to complete and makes @{upstream} resolve to the expected commit. Repair must
also retain configured negative exclusions and refuse an excluded restoration before creating its
branch or checkout. No fetch or other operation touched the gated core remote.

ALLOC1 resolved: selected positive fetch mappings are preserved, the helper adds only a missing exact
tracking mapping, and exact/wildcard exclusions refuse before branch or checkout creation. The focused
real-Git suite passes: 19 tests in 181.583 seconds, one Windows symlink skip. This includes future normal
fetches updating the restored upstream and both refreshed generated host copies running outside the
author tree. Three harness declarations and the generated-tree check pass. New fixture failures were
repaired without weakening allocator assertions. The correction requires incremental review.

## Review pass - 2026-10-07 - incremental restoration correction

**Candidate base:** `6383bbca545f56544d28a16184aa11266dc33e17`
**Candidate head:** `4fd86e3772b004022eb924e638215b2158271381`
**Candidate branch:** `Feature/RepositoryOwnedLayout`
**Candidate scope:** `all`
**Candidate path-set:** `sha256:7cdca52db782f0eec9857e8a2076d3143769759f94c12b1eb405432af77833ba` `(3 paths)`
**Candidate patch:** `sha256:aa4e1f726ae908dfbfbb61c5ffe3ea0487eef68a414a2c2940249a20a7b42db1`
**Candidate bundle:** `C:\Users\TommySeery\AppData\Local\Temp\review\mS7RZPUPbus2bffhy8mjBa\_YeTVzK33S6Kc2uvp0OUDk\-uUcq6j1FS9jBAsrlWTq9z`
**Candidate bundle identity:** `sha256:279b64bcc4b2126a25c22b7415ffab0dfd685a12bc6bafaa3daf2f748ed4e3a2`
**Work-order path:** `reviews/Feature-RepositoryOwnedLayout.md`
**Work-order mode:** `append`
**Pass judgment:** `approved`

Selected lenses: native-general and workflow. No routed technical rule or security path selected.
Native review uses the available configured fallback at medium effort; the independent read-only
workflow lens uses the supported L4 fallback at high effort. Specialist unavailability was already
observed; no repeated unavailable dispatch is needed. This is local source preparation, with remote
base synchronization still held by the recorded permission decision. ALLOC1 remediation and its
19-test green focused run are complete. The fixing commit is `4fd86e3772b004022eb924e638215b2158271381`.

### Findings

No new findings. Native review completed successfully at the frozen head and found no defect.
Parent verified candidate hashes and unchanged authored files, and completed the bounded workflow
check against the frozen helper, tests and contract. Existing mappings remain intact; exclusions
precede restoration creation; exact mapping addition and subsequent fetch behavior are tested.

The independent workflow lens returned no findings. Its first envelope was malformed; one focused
format correction produced a schema-shaped result but did not bind every claim to the complete
dispatch immutable-artifact set. The dispatch is closed and contributes no formal acceptance; parent
fallback owns the bounded conclusion above. No further reviewer wave or candidate change occurred.
The earlier implementation lens also supplied useful cited source evidence without a schema-valid
Workflow v2 result; its no-findings return was not independent formal acceptance. That completed
pass retained the parent's real-Git ALLOC1 finding, and the current parent/native pass now verifies
the implemented correction. Earlier candidate identities and pass judgments remain unchanged.

Frozen docs reachability: zero errors/warnings. Plan graph, harness declarations, generated-tree check
and authored whitespace pass. The actual PR generated-path guard passes against locally observed main.
Current-main synchronization, reconciliation and delivery remain behind the explicit recorded fetch
permission gate; source approval alone is not final merge or installed-host acceptance.
