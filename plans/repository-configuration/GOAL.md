# Repository configuration and guarded auto-merge preferences

## Outcome and authority

Deliver one atomic Core source change for the accepted version-1 repository configuration envelope and every existing auto-merge preference consumer. The source change adds a strict reusable reader, a Core policy resolver, consumer migration, schema and operational documentation, and the required package mappings and harness declarations. It preserves the existing guarded command and authorization contract. The shared selected design is [the immutable configuration design](https://github.com/tj-agents/docs/blob/0d74933ff0889251f6228c96d81b7553ed95a736/plans/tj-agents-auto-merge/PLAN.md#selected-repository-configuration-design); this Goal records the current Core API map and decisions needed to implement it without relying on scratch artifacts.

Tommy authorized reviewed both-host source delivery and eventual opt-in in the twelve authorized tj-agents repositories. This Core slice does not edit or activate `.agents/configuration.json` in a repository, modify authorization policy, install into normal profiles, enable Concertable, pay or bypass billing, change review/protection controls, or adopt another owner's PR or checkout. Kit support and the twelve-repository adoption happen only after Core is published and under their explicit adoption gates. Root retains the global rollout and parent Goal.

## Execution readiness

Verdict: ready
Execution authorization: implementation
Transfer: no critical native-owner transfer is required for the bounded L4 lane
Receipt: none; Root checkpoints this Goal before dispatching the source writer

Readiness authorizes only the listed Core source change. It does not authorize a PR before Root review, normal-profile installation, billing or protection bypass, or repository adoption.

## Current source and API map

This Goal is on fresh Core branch `Feature/RepositoryConfiguration`, based at `86e9b1dedfdf5ab16f52c0e8da05d7d61343dee1`. The former `Feature/ConfigurableAutoMerge` checkout remains preserved and unadopted; do not modify or clean it up.

At this base, `.agents/workflows/delivery_policy.py` already owns strict `validate(policy)` and `PolicyViolation`, including strict legacy `auto_merge` bool validation and all five `authorized_stop_classes` rules. `.agents/workflows/delivery_runtime.py` duplicates much of that validation in `StandingMergeAuthorization.validate_policy`; remove the duplication by calling the canonical validator while preserving its public contract and error behavior. Its `resolve(policy, changed_paths, labels)` currently reads the legacy preference. `.agents/workflows/workflow_ops.py:standing_authorization` reads and resolves standing authority. `.agents/workflows/auto_merge.py` already consumes a fresh resolution; do not add another reader or alter its fixed guarded command.

The actual preference consumers are `.agents/hooks/delivery_binding_gate.py:auto_merge_enabled`, `.agents/machine/utility/bootstrap-capabilities/scripts/harness_permissions_sync.py:auto_merge_enabled`, and `StandingMergeAuthorization.resolve`. Route all through the shared policy resolver. Hook permission rendering still requires present, fully validated authority; invalid configuration denies grants and diagnoses/removes prior conditional grants. Preserve standing authorization, scoped authorization, holds, all five stop classes, review/check gates, and fixed guarded-command behavior. `workflow_ops` composes the effective preference with its fresh authority result; a preference never grants authority.

Add `.agents/workflows/repository_configuration.py`, a Python standard-library reader loaded relative to `delivery_policy.py` so `importlib.util.spec_from_file_location` loading by the machine consumer works. `load(root)` receives only the caller's actual absolute checkout root and distinguishes absent configuration from an invalid present path. Read only `<root>/.agents/configuration.json`; no ancestor, git common-directory, profile, environment, repository allowlist, or plugin lookup. The exact envelope contains `schema_version` and `configuration`; version is actual integer `1`, excluding bool. Namespace names match `^[a-z][a-z0-9-]*$`, values are objects, and well-formed future namespace objects remain opaque and unchanged. Reject duplicate nested keys, malformed/unreadable files, dangling links/directories, non-JSON constants, and non-finite overflow such as `1e999`.

Add `.agents/schemas/repository-configuration.schema.json` for the open envelope, without Core-private fields. Core consumes only its `core` namespace and strict boolean `auto_merge`; unknown Core keys are errors. With the new file present, missing `core` or `auto_merge` resolves false, and false cannot be overridden by legacy true. Only when the new file is wholly absent may the fully validated legacy authority file provide its strict `auto_merge` bool; invalid-present configuration never falls back. The resolver preserves the full `authorized_stop_classes` validation when extracting canonical validation. Mark `.agents/configuration.json` as non-exemptible standing-authorization-sensitive work and add it to `.agents/hooks/merge_review_gate.py`'s generic security patterns, so changing the opt-in cannot authorize its own PR.

Package the shared reader for the machine consumer through `.agents/plugins/sources.json` as machine-owned resource `resources/machine/scripts/repository_configuration.py`, beside the existing `delivery_policy.py` resource. The engineering package already maps `.agents/workflows/**`; do not add cross-plugin runtime imports, a marketplace, auto-install, new permission, or package cycle. Update the actual machine harness declarations and their validation/generated harness representation on both hosts as required by packaging checks. Do not add permissions unless the reviewed source and shipped harness schema prove they are needed.

## Owned source paths

The atomic implementation owns:

- `.agents/workflows/repository_configuration.py`
- `.agents/schemas/repository-configuration.schema.json`
- `.agents/workflows/delivery_policy.py`
- `.agents/workflows/delivery_runtime.py`
- `.agents/workflows/workflow_ops.py`
- `.agents/hooks/delivery_binding_gate.py`
- `.agents/hooks/merge_review_gate.py`
- `.agents/machine/utility/bootstrap-capabilities/scripts/harness_permissions_sync.py`
- `.agents/plugins/sources.json`
- `.agents/catalog/catalog.json` as required authored catalog inventory/digest output from the existing manifest and package lifecycle
- `.agents/engineering/policy/persistent-delivery/SKILL.md`
- `README.md`
- `docs/workflows/REPOSITORY_CONFIGURATION.md`
- `.agents/hooks/tests/test_repository_configuration.py` and only the affected existing tests: `test_delivery_runtime.py`, `test_delivery_binding_gate.py`, `test_auto_merge.py`, `test_merge_review_gate.py`, `tests/test_harness_permissions_sync.py`, `tests/test_harness_manifests.py`, `tests/test_source_layout.py`
- `.agents/plugins/harness/machine.json` and `.agents/plugins/harness/engineering.json` only as required by the existing harness validator and reader resource mapping
- this Goal

Do not edit `auto_merge.py` unless implementation discovers a concrete missing-consumer defect; it already consumes the fresh resolution. Any extra source path requires parent review before expansion. No Kit files, generated `plugins/*`, marketplace output, or repository adoption configuration belongs in this Core PR.

## Acceptance and verification

Add meaningful Windows and Linux tests, including paths with spaces and Unicode, for absent versus invalid-present configuration; actual integer version; exact envelope keys; namespace syntax/object values and opaque preservation; duplicate nested keys, malformed/unreadable/directory/dangling paths, non-finite values and `1e999`; strict core bool and unknown keys; authoritative false/missing-core behavior versus absent-only fully validated legacy fallback; all five stop classes; current hook and harness denial/removal behavior; and machine-loaded `delivery_policy.py` resolving its sibling reader from the packaged resource layout. Assert legacy authority, holds, scope, guarded command, fresh revalidation and authorization-sensitive classification remain enforced.

Verify schema and docs against runtime; exercise both authored source and copied machine-resource consumer on Windows and Linux. Use `python` on Windows and `python3` on Linux/macOS for Python checks. Run focused affected tests, both full Python unittest discovery commands from `.github/workflows/ci.yml`, `python -B scripts/sync_harness_manifests.py --check`, source-layout/package checks, `python -B scripts/update_catalog_digests.py`, then `pwsh .agents/sync-generated.ps1 -Check`. Local generation may refresh `plugins/*` and host output for tests; leave all derived output uncommitted. The authored `.agents/catalog/catalog.json` synchronization remains in the reviewed source change when required by the manifest/package lifecycle; never include generated `plugins/*` in the Source PR. Measure changed source, tests, and Goal before the 1,000-line trigger; if reached, stop and reassess the readable atomic scope with Root rather than compressing or dropping coverage. Source tests prove neither installed-host activation nor repository adoption.

After implementation, release to Root for exact review before any PR. Delivery remains independent review, required Windows/Linux CI, normal merge, causal generated publication, and safe cleanup of this checkout. Only the published Core result can unblock the separate Kit support and later twelve-repository opt-in. No native installation is part of this Goal.

## Host coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": "Core authored Python policy reader and consumers under .agents/",
  "hosts": [
    {
      "host": "claude",
      "behavior": "The shared configuration reader and guarded preference consumers are planned to use the same Core implementation.",
      "source": "planned Core atomic change; implementation and tests have not started.",
      "mapping": "planned engineering workflow mapping and machine-owned reader resource declaration; verify packaged copy after generation.",
      "verification": {"level": "planned", "result": "pending", "evidence": "Required Windows and Linux CI, source/resource parity, and both-host machine harness validation have not run."}
    },
    {
      "host": "codex",
      "behavior": "The shared configuration reader and guarded preference consumers are planned to use the same Core implementation.",
      "source": "planned Core atomic change; implementation and tests have not started.",
      "mapping": "planned engineering workflow mapping and machine-owned reader resource declaration; verify packaged copy after generation.",
      "verification": {"level": "planned", "result": "pending", "evidence": "Required Windows and Linux CI, source/resource parity, and both-host machine harness validation have not run."}
    }
  ]
}
```

## Next Steps

1. Root checkpoints and publishes this Goal before source implementation. Dispatch one bounded L4 writer on this fresh branch; no critical native-owner transfer is required for this source lane.
2. The writer reads current instructions and source state, implements this one atomic Core slice, runs meaningful focused/full checks and generation/harness validation, measures changed lines before 1,000, and updates this Goal with evidence. Do not claim generated output, installed activation, or consumer adoption.
3. Release the source checkout to Root for exact review. Do not open a PR until Root records review; then complete independent review, required Windows/Linux CI, normal merge, causal publication and safe cleanup.
4. Continue the separately owned Kit support and authorized twelve-repository adoption only after the Core publication and their explicit gates.

## Current rollout ownership and reconciliation

Root's parent rollout remains active. The prior configuration source checkout and its ownership are preserved; this new branch is an isolated authorized follow-on, not adoption of the former owner. Latest read-only native evidence reports association owner state WAITING, foreground and child null, deadline `1791803662.918` (approximately October 12), and launches/failures zero. The actual native Codex metadata reports SID `01a12aa7-5b58-7312-9400-ef710762147f`, PID `5896`, creation identity `134361905721115133`, while the active transfer receipt still names heartbeat SID `01a12745-ab05-7d12-8a0c-0d6bfc04ee41`; receipt identity is unverified. Its owner checkpoint is paused pending an owner-supported correction to the catalog-sync scope: catalog digest synchronization is required by the existing authorized manifest/source lifecycle, although the current seven-path boundary omits `.agents/catalog/catalog.json`. Root must not adopt or self-repair the association Goal or receipt. The current app-server session cannot perform the supported native follow-up; no retry, replacement launch, daemon, or send was performed. Preserve these gates until the owner corrects the scope and native reconciliation is available.
