# Record installed workflow skill identities

## Outcome and authorization

Repair Core's workflow skill-identity recorder for consuming repositories using the installed shared lifecycle and routed skills. Both Claude and Codex must retain one canonical source, accurate loaded-body provenance, repository-local path safeguards, and ordinary review/delivery gates.

Authorization is engineering:session-guidance's standing consumed-standards-defect scope: diagnose, implement, test, review, open the source PR and merge after repository gates pass. No normal-profile installation, hook-trust bypass, arbitrary-file trust, security-policy bypass or copied Core lifecycle in consumers is authorized. The originating twelve-repository auto-merge rollout remains with its existing controller.

Repository: tj-agents/core. Branch: Fix/ExternalWorkflowSkillIdentities. Owning checkout: .worktrees/Fix-ExternalWorkflowSkillIdentities, based on published d747cbed6add80e57c5d0cbbac716dbd4502bf78. Only this isolated source workstream may change its paths; do not adopt other linked checkouts or active work.

## Observed defect and ownership

During C++ repository opt-in review, the installed workflow_ops.py skills command rejected the installed engineering review lifecycle with `skill paths must stay inside the repository`. Its skill_identities implementation prohibits absolute and escaping paths, defaults to the obsolete .agents/skills layout, and has no installed-plugin identity resolver. Canonical review Stage 4 requires recording the owning shared lifecycle and plugin-owned routed identities in every consuming repository. The C++ repository correctly contains no copy of Core's review lifecycle.

The installed canonical lifecycle was actually read and its SHA-256 was a0420bad26f5a73a5f3e318dd82201985b41eba4b913bded5465d115c97cb09a. That read is not a successful helper cache operation. Record actual source/hash provenance without falsifying `load` or `cached` results. The observed API capability gap is confirmed; the selected constrained mechanism below is complete. Candidate7b5d417 is checkpointed but parent acceptance found unresolved specification/test boundaries; it is not accepted or delivered.

Existing merge-worktree-cleanup progress records the older obsolete default path, with an objective resolution condition but no current isolated owner for this external-consumer defect. Link/reconcile that record rather than duplicate its wording or claim ownership of its historical checkout. Source owner for this bounded defect is .agents/workflows/workflow_ops.py and directly causal contracts/tests/manifests.

## Completion criteria

Repository-local bodies still reject traversal and unsafe external references. Authenticated installed shared lifecycle and plugin-owned routed skills have truthful stable identity/load/cache behavior for both hosts without copying guidance into consumers or modifying machine profiles. Tests cover actual consumer invocation, provenance changes and invalid source paths. Update the shipped harness manifest if capability requirements change. Run focused validation, independent ordinary and conditional security review, exact-head Windows/Linux CI, normal authorized merge, causal package publication, and owned checkout cleanup. Preserve unrelated settings, source owners and existing stop classes.

## Current state and transfer gate

Independent transfer has not been submitted or acknowledged. The originating controller retains Source/delivery and has an exclusive bounded L4 in-session implementation writer. This is not machine-handoff pickup. The packaged launcher unconditionally refreshes/reinstalls enabled plugins and establishes hook trust; no no-refresh option is documented, so the independent launcher remains capability-gated under the no-profile-mutation limit.

Gate type: capability/installation scope. Resolver: supported independent launcher with no profile mutation, or separately authorized profile maintenance. Observable resume condition: an available supported launcher preserves that limit and submits exactly one successor; acknowledgement in this Goal separately proves pickup. No elapsed-time inference or duplicate launch.

## Next Steps

The bounded L3 specification is selected. L4 checkpoint7b5d417 (636 insertions/43 deletions, eight authored/catalog paths) is incomplete at parent acceptance: native default-root containment, explicit Codex installed=false, bare-name installed compatibility, cross-marketplace ambiguity, lexical redirect rejection and truthful complete metadata/descriptor regressions require correction. The same writer retains its lease for one focused correction; parent owns Goal/BUGS/debt and will require complete acceptance before fresh ordinary/L2 security review, exact CI and normal delivery. The independent machine-transfer gate remains; no profile update or launcher pickup is claimed.

## Selected implementation contract

The source-backed L3 investigation is complete. Native enabled installation metadata is the authority to read its declared guidance; this metadata recorder does not grant hook trust or certify a remote publisher. No new allowlist, Git/network authentication or normal-profile mutation is introduced. Preserve existing identity-cache load/cached semantics and actual caller body reads; no loaded-body receipt API is added.

### References

- Preserve explicit name=repository-relative-path exactly as a local-only input. It never selects the installed branch and continues rejecting absolute, drive-relative, UNC, traversal and resolved escapes.
- A plugin-qualified plugin:skill without = selects the installed branch. It must resolve to one enabled applicable native installation across marketplaces. Requested name remains separate from resolved identity so exact direct-route comparison remains meaningful.
- For backward-compatible bare names: use an existing local legacy .agents/skills/<name>/SKILL.md first; otherwise a unique local canonical owner/kind body; otherwise a unique installed declared skill for the explicit host. No first-installed or first-glob winner. The review instructions explicitly pass engineering:review so a consumer-local review file cannot shadow the owning installed lifecycle.
- Local canonical discovery stays inside the repository. Use declared local sources.json scope roots when present, validating every root's containment, or the known .agents/<owner>/<kind>/<name>/SKILL.md shape. Require matching public name metadata and uniqueness; do not follow arbitrary prose links or outside roots.
- Use the existing shipped one-hop compatibility map only after the direct qualified identity is absent. Do not follow chains, arbitrary consumer alias files or alias paths. Record requested_name, resolved_name and alias_from separately.

### Native authority

- Run the existing native plugin list --json command for an explicit host in the original consumer repository cwd and active profile environment. Add that cwd to the inventory cache key. Do not query from the exported review tree, which can change project-scoped enablement.
- Codex: accept enabled records from the native installed list, reject installed=false, parse pluginId or name+marketplaceName consistently, require a safe version path segment, and derive the cache root from active CODEX_HOME/default profile plus marketplace/name/version. Do not treat source.path as the installed root; it can name marketplace source files.
- Claude: require enabled records with a consistent id=name@marketplace and native installPath. Retain scope. Reject explicitly unrelated projectPath records; project/local scope must provide an applicable projectPath. User/managed scope is applicable. Prefer the uniquely most specific applicable scope within one plugin ID; equal-rank different locations and same plugin name across marketplaces are errors. An omitted scope can be recorded as native-effective only when returned by this host query for the original cwd; do not invent a user-scope claim.
- When Codex does not return a separate scope field, record native-effective scope plus the queried project context rather than guessing it. Retain any actual scope/project metadata the host supplies and reject contradictory explicit metadata.
- Enabled native installation is the authority to read that package's declared guidance. It is not proof of remote publisher authenticity, a clean checkout or package-wide integrity. Report native source/version/revision fields only if present, clearly as advertised metadata.
- Missing binary, timeout, malformed inventory, disabled/missing owner, ambiguous candidate or stale cache-only body fails clearly. No linked-home, own-payload, cache glob, installed-registry-only or alternate-host fallback.

### Package paths

- Inspect only the selected installation root's host manifest (.codex-plugin/plugin.json or .claude-plugin/plugin.json; retain an existing legacy root plugin.json if unambiguous). A manifest-declared name must match the native plugin name. Keep native version and manifest version as distinct reported fields; Claude can use a revision-like native version.
- Use manifest skills roots: a relative string or list of relative declared skill-directory roots. If absent, use the host's conventional skills/ directory and mark declaration_method=native-default. Do not infer codex-skills/ merely from the host; Core explicitly declares that custom directory.
- Reject an absolute/URI/escaping declared skills root, duplicate conflicting declarations and roots with redirected path components. Locate exactly the requested bare name's SKILL.md beneath those declared roots. Multiple distinct matches are ambiguous; directory scanning outside declared roots is forbidden.
- Read the declared entry bytes once and hash the exact raw bytes. Recognize only the existing generated canonical-shared-definition link marker. Zero such links means the declared entry is the body; exactly one means resolve that contained target; more than one, an absent target or an unsafe target is an error.
- For the generated canonical link, relative .. components are permitted only when lexical normalization stays inside the same selected package. Reject drive/UNC/URI references and normalize before reading; then lstat package root and each contained target component, rejecting POSIX symlinks and Windows reparse/junction redirections. Do not recursively follow arbitrary Markdown links or links into another installed package.
- Read canonical bytes once and hash those raw bytes. Emit metadata only; do not import/execute package-supplied Python or return its body as a new loader feature. The actual read path in the result names the canonical file, not merely the thin host wrapper.
- Package-root location originates solely from the native host record/cache convention, never from user-supplied absolute path arguments. Validating paths beneath that declared root does not grant authority to an unrelated outside file.

### Record

```json
{
  "common": [
    "kind",
    "name (requested route/lifecycle identifier)",
    "resolved_name",
    "source_type (repository_local|installed_plugin)",
    "path (repository-relative or package-relative actual body path)",
    "sha256 (exact raw body bytes)"
  ],
  "installed": [
    "host",
    "plugin_id (name@marketplace)",
    "marketplace",
    "native_version",
    "native_scope and applicable project metadata",
    "advertised_source metadata when supplied, otherwise null",
    "declaration_method",
    "manifest_path/hash when present",
    "entry_path and entry_sha256",
    "body_path and body_sha256",
    "resolved_path and package_root as current diagnostic/read locations",
    "alias_from when used"
  ],
  "truthful_provenance": "Do not label publisher/commit metadata verified or authenticated. No verified_source_commit field is synthesized. Actual raw entry/body hashes identify the bytes observed; they do not certify who published them.",
  "stable_identity": "For installed sources, compare kind, resolved plugin/skill identity, host, native version/scope, normalized advertised-source metadata, declared manifest/entry/body relative paths and their raw hashes. Exclude diagnostic package_root/resolved_path. A location-only relocation with equal source identity/bytes reuses cached; changed identity or bytes returns load. For local sources keep the existing kind/name/path/raw-hash comparison.",
  "action": "load/cached retains its current identity-record meaning. Cached is valid only for the same complete identity already in this logical workflow's skills.json. Legacy local records remain compatible; legacy records without the newly required installed fields cannot establish an installed cache hit. Workflow body reading stays with the caller."
}
```

### Frozen review

- Keep existing local rules for exported-tree bodies; add installed_rules and skill_resolution_context fields to new descriptors. installed_rules contains stable installed identities, not mutable diagnostic absolute paths.
- review-prepare resolves every directly routed installed rule using the original consumer's host/scope, hashes its contained body, and freezes that identity in the descriptor before descriptor_id and identity.json are written. Add installed_rules to expected_identity and the initial manifest; descriptor_identity already includes new fields.
- Add --host to review-prepare and skills, optional for local-only invocations but required whenever installed resolution is needed. Add --descriptor to skills for canonical review. With it, derive expected routes from the validated frozen descriptor, local bodies from its exported tree, and installed records from its pinned installed_rules. Reject supplied --technical/--changed-path values that contradict the descriptor rather than routing live checkout paths.
- load_descriptor and restored-bundle validation verify the descriptor/manifest pins and re-resolve installed identities in the stored explicit host against the original consumer cwd. Native inventory is refreshed in each new helper process. Changed, removed, disabled, ambiguous or redirected installed guidance raises a clear 'installed rule identity changed; start a fresh review run' error. Never mutate existing pinned evidence or silently substitute the latest plugin.
- Legacy descriptors with only local/no routes remain supported. A legacy descriptor containing installed routes without installed_rules must be re-prepared under a new logical review run; it cannot claim pinned external hashes.
- review_reconcile keeps local Git-path sensitivity logic over rules only. installed_rules are validated as their own provenance/hash evidence, not added as external paths to Git base-path intersections.
- Stage 4 calls skills with the descriptor and explicit host, records engineering:review plus exactly the pinned route identities, and reads actual body paths only on load. No copying installed bodies into the candidate tree or consumer.

### Subprocess boundary

```json
"Inventory is the only added read-only subprocess use. Reuse the router's UTF-8 JSON, 8-second timeout, argument-list/shell=False behavior and Windows hidden process flag. Do not invoke a profile-refresh launcher/wrapper, apply bootstrap, plugin add/install/update/enable, Git/network publication verification, hooks/trust writes or package-supplied executable code."
```

## Specified execution boundary

L4: implement the selected resolver, truthful native metadata/cache identity and pinned installed review evidence with focused cross-platform regressions. Source ownership is limited to the listed helper/router, canonical review/efficiency guidance, directly causal tests and a shipped harness manifest only if requirements change. No consumer source or profiles may change. Keep one writer, inspect branch size before expanding around1000 substantive lines, and return for parent acceptance, independent ordinary/L2 security review and exact CI. Original controller owns Goal/BUGS/debt reconciliation and all delivery. The independent machine launcher remains capability-gated; no submission/pickup is claimed.

### Concrete APIs

```json
[
  {
    "file": ".agents/hooks/skill_router.py",
    "add": "native_plugin_inventory(harness, project_root=None) -> list[dict]",
    "behavior": "Factor the bounded existing query/JSON validation into a reusable raw-record API keyed by explicit host and normalized project cwd. Existing _native_install_roots calls it and retains its existing root-only lookup behavior for existing router callers. Additive refactor only; do not change skill_search_dirs or resolved_skill semantics.",
    "error": "Preserve NativePluginDiscoveryError diagnostics for missing CLI, timeout, nonzero result, invalid JSON/roster."
  },
  {
    "file": ".agents/workflows/skill_sources.py (new)",
    "add": [
      "resolve_skill(reference, repository_root, local_body_root, host=None) -> identity dict",
      "resolve_installed_skill(plugin, bare_name, host, project_root, inventory) -> identity dict",
      "identity_key(record) -> stable comparable tuple or canonical digest",
      "validate_pinned_installed_rules(records, host, project_root) -> None"
    ],
    "behavior": "Own strict reference/name/native-record normalization, scope/ambiguity selection, manifest-declared entry lookup, contained canonical target validation, redirect checks and exact-byte hashes. Reuse the shipped router raw inventory/one-hop alias map via the same package's sibling hooks directory, never a module from the consumer or selected guidance package. Construct one inventory snapshot per host/project per helper invocation.",
    "errors": "Raise a resolver-specific error converted by workflow_ops into WorkflowOperationError; report requested identity and reason without silently falling back."
  },
  {
    "file": ".agents/workflows/workflow_ops.py",
    "modify": [
      "skill_identities(root, workflow_run_id, lifecycle, technical, changed_paths=(), host=None, descriptor=None): preserve existing positional callers; use strict resolver and identity_key; retain skills.json/event writes and load/cached directives.",
      "review_prepare(root, workflow_run_id, base_ref, head_ref, synchronize, host=None): preserve local-only calls; freeze installed_rules and stored host/project context when required.",
      "parser/main: add choices --host codex|claude to skills/review-prepare and --descriptor to skills; pass them through.",
      "expected_identity, initial identity.json, both descriptor validation/recovery paths: bind/validate optional installed_rules consistently, require reprepare for unpinned legacy installed routes.",
      "review_reconcile: surface installed identity drift through existing descriptor validation; keep its local-path intersection unchanged."
    ]
  }
]
```

### Causal source files and regressions

```json
{
  "files": [
    {
      "path": ".agents/hooks/skill_router.py",
      "work": "Raw native inventory factoring; no discovery-policy expansion."
    },
    {
      "path": ".agents/workflows/skill_sources.py (new)",
      "work": "Strict generic local/installed metadata and contained body resolver."
    },
    {
      "path": ".agents/workflows/workflow_ops.py",
      "work": "Resolution/cache keys, explicit host/descriptor options and pinned installed review rules."
    },
    {
      "path": ".agents/engineering/workflow/review/SKILL.md",
      "work": "Stage 1 passes host when resolving installed routes; Stage 4 uses explicit host, descriptor and engineering:review, and actual returned canonical body paths."
    },
    {
      "path": ".agents/workflows/efficiency.md",
      "work": "Describe identity caching and installed provenance accurately; avoid adding a body-read receipt claim."
    },
    {
      "path": ".agents/plugins/harness/engineering.json",
      "work": "Record any changed approval-bearing documented workflow invocation/prerequisite under its existing manifest contract. The internal inventory capability already ships in engineering's router; do not add trust/install/network grants or broad shell permissions. If no capability requirement changes, this file needs no change; verify with its tests."
    },
    {
      "path": ".agents/hooks/tests/test_skill_router.py",
      "work": "Pin raw-record API and host/original-cwd isolation while preserving existing linked/own/alias callers."
    },
    {
      "path": ".agents/hooks/tests/test_workflow_ops.py",
      "work": "Pin local compatibility, new installed identity/cache behavior and descriptor installed-rule integrity."
    },
    {
      "path": "tests/test_workflow_skill_sources.py (new)",
      "work": "Strict metadata/path/scope/canonical resolution tests over disposable enabled host inventories."
    },
    {
      "path": "tests/test_review_native_layer.py",
      "work": "Actual generated workflow CLI against disposable consumers for both hosts."
    },
    {
      "path": "tests/test_source_layout.py and tests/test_harness_manifests.py",
      "work": "Package closure and declared invocation coverage."
    }
  ],
  "regressions": [
    {
      "case": "Generated consumer invocation",
      "assertion": "Generate engineering into a disposable package, advertise it via fake native CLI/profile fixtures, and invoke its actual workflow_ops CLI from a separate cwd against a consumer with no local lifecycle/runtime. For both hosts skills --host <host> --lifecycle engineering:review returns the exact canonical raw hash and path, enabled plugin ID/version/scope and separate entry hash. No remote/publisher authentication is required."
    },
    {
      "case": "Generic publisher and metadata truth",
      "assertion": "An enabled package under an arbitrary marketplace/publisher resolves normally. Missing source URL/commit stays null; supplied source metadata is reported without verified claims. Marketplace name never becomes an invented GitHub owner. Local source or absent remote access is not rejected merely for failing unrelated trust activation policy."
    },
    {
      "case": "Host/context scope",
      "assertion": "Inventory call uses original consumer cwd even when local routing/body reads use a temporary frozen tree. Respect explicit host/profile, user/managed and applicable project/local scope; refuse wrong-project metadata, ambiguous equal scope and same plugin across marketplaces. Calls for different host/project do not share cached inventory."
    },
    {
      "case": "Disabled/stale refusal",
      "assertion": "Disabled or installed=false records never resolve. A readable stale cache, installed registry record without native enablement, linked-home body or own-package body absent from the selected enabled roster cannot rescue a failed installed lookup. Missing CLI, timeout, malformed/invalid roster is a visible error."
    },
    {
      "case": "Manifest and canonical mapping",
      "assertion": "Resolve Core Claude skills and Codex codex-skills declared roots to the same canonical hash while preserving different entry hashes. Cover generic declared directory/list roots, conventional skills default, full-body legacy entry, one contained ../.. canonical link, and one-hop shipped alias with requested and resolved names separate."
    },
    {
      "case": "Local compatibility",
      "assertion": "Existing name=relative-path and legacy bare flat bodies keep working without --host. Add unique canonical owner/kind local source coverage. Absolute/UNC/drive-relative/traversal and resolved external local references remain rejected. Installed branch is selected only by identity, never by external path."
    },
    {
      "case": "Boundary attacks",
      "assertion": "Reject separator/drive/.. names or native cache segments, escaping manifest roots, conflicting declarations, duplicate skill matches, unsafe/URI/absolute canonical links, multiple canonical targets, missing target, POSIX symlink and Windows junction/reparse root or contained target components. No guidance package Python is imported."
    },
    {
      "case": "Identity/cache semantics",
      "assertion": "First complete identity returns load; unchanged second call returns cached under existing semantics. Changed native version/scope/source metadata, manifest/entry/canonical path/hash returns load. Package relocation alone with unchanged identity/bytes preserves cached and updates diagnostic read location. Raw LF/CRLF changes are recorded as actual byte changes."
    },
    {
      "case": "Pinned review evidence",
      "assertion": "A frozen consumer route names both a local body and a second generic installed plugin. review-prepare pins local rules plus installed_rules in descriptor/identity manifest. skills --descriptor derives routes and local bodies from the frozen tree, refuses contradicting technical/path input, and detects live candidate/body changes correctly."
    },
    {
      "case": "Drift, recovery and old records",
      "assertion": "Tampering installed_rules or identity manifest fails validation. Installed body/version/source/enablement drift before resume requires a fresh review run, without updating the old pin. Both recovery/normal descriptor branches enforce this. Local-only legacy descriptors remain valid; legacy installed-route descriptors missing pins require reprepare."
    },
    {
      "case": "No trust/profile/network side effects",
      "assertion": "Record all subprocesses/files written in disposable fixtures. Only bounded native inventory queries and ordinary existing workflow-private metadata writes occur; no Git/network publication check, add/install/update/enable, launcher/profile sync, trust write, remote fetch or copied skill appears."
    },
    {
      "case": "Cross-platform closure",
      "assertion": "Run Windows/Linux cases with spaces/non-ASCII paths, real Windows junction when supported and Linux symlink equivalent. Verify generated helper/router/runtime closure and host manifests. Existing router own/linked/native/alias tests and unaffected local workflow tests still pass."
    }
  ]
}
```

Next executable action: bounded L4 Source implementation under the original controller; the earlier read-only Next Steps is completed. Complete this source workstream through review/CI/normal merge/causal publication/owned cleanup without adopting or closing the originating rollout.

## Split reassessment before acceptance correction — 2026-10-12

Immutable checkpoint7b5d417 is preserved at published base d747. Current scope is eight authored/catalog paths,636 insertions/43 deletions; generated payloads are separate and unstaged. The corrected native selection/path boundary and previously specified consumer/descriptor regressions project another350–500 substantive changed lines, taking this atomic repair to1029–1179 before final measurement. Parent accepts a bounded exception up to1500 substantive added/deleted lines for this cutover; above that requires a new assessment before expansion. Maintained Goal/BUGS/debt, command-reference guidance and generated packages are reported separately, with full totals retained.

Rejected boundary: publishing only an unused resolver foundation creates a dormant API while the actual workflow still rejects installed bodies; publishing CLI selection without descriptor pin/load/restore validation exposes mismatched guidance provenance. Splitting either host leaves one host's current consumer contract unqualified. Separating required path/enablement/ambiguity regressions leaves the same new native-file read boundary unproven. The changed command references are callers of this same API and cannot precede its availability. Independent generic guidance, trust policy, installation behavior and new body-receipt APIs remain out of scope. This exception is based on the API/descriptor/caller integrity boundary and required qualifying regressions, not the existing branch or sunk implementation.

Validation gate: real fixture-native inventory subprocess from the original separate consumer cwd for both hosts; generated-package helper invocation; mixed local/installed frozen review creation, load, reconciliation and missing-bundle restore; changed body/version/enablement/context refusal; default roots/canonical wrappers/alias identity; ambiguity and disabled/stale cache; lexical symlink/junction and escaping metadata rejection; stable raw-byte/cache identity including relocated equivalent package; unchanged native router callers. Parent independently reads the complete code/results, then fresh general and security lenses cover the exact committed candidate, followed by exact-head Windows/Linux CI and causal package publication. No source completion or installed activation is claimed by the initial five-test result.
