# Shared native work-item sessions: completed audit and reviewed design


## Existing implementation and compatibility

Core Machine owns `~/.agents-state/sessions.db`, honoring `AGENT_STATE_DIRECTORY`, in WAL mode. Audited schema version3 has `work_items` keyed by repository plus local feature/item, and `sessions` keyed by exact `host:native-session-id`. Sessions reference work items, permit many retained native handles per item, and enforce one owner with a partial unique index and transactional claim. Preserve exact keys, native handles, owner/predecessor/successor links and current recovery decisions.

`work_item_sessions.py` exposes `claim`, `status`, `find`, `resume`, `interrupted`, `end` and `item`; selectors currently require a local feature/item. Its supported handoff is a successor claim naming `--predecessor <exact-handle>`. `end --reason handed_off --successor <handle>` records session state. Do not set an unfinished item to done just to transfer ownership.

Recovery independently checks native history, liveness, checkout/head and observed receipts. Resume refuses live, foreign, unknown, stale, finished and handed-off sessions. Preserve these controls. PR295 retention intentionally removes eligible ended/dead sessions on completion, preserving the caller and live/foreign-running rows. Do not undo that policy or promise unlimited history.

Consumers requiring coordinated compatibility include:

- `.agents/machine/scripts/session_store.py` and `work_item_sessions.py`.
- `.agents/machine/utility/peer-cli/scripts/register_session.py`, `session_close.py`, and staged exit observers which copy store/identity helpers.
- `.agents/machine/utility/close/scripts/close_session.py` and `.agents/machine/scripts/agent_recovery.py`.
- `.agents/workflows/workflow_runtime.py`: `ReadOnlyWorkItemStore` accepts only versions2/3 and reconstructs local keys.
- Machine host hook manifests, `.agents/plugins/sources.json`, `.agents/plugins/harness/machine.json`, generated host adapters and session-store resources.

Use fresh main rather than overwriting newer root/registry fixes from the old tracker candidate. An empty isolated implementation checkout already exists: `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Feature-NativeWorkItemSessions`, branch `Feature/NativeWorkItemSessions`, allocated at281303c399046273be7b9d129daf8a9d4bde4d5b. No implementation writer or PR was assigned to it.

## Reviewed additive storage design

Keep the database and runtime in Core Machine. Do not move the database or create a second session store. Add schema version4 references:

```sql
CREATE TABLE work_item_references (
    provider TEXT NOT NULL,
    scope TEXT NOT NULL,
    native_id TEXT NOT NULL,
    work_item TEXT NOT NULL REFERENCES work_items(key),
    PRIMARY KEY (provider, scope, native_id)
);
CREATE INDEX work_item_references_item ON work_item_references(work_item);
```

Keep existing work-item keys unchanged. Permit `feature` and `item` to be both present or both null, enforcing that invariant. A new native-only execution uses an opaque `execution:<uuid>` key with null local labels. Never fabricate feature/item slugs from remote titles.

Canonical remote identity:

| Provider | Scope | Native ID |
| --- | --- | --- |
| `github` | `github.com/<lowercase-owner>/<lowercase-repository>` | Positive canonical decimal issue number |
| `azure-devops` | `dev.azure.com/<lowercase-organization>` | Positive canonical decimal work-item ID |

GitHub database IDs, GraphQL node IDs and Project item IDs are not issue identity. Exclude pull requests at the cloud adapter. Azure project is metadata rather than uniqueness: work-item IDs are organization-wide and project moves must preserve identity. Explicitly verified aliases may support repository renames/transfers; never infer aliases from titles or branches.

Cloud adapters enforce account, provider and repository policy. Core validates identity shape without remote calls or credentials. Execution home repository remains separate from remote scope; qualified lookup is global. A cross-repository agent joins the same execution/owner while retaining its own repository/cwd/branch session fields. Do not overwrite the home execution's branch or relative plan path when another repository joins it. Local execution status is not remote backlog status.

Reference registration is atomic and does not claim ownership. Explicit binding to an existing local selector or execution key uses `BEGIN IMMEDIATE`: refuse a missing target; treat the same reference/key as idempotent; refuse a reference bound elsewhere and report both identities; otherwise insert. Binding changes no sessions, owners, status or branch. Do not provide a blind force/merge. A native claim from a session attached to an unmatched legacy execution must direct an explicit bind, never silently detach it.

## Migration and rollout order

Publish readers before enabling version4 writers. Existing workflow readers reject a newer schema; running hooks may retain copied older readers even after source publication. Verify active-host adoption separately from source merge.

If rebuilding `work_items` for nullable local labels: disable foreign keys before beginning the transaction; begin immediate; re-read schema version under lock; create replacement, copy explicit columns, drop old table, rename replacement, recreate indexes/triggers, run foreign-key checks, set user_version4 and commit; restore foreign keys afterward. Do not rename the original table first because SQLite can retarget foreign-key references. Roll back every failure and refuse unknown future versions. Migration never guesses remote bindings.

Expose the public operation through Machine's existing `recover-agents` capability and a shipped skill-local `scripts/work_item_sessions.py` facade. Work Items declares its Machine dependency and composes qualified skills. Do not make another plugin import private cache-relative Machine files, query this database directly or depend on an unshipped local helper.

Retain existing CLI forms. Add mutually exclusive selectors: legacy feature/item, `--execution-key`, or the complete `--provider --scope --native-id` tuple. Status/resume lookups never create rows. Add execution key and structured reference to output; handle null labels explicitly in find/interrupted output, never `None/None`.

A Feature's direct attached sessions are Core's responsibility. Cloud profiles enumerate verified descendants for rollups. Do not add a second hierarchy/backlog table in the session store.

## Required meaningful checks

- Migrate version1/2/3 fixtures, preserve exact rows and handles, validate foreign keys/one-owner index, reconnect, roll back injected failures and refuse future versions.
- Verify concurrent native resolution creates one execution; binding is idempotent or conflict-visible and never changes ownership.
- Separate GitHub repositories and Azure organizations; preserve Azure identity across project metadata changes; normalize case and decimal IDs deliberately.
- Verify native-only null-label output and identical retained handles through both local and remote selectors.
- Preserve every ownership, helper, handoff, liveness and resume refusal, and unchanged PR295 retention outcomes.
- Verify version4 read-only workflow readers and staged observer consumers before writer rollout.
- Exercise shipped facades and dependency resolution on Windows/Linux, including spaces/non-ASCII paths and missing-Machine failures; prove personal/work account separation.

Focused suites: session store, work-item sessions, registration, finish, recovery, hook workflow contracts and harness manifests. Use source generation for local verification and leave generated distribution paths uncommitted.

## Completed GitHub provider audit

The inspected Work Items PR20 head9b2a2df1d8ff2a6c4968b39624cbdc683e33da07 extracts cloud record operations, not SQLite session storage. Preserve its reviewed candidate while reconciling scope.


Remaining personal source slices are six-kind representation/readback, native hierarchy, Project membership, typed fields/dates and roadmap views. GitHub supports programmatic roadmap view creation; do not repeat the earlier unsupported claim that this is UI-only. Existing prepared inventory has66 repositories and36 Project destinations: product boards for Concertable/TjAgents and one separate board plus roadmap for each independent personal repository. No catch-all Personal board.

