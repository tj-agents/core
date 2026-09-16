# Workflow v2 adapter, deck, and compatibility support matrix

This is the published support statement for contract `v2`. `compatibility.json` is its machine-checkable
half; `verify.py` fails when the two disagree.

## Contract versioning

The workflow contract versions independently of the plugin. Additive optional fields stay within a version.
A new required field, decision-boundary change, capability rename, result meaning, or provider operation
change opens a new version with its own row here. A host adapter declares every contract version it accepts,
so one installed plugin can serve two contract versions during a transition.

## Host adapters

Both adapters are `available-with-parent-fallback`: the host runs the bounded role when it can, and every
unsupported case is a typed fallback that executes the same bounded contract in the parent, never a silent
skip.

| Concern | Codex | Claude |
|---|---|---|
| Contract versions | `v2` | `v2` |
| Role delivery | project-scoped `.codex/agents`; plugin loading unsupported, so provisioning installs them per repository | plugin-loaded `agents/`, no per-project install |
| Semantic stage route declaration | `hosts/codex.json` | `hosts/claude.json` |
| Stage launch | native bounded role with an explicit routed model | native bounded role with an explicit routed model |
| Read-only enforcement | `sandbox_mode = read-only` | tool allowlist without `Write`, `Edit`, `Bash` |
| Parallel readers | supported | supported |
| Serialized writers | required, one repository lease | required, one repository lease |
| Nested dispatch | unavailable | unavailable |

An unavailable host, role, or model, an unsupported capability, an invalid result, or a cancellation are the
six declared fallback reasons. Both manifests carry all six, so neither host can quietly drop one.

Each host manifest declares only the task parameters for a semantic stage. The caller resolves those
parameters through the machine routing policy and passes the returned model, effort, and lane into host
preparation. Missing routing output is a contract violation, and generated roles carry no model default that
could conceal it. A missing implementation or mechanical model returns a typed same-stage parent fallback. A
missing strategic, review, or critical model pauses for a decision; it is never silently downgraded or
substituted across lanes.

Codex's skills context budget is shared across every installed plugin on the machine, and selection lives
entirely in skill descriptions, so an oversized roster shortens or drops them and degrades selection itself.
Install only the standards plugins a machine needs, and never route a parent session to the bounded-role
model — its budget is smaller still.

## Execution decks

A deck owns the outer task, worktree, and host session. It is optional and never a workflow-state API.

| Deck | Status | Required for |
|---|---|---|
| kandev | external, `native-cli-passthrough` | nothing — bare Claude and Codex CLIs are the supported baseline |

A deck that is absent, unavailable, or defective degrades to the bare-CLI path with no change to workflow
selection or semantics. Deck recovery defects belong to the deck's own plan, not to this contract.

## Compatibility entries and release gates

| Entry | Kind | Status | Replacement |
|---|---|---|---|
| `resume-plan` | compatibility entry | supported | `plan-execution` |
| `continue-roadmap` | compatibility entry | supported | `plan-authoring` |
| `big-review-all` | driver | retained | drives `big-review`; no removal gate |

The release letter in `compatibility.json` is the contraction gate. Release **A** publishes the new workflows
and thin entries. Release **B** may mark an entry `deprecated` once every standards-managed consumer has
migrated. Release **C** may remove one only after Release B is installed everywhere, a repository-wide
route, skill, and plan grep finds no remaining caller, and both host acceptance suites pass through the
replacement. One remaining caller keeps the entry for another published version. A driver has no removal
gate because it is not a wrapper over a retired name.
