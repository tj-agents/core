# Skill kinds

`kind` answers: **what responsibility does this skill supply?** It is an open vocabulary. A skill declares
one lowercase ASCII word matching `[a-z]+`; producers and payload validators enforce the same shape.
Document a materially distinct new kind here before using it. Generic generators do not embed a vocabulary
allowlist. A checker may enforce a deliberate semantic requirement for a particular capability or repository.

| Kind | Meaning and examples |
|---|---|
| `policy` | Agent-conduct rules active within an already selected scope: authorship mode, authority, continuation, credential scope or process selection. Examples: `goal-continuation`, `git-auth`, `learning`. |
| `convention` | Requirements used to create or assess an artifact: code design, naming, document format, route-table semantics or evidence-record structure. Examples: `style`, `handoff-format`, `review-lifecycle`. |
| `utility` | A bounded capability with a concrete input and result, called directly or by another skill. Examples: `commit`, `pull`, `clip`, `scaffold`, `failure-provenance`. It may have several steps and validation. |
| `workflow` | A capability that keeps ownership of a task across distinct stages and advances it to a declared terminal outcome. Examples: `feature`, `review`, `plan-execution`, `debug-integration`, `stack`. |
| `knowledge` | Descriptive context: proficiency, goals, reference material or orientation. Local interpretation and maintenance guards may accompany the facts; it does not govern unrelated work or own an execution lifecycle. |

Choose the primary responsibility, not a sentence's grammatical form. A convention may contain an example
command or a short checklist. A utility may perform several commands, delegate to another utility, and
verify its result. Those facts alone do not make a workflow. A policy may explain recovery without becoming
a separate executor. A workflow selector or compatibility entry follows the role of the lifecycle it enters.

Use a separate owner when one body has two independently consumed responsibilities; retain supporting
examples and guards with their owner. Do not invent one category per document format or a distinct kind
for aliases. Existing profile/applicability metadata and route/hook configuration select what loads.
`kind: policy` does not mean always loaded, and `kind: utility` does not grant write, network or publication
permission. `kind: convention` makes a skill eligible for convention discovery only after tier selection;
its existing profile and prerequisite constraints still apply.

`contract` and `operation` are legacy skill labels. Updated convention readers accept both `contract` and
`convention` during the compatibility period. Do not translate every legacy contract mechanically: the
approved migration map determines each new role. The labels `lane` and `review` on generated agent records
remain their existing agent-role metadata, outside this canonical-skill migration. Genuine protocol/schema
contracts, workflow identity kinds and review concerns also keep their own meaning.
