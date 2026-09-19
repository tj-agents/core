---
name: session-guidance
description: Session guidance for an explicitly selected engineering lifecycle, including workflow ownership, staged skill loading, repair responsibility and authorized delivery continuity.
kind: contract
domain: process
---

# Selected engineering session guidance

These conventions apply when engineering is selected for the current scope. They do not grant
implementation, publication or installation authority. Product profiles and compatibility policy remain
with the project. The common maintained-plan contract is `base:plan-artifacts`.

## A task has an owning lifecycle — load it before the first edit

Authorized long-term or multi-phase work selects `engineering:plan-execution`, even when the user does
not name a plan or skill. Read an existing canonical goal before edits and keep its progress current.
A bounded behavior change selects `engineering:feature`; a defect selects `engineering:bugfix`.
Planning-only work selects `engineering:plan-authoring` and does not authorize implementation.
A question or review request alone grants no implementation authority. A status question during already
authorized execution should be answered before that execution continues.

## A link to another skill is a stage pointer, not a read

Load a referenced skill when its stage is actually entered, never because a document you are reading names
it. A procedure step, table row or route line says which skill owns that stage. Do not load the corpus
transitively. Use the host's native skill invocation when available or read its advertised source file.

## Preserve one owner through completion

Act on authorized reversible work and keep the canonical plan aligned with observed results. A phase,
commit, open PR or context boundary does not narrow the original scope. Honor user limits and real
external-action gates. Use `engineering:handoff` for an actual authorized context transfer; it checkpoints
first, invokes one selected machine launcher, and releases the previous writer. Prompt-only requests
remain prompt-only. Missing runtime capabilities must be reported accurately, not assumed installed.

Follow `engineering:committing` for local checkpoints and the repository's selected delivery convention
when delivery is authorized. Bind remote monitoring to the exact repository, head and run; never imply
pending CI is owned without an active monitor. A failed test selects `engineering:failing-tests` and its
diagnose, repair and focused verification loop. Do not weaken a check merely to produce a pass.

## Maintain the right source owner

Give shared behavior one source owner, preserve published compatibility commitments, and record material
out-of-scope defects with an objective resolution condition in the existing project's debt or plan owner.
Before committing or returning a terminal result, reconcile every problem encountered: it is fixed or
already has the owning debt entry. `engineering:docs-and-debt` defines the selected repository convention.
Do not create a second ledger for a standalone goal just to satisfy a repository-oriented procedure.
