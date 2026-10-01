# Workflow v2 transition, fallback, and gate contract

Only the executable task workflow chooses its next stage. The shared contract supplies record meanings and
validation; it never selects a task, triggers as a skill, or assumes workflow ownership.

## Semantic execution stages

The parent selects one model-independent stage from evidence and remains the workflow owner:

| Stage | Evidence |
|---|---|
| `strategic` | Ambiguous or high-level work, architecture, major planning, or cross-cutting diagnosis |
| `implementation` | Implementation, evidenced CI repair, debugging, focused testing, or coverage work |
| `mechanical` | Deterministic inventory, repetitive processing, or mechanical verification with no implementation judgment |
| `review` | An implementation-ready or pre-merge candidate requiring independent judgment |
| `critical` | Security, migration, irreversible, or otherwise high-risk decisions |

Critical evidence wins over every other signal. Ambiguous strategic evidence wins before implementation.
Review follows an implementation-ready candidate. Implementation judgment moves nominally mechanical work to
`implementation`. Host configuration resolves the selected stage through its ordered primary and fallback
model route. A fallback preserves the semantic stage, frozen evidence, role boundary, and fresh-context
requirement, and the invocation records both the primary and selected model. Protected stages may use only a
declared equivalent-or-stronger fallback; exhausting that route is a decision rather than a silent downgrade.
The parent does not silently change model in place. When a fixed specialist cannot launch the selected model,
the host starts its native general/default agent with the specialist role body and explicit selected model.
If a launch then fails for quota or capacity, the failed dispatch closes and a fresh dispatch advances to the
next declared model in that same stage. Exhausting a protected route pauses.

| Transition | Meaning |
|---|---|
| `continue` | Run the resolved safe, reversible next stage in the same workstream under existing authorization. |
| `retry` | Repeat one bounded stage after a correctable incomplete result or transient failure. |
| `fallback` | Cancel the dispatch and execute the same bounded contract in the parent. |
| `cancel` | Close the dispatch and ignore late or obsolete results. |
| `checkpoint` | Persist a material recovery transition in the owning plan, ledger, or review artifact. |
| `transfer` | Checkpoint and move ownership across a deliberate fresh-context boundary. |
| `pause` | Stop for a named human or external action with an observable resume condition. |
| `block` | Stop on an owned dependency with an objective unblock condition and reciprocal return path. |
| `complete` | Finish only when the workflow outcome and every required gate are terminal. |

Validate every subordinate result and its cited evidence before using it. A malformed or correctable
incomplete result gets at most one focused follow-up in the same bounded context. Agent unavailability,
timeout, cancellation, unsupported roles, or a second invalid result closes that dispatch and falls back to
the parent without changing its objective or authority.

A cancelled reader contributes no conclusions. Before another writer starts, a cancelled or failed writer
must report its partial paths or the parent must reconstruct them from Git and re-establish exclusive lease
ownership. Late results from a closed dispatch or an obsolete immutable baseline are ignored.

Human gates are limited to material product ambiguity, architecture or security choices without a safe
default, destructive work outside authorization, external-only actions, unresolved conflicting evidence,
required delivery authorization, or a deliberate context boundary. Every open gate names its owner, one
action, its evidence, and an observable resume condition.
