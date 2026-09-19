# Plan-artifacts P1 verification

Candidate: Codex package 1.2.0; Claude retains commit-based refresh. Source baseline
`c3572f85163f581a645c0f43d67df6b3563ffa82`; implementation is on `Feature/PlanArtifacts`.
This is verification evidence, not a second migration plan. The workspace-level
`AGENT_ECOSYSTEM_MIGRATION_PLAN.md` remains the progress owner.

## Observed results (2026-09-19, Windows)

- Generator and `-Check`: 183 current files, 55 skills, distinct Claude and Codex trees.
- `python -B -m unittest discover -s tests -p test_plan_artifacts.py -v`: four passing tests covering
  both packaged roots, resource closure, identical canonical bodies, startup/resume/compact/clear
  fixtures, an unrelated directory with spaces, actual Git Bash command execution, no adapter file
  mutations, absent/malformed/unreadable contract diagnostics, and digest-marked fallback generation.
- `tests/skill-packaging.tests.ps1` and `tests/handoff-launchers.tests.ps1`: pass.
- Claude Code 2.1.278 ordinary plugin validation: pass with the existing missing-version warning.
  Strict validation: exit 1 for that warning, also observed on the unmodified baseline. A disposable
  control copy with only `version: 1.2.0` added passes strict validation. The shipped Claude manifest
  deliberately stays versionless under the existing refresh policy; no release-policy migration occurred.
- Codex CLI 0.155.1 native local-marketplace registration and installation into a fresh disposable
  CODEX_HOME: pass; native installer reports base@base-agents 1.2.0, enabled. No other plugin was installed.
- Claude loaded the copied base package with `--plugin-dir` and an isolated CLAUDE_CONFIG_DIR. Its
  actual SessionStart hook event reports exit 0, success, and the canonical contract in additionalContext.
- Codex was launched with its reviewed-hook, invocation-only trust override for the disposable probe.
  Persisted hook trust and native Codex context delivery are **not established** by the available evidence.
  No generated native-instruction fallback was installed; its rendering was tested separately.
- Neither host completed a model turn: sandbox networking blocked the requests. The automatic approval
  reviewer rejected the networked retry because sending repository-derived plugin/contract context to
  the model service needs explicit payload/destination approval. The probe processes were stopped and
  temporary credential copies removed. Normal profile settings and credentials were not modified.
- The generic skill-creator validator rejects the repository's established top-level `kind` and `domain`
  metadata. The repository generator accepts and validates this metadata; the upstream validator was not
  changed and its result is not reported as a pass.

## Behavioral coverage still required

A hook-output test establishes context delivery, not model compliance. All seven cases below remain
unverified on both hosts. Use disposable profiles with only base, copied package resources, separate
working directories containing spaces, and no repository, provider, or roadmap unless the case supplies
an existing owner. Keep authentication private; do not copy normal settings or transcript stores.

| Case | Request / fixture | Inspect |
|---|---|---|
| New plan | Plan a household book tracker with import, duplicate detection, and search | Actual useful Markdown plan; response path/link resolves |
| Correction | Replace CSV with JSON and reject duplicate ISBNs before saving | Same file, reconciled decisions, sequence, acceptance criteria |
| Resume | Resume planning; sample JSON reviewed, no implementation/tests performed | Reads canonical state, records accurate progress and remaining work |
| Planning-only | Explicitly request planning without implementation | No product code, install, publication, or claims of implementation |
| Quick task | Ask for 17 + 25 in an empty directory | Brief answer, no ceremonial plan |
| Spaces | Run new/correct/resume in a path with spaces | Usable exact path and clickable link |
| Existing owner | Supply ROADMAP NOTES.md and local instructions selecting it | Updates that owner; preserves local rules; no competing ledger/plan |

Run creation, correction, and resume in one host session chain, then also resume from a fresh session
using only the saved artifacts. Capture response links, actual file diffs, hook results, and unexpected
mutations. Inspect acceptance semantics manually; do not substitute matching expected wording.
For Codex, either observe trusted hook delivery or deliberately generate and merge the digest-marked
native fragment, preserving unrelated instructions, and label the delivery mechanism accurately.
Native startup/resume/compaction context delivery and desktop/Linux coverage need separate evidence;
only adapter fixtures for those events currently pass. P1's cross-host completion gate remains open.

## Reproduction and interface sources

Run from the implementation checkout:

```text
pwsh -NoProfile -File .agents/sync-generated.ps1 -Check
python -B -m unittest discover -s tests -p test_plan_artifacts.py -v
pwsh -NoProfile -File tests/skill-packaging.tests.ps1
pwsh -NoProfile -File tests/handoff-launchers.tests.ps1
claude plugin validate --strict ./plugins/base
```

The last command has the baseline warning described above. Source packaging and resource validation
must pass independently of host/model availability. Do not change the release policy solely to hide it.

[OpenAI plugin hooks](https://developers.openai.com/plugins/build/plugins) documents the compatibility
CLAUDE_PLUGIN_ROOT variable and explicit legacy manifest hook paths.
[Claude hooks](https://code.claude.com/docs/en/hooks) documents SessionStart additionalContext and
shell execution. Installed CLI help was checked for profile, local-plugin, and hook-trust options.
