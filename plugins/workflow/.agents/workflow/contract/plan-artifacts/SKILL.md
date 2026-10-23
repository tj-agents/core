---
name: plan-artifacts
description: Maintain one canonical Markdown plan or goal artifact for substantive work, with current recovery evidence and host-coverage records where applicable. Use when creating, revising, recovering, or reporting a substantive plan.
kind: contract
domain: process
---

# Maintained plan artifacts

For substantive planning intended for execution, write an actual Markdown artifact before presenting the
plan as ready. A repository plan follows the repository's declared plans or docs convention, or defaults to
`plans/<goal>/`; the active delivery checkout owns current planning state. Promote a host-scratch draft into
that owner before execution or handoff, preserving decisions and progress and verifying recovery references
resolve to the promoted copy. A standalone task keeps its task-directory goal and needs no repository,
roadmap, companion ledger, provider, pull request, or publication. Quick answers and one-step work do not
need a ceremonial plan.

Whenever creating, revising, or resuming a plan, include its exact absolute path as a clickable Markdown link
in the response, including a fresh-session progress summary. A bare filename or relative link is insufficient.
Keep the response aligned with the saved artifact.

Keep one canonical file. Apply corrections to its scope, decisions, sequence, and acceptance directly; do not
maintain competing copies or ask the user to splice replacement paragraphs. If the user names an existing
plan, read it before changing it and resolve ambiguous ownership before creating another. The optional
template is a starting point, not a required format.

Keep current progress, useful verification evidence, unresolved decisions, and remaining work in the canonical
plan or its existing project-owned progress artifact. Before resuming, read those artifacts and reconcile them
with available evidence. Checkpoint a material milestone, changed blocker or owner, deliberate transfer,
or context ending with unreconstructable partial state. Retain enough next-step context for another session
to act; routine observations need no checkpoint. Do not claim unobserved work or passed tests.

Planning grants no implementation, publication, installation, or other authority outside the request or a
standing authorization. Record authorized scope separately from proposed steps. Finish a planning outcome with
the concrete proposal, any decision genuinely still required, and the first action that follows it. If
execution is already authorized, `workflow:run` owns continuing it; this contract does not emit context or
own execution routing.

For a selected Engineering lifecycle, `engineering:plans` owns repository provider, plan graph, ledger,
review, delivery, and selected-item extensions. Generic artifact care remains valid without those capabilities.

## Agent-host coverage

An agent-behavior plan, fix, or review has exactly one fenced `agent-host-coverage` JSON object. It records one
shared source and exactly Claude and Codex with behavior, source, mapping, and verification evidence.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/workflow/contract/plan-artifacts/SKILL.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "loads the canonical contract",
      "source": ".agents/plugins/manifests/claude/workflow.json",
      "mapping": "workflow package manifest",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "plan validation"
      }
    },
    {
      "host": "codex",
      "behavior": "loads the canonical contract",
      "source": ".agents/plugins/manifests/codex/workflow.json",
      "mapping": "workflow package manifest",
      "verification": {
        "level": "planned",
        "result": "pending",
        "evidence": "plan validation"
      }
    }
  ]
}
```

Planning may use `planned` with `pending`. A review replaces the moving record in its work order with a record
that adds the full frozen lowercase `candidate_head`, uses `source` or `installed`, and records `passed` or
`limited`. A limited result adds only an `exception` object with `constraint_evidence` and
`supported_other_host_outcome`.

Validate a plan before advancing it and validate review evidence against its candidate head. The helper requires
Python 3.9+: use `python` on Windows and `python3` on Linux or macOS.

```text
python -B "<skill-directory>/scripts/host_coverage.py" --stage plan --document <plan-path>
python3 -B "<skill-directory>/scripts/host_coverage.py" --stage review --document <review-path> --expected-head <full-candidate-head>
```

The validator rejects missing fields, duplicate host or JSON keys, placeholders, malformed records, and the
wrong review level or result. Source verification and installed-host acceptance remain distinct evidence.
