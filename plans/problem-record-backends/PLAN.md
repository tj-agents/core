# Optional problem-record providers

Authorized by Tommy's 16 October 2026 instruction to implement the work-items proposal.
Shared design: tj-agents/docs/plans/problem-management/PLAN.md. Source slice owner:
codex:01a1415f-6448-7123-8b17-c7fb67aee637. PR: not opened.
Branch Feature/ProblemRecordBackends from 6be8c45a211d6a673ae69025263e787ff7a4895e.
This checkout is isolated from the parent's Fix/RollingPluginSync task and dirty primary checkout.

## Contract and scope

Keep published record/address skills and existing file-backed callers. An optional committed
`.problem-records.json` selects `{"schema_version":1,"provider":"plugin:utility"}`; absence retains
file behavior. A selected provider must resolve through Core's real installed-skill resolver and ship
`scripts/read_problem_record.py`, invoked as a separate Python process with explicit source root
and record URI. Core imports no provider runtime and contains no GitHub transport. Missing or broken
selected providers fail without falling back to Markdown or another backend. Backend-specific
configuration stays with the provider (.work-items.json for the optional GitHub implementation).

Remote admission takes explicit source root and host, re-reads the provider's current body, and
validates the existing unique disposition, callout binding, causal owner, repair goal, native-owner
and capability/dependency evidence. The selected source and repair goal must share the actual source
primary checkout. Closed records cannot defer an outstanding obligation. Legacy absolute paths and
primary register behavior remain compatible. Core recording semantics defer storage and retention to
an explicitly adopted provider; work repositories receive no new provider automatically.

The backend package adds its reader and adopts both configuration declarations as a coordinated
follow-up before rollout. This source change alone does not install or adopt that package.

## Verification and delivery

Expected under 1,000 substantive changed lines. Include helper, admission caller, source packaging,
record guidance and focused provider/gate tests atomically. Validate existing file admission plus
missing provider, malformed response, changed source, closed issue and fresh remote evidence for both
host values. Run generated checks with distribution changes unstaged, independent review, then
Windows/Linux CI. Source provider acceptance remains separate from installed host evidence.

## Progress

Fresh Core base and runtime/packaging/admission contracts inspected. Generic provider interface chosen
because Core already owns installed-skill discovery; reusing it avoids another registry or machine-local
script configuration. Generic provider, admission and both host receipt callers are implemented. Four provider tests, thirteen admission tests and twenty-two gate tests passed. Package synchronization checked 567 files and three harness manifests. Generated distribution and catalog changes remain local and unstaged. No consumer behavior or installed acceptance is claimed.

## Next

Review and deliver this bounded Core slice, then qualify the work-items adapter
against the same protocol and run its controlled pilot.

Review correction: deterministic shipped helper resolution is verified for source and all four packaged admission entry layouts. Five provider, fourteen admission and twenty-two gate tests pass (41 total). Native discovery failure and wrong-host receipts fail closed. Package and harness freshness passed before disposable generated output was restored to HEAD for the next native review. No generated distribution or catalog is in the candidate.
