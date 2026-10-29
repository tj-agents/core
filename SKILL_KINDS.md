# Skill kinds

`kind` answers: **what responsibility does this skill supply?** Each canonical skill declares one of
the six values below. Core owns their shared meanings; producers validate the supported vocabulary.
The navigation group is derived from kind, not stored as another field.

| Group | Kind | Responsibility and selection test |
|---|---|---|
| Rules | `policy` | Governs agent conduct, authority or action selection within an already selected scope. Examples: `base:task-routing`, `engineering:committing`. |
| Rules | `standard` | Defines criteria for constructing or assessing an artifact or system. Examples: `engineering:docs`, `workflow:plan-artifacts`. |
| Work | `operation` | Accepts bounded input and returns a concrete result to its caller. Examples: `engineering:commit`, `engineering:review`, `workflow:status`. |
| Work | `workflow` | Retains task ownership through distinct stages and unresolved acceptance, selecting subsequent actions until its declared outcome. Examples: `workflow:run`, `engineering:feature`. |
| Learning | `learning` | Owns teaching, assessment and learner understanding or progression. Example: `python:learning`. |
| Context | `reference` | Supplies independently useful descriptive orientation without owning execution or normative rules. Example: the descriptive orientation in `python:direction`. |

```text
engineering:review: frozen candidate -> assessment; kind: operation
engineering:feature: implementation -> review -> validation -> delivery; kind: workflow
python:learning: explanation -> learner demonstration -> assessment; kind: learning
```

Choose the primary responsibility and observable ownership. Several commands, delegation, retries,
duration or saved intermediate state do not alone make a workflow. An operation may diagnose, repair
and validate what it needs to return its bounded result. A workflow remains responsible when a
constituent operation returns and the goal's acceptance is still unmet. A standard may include commands
or executable helpers without becoming an operation. Incidental teaching constraints do not make a
learning skill a policy.

Kind is independent of source path, public identity, repository preset, host, applicability and
authority. Canonical skills live at `.agents/<namespace>/skills/<subject>/SKILL.md`; recategorisation
changes metadata. `kind: policy` does not mean always loaded, and `kind: operation` grants no write,
network or publication permission. Selected standards retain their existing tier, profile and
prerequisite constraints.

Maintained proficiency, goals and progress are learner data read by their learning owner, not reference
skills merely because they are Markdown. Reference material needs an independent descriptive consumer;
otherwise keep it as a supporting resource. For mixed documents, separate independently consumed
responsibilities and link their existing owners. Skill existence, sizing and naming remain owned by
[`engineering:skill-authoring`](.agents/engineering/skills/skill-authoring/SKILL.md).

`utility`, `convention`, `contract` and `knowledge` are retired canonical skill kinds. Reclassify by
responsibility rather than translating every former value mechanically. Ordinary protocol/schema
contracts, workflow identity fields and generated agent-role labels keep their own meanings; this
vocabulary governs canonical skills only. A helper, adapter, schema or template is not another kind.
