# Assess existing solutions once when an idea begins

Status: in-progress
Worktree: C:\Users\TommySeery\source\repos\tj-agents\core\.worktrees\Fix-IdeaInitialization
Branch: Fix/IdeaInitialization
PR: not opened
Transfer mode: bounded side-workstream
Execution authorization: source repair, verification, review, PR and merge under standing core authorization; no installation into consuming repositories or host profiles.

## Goal

Correct the shared convention added in PR 221. Tommy wants a SMALL initialization convention for every repository consuming core: once when a new idea is introduced, check existing work and decide whether to adopt, fork, selectively reuse, build custom, or keep what exists. Handoff, resume, compaction, another implementation step, a branch change, or reading the convention again must never trigger another assessment for the same idea. Preserve and carry the recorded decision. Reopening requires an explicit user request; do not silently add a repeat-on-material-change exception.

## Evidence and authority

On 2026-10-12 Tommy said the rule should not be in goal continuation: it should be initialization, done once and only once at the start of the idea. The merged rule is currently in .agents/base/policy/goal-continuation/SKILL.md. It already has some recorded-assessment reuse wording, so repeated research was not observed; the confirmed defect is its lifecycle ownership and the remaining material-change reopening exception. The original parent chose the wrong owner. Source defect repair is authorized by engineering:session-guidance, whose standing default covers source implementation, testing, PR and merge after gates. .agents/delivery-authorization.json provides core's standing merge authority.

The initial public-alternative assessment is already complete in docs/workflows/HANDOFF_ALTERNATIVES.md. Do not repeat it. Do not modify that comparison or handoff launch/receipt/cleanup runtime.

## Acceptance

- Remove the reuse-assessment section from goal-continuation and place a brief rule with the appropriate shared idea-initialization owner; inspect existing owners before creating a new skill.
- Scope it to new ideas, general projects and reusable mechanisms, keeping routine edits and application-specific business logic proportionate.
- Before researching, consult the same idea's existing decision. Record completion and useful references in existing task context or an existing goal/decision artifact; do not require a new plan, repo-local configuration, database, or command for a small idea.
- Handoff and resume carry the completed assessment forward. They do not rerun it. Do not equate SessionStart context delivery with execution of initialization.
- All core consumers on both Codex and Claude receive the rule through shipped base delivery, with one canonical source. Update only required adapters, declarations and pointers.
- Keep the authored rule small. No new runtime merely to count invocations; this is a convention, not a request for a once-only execution engine.
- Verify packaging and context delivery, complete independent review and required exact-head CI, merge under standing authorization, verify causal generation, and perform proven cleanup. Keep generated output out of the PR.

## Ownership and next steps

Pickup acknowledged: 2026-10-12 by the successor in this exact checkout on
`Fix/IdeaInitialization`. The handoff authorization and acceptance criteria are preserved.
The bounded L3 inspection selected a new, independent `policy` in the base behavior domain:
`idea-initialization`. It has no lane because it is a conduct rule, not an execution workflow.
The completed public-alternative assessment remains authoritative and will not be repeated.
This source move is one focused repair slice for merged PR 221; no new PR owner is selected yet.
It is based on `0d797f568a53b73ff2e8c271c7aaf3f32f29035e`; no branch rename is needed.
It is based on `0d797f568a53b73ff2e8c271c7aaf3f32f29035e`; no branch rename is needed.

The prose move uses a serialized L5 writer. A separate L4 writer owns any packaging, hook wiring,
or tests that prove both-host source coverage and context delivery. The existing base adapter roots
map canonical skills to `.codex/skills` and `.claude/skills`; source generation and manifests remain
with the L4 phase if evidence shows they need changes.

One successor owns this checkout and its source changes; the originating session answers the user
and will not edit these paths. You are not alone in this repository: preserve other agents' work and
do not edit or clean the dirty primary checkout.

L5 source work is complete in `.agents/base/policy/idea-initialization/SKILL.md`,
`.codex/skills/idea-initialization/SKILL.md`, `.claude/skills/idea-initialization/SKILL.md`, and
`.agents/base/policy/goal-continuation/SKILL.md`; README and this goal now distinguish initialization
from continuation. Next action: L4 verifies packaging and context delivery for both hosts and updates
only the required source declarations or tests if evidence requires them.

L4 added the read-only packaged context helper at
`.agents/base/policy/idea-initialization/scripts/session-context.py`, registered it in both host
SessionStart manifests, and declared the skill and hook in the base harness and catalog. Local package
generation, generated-package freshness, harness-manifest validation, and catalog-digest validation passed.
The installed-package context and both-host registration tests passed. The initial source-layout run could
not copy the active ignored `.agents/continuation/scheduler.lock`; its fixture now excludes that transient
directory, and the isolated rerun passed 22 tests. The local catalog digest refresh was verified, then its
base digest field was restored for the authored-only commit. Continuation initialization, foreground claim,
task registration, and wake have also succeeded for this worktree. Next action: stage only the authored
source paths, commit the repair, and begin frozen review; generated output remains unstaged.

L4 added the read-only packaged context helper at
`.agents/base/policy/idea-initialization/scripts/session-context.py`, registered it in both host
SessionStart manifests, and declared the skill and hook in the base harness and catalog. Local package
generation, generated-package freshness, harness-manifest validation, and catalog-digest validation passed.
The installed-package context and both-host registration tests passed. The initial source-layout run could
not copy the active ignored `.agents/continuation/scheduler.lock`; its fixture now excludes that transient
directory, and the isolated rerun passed 22 tests. The local catalog digest refresh was verified, then its
base digest field was restored for the authored-only commit. Continuation initialization, foreground claim,
task registration, and wake have also succeeded for this worktree. Next action: stage only the authored
source paths, commit the repair, and begin frozen review; generated output remains unstaged.

The existing public-alternative assessment remains authoritative. Do not repeat it. Do not ask Tommy
to approve the already-authorized repair. The root working BUGS.md record links to this goal; do not
edit that primary register while another session owns it.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/base/policy/idea-initialization/SKILL.md",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Move reuse assessment from continuation into a small once-per-idea initialization convention; preserve completed decisions during handoff and resume.",
      "source": ".agents/base/policy/idea-initialization/SKILL.md",
      "mapping": "Canonical base policy mapped through .claude/skills/idea-initialization/SKILL.md; shared base SessionStart delivery supplies context only.",
      "verification": {"level": "planned", "result": "pending", "evidence": "Canonical idea-initialization policy and Claude pointer are authored; L4 packaging and context verification remain pending."}
    },
    {
      "host": "codex",
      "behavior": "Move reuse assessment from continuation into a small once-per-idea initialization convention; preserve completed decisions during handoff and resume.",
      "source": ".agents/base/policy/idea-initialization/SKILL.md",
      "mapping": "Canonical base policy mapped through .codex/skills/idea-initialization/SKILL.md; shared base SessionStart delivery supplies context only.",
      "verification": {"level": "planned", "result": "pending", "evidence": "Canonical idea-initialization policy and Codex pointer are authored; L4 packaging and context verification remain pending."}
    }
  ]
}
```
