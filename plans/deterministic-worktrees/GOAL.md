# Deterministic worktrees

Owning items: https://github.com/tj-agents/core/issues/604 and https://github.com/tj-agents/core/issues/632

State: complete on 2026-11-17. The implementation, dependent callers, publication and installed acceptance are delivered.

Current owner: codex:01a1e945-2b55-7c21-a2a4-f1ce61aa72b0, launch e67b250439ed4d6a9d4811c068bb8fd8.
Tommy authorized takeover of the interrupted repair and explicitly requested full merge and completion.
The reporting parent is "dotnet concurrency standard", codex:01a1e93d-9768-7493-86d0-69769836f0e0.
Report only completion, an unresolvable blocker or required approval to that parent through agent:message.

## Why the earlier repair did not prevent the incident

The prior Core PR 605 remained unmerged and unpublished after November 12. A November 17 Claude
transcript records a direct Git creation into ../dotnet.worktrees/concurrency-standard, followed by a
branch rename and a failed move. It bypassed the shared creator. Agent's tj start also independently
used worktrunk to create sibling checkouts. Marketplace source pins were a further required delivery
layer: changing producer source alone did not update installed payloads.

The replacement uses the one Core creator for primary-root resolution, fresh default-base creation,
safe repeated reuse, canonical placement and actual session claims. Base embeds that source and gates
supported direct shell and native routes. Agent resolves the enabled native Base installation and invokes

The canonical location is <primary repository>/.worktrees/<flattened branch>. The owning public
operation is engineering:open-worktree; its create_worktree.py accepts --repo and a Type/Name branch.

## Delivered changes

| Repository | PR | Merge | Published payload |
|---|---|---|---|
| Core | https://github.com/tj-agents/core/pull/605 | 5c13ca15f26b4992c5a7ff59752aba8094ddbf54 | Superseded by the final Core publication below |
| Core | https://github.com/tj-agents/core/pull/635 | b56b85fc70adb8294cb102e0815dde0151898e0a | ac38a9737f872b45ff9f674418ff4cc5d9df5436 |
| Agent | https://github.com/tj-agents/agent/pull/230 | ecf01852b2ea01a7b0253c492d9a42175f9fe1e2 | 1cc5511a613e9b90ac4284fdd84fbc81412e03eb |
| Marketplace | https://github.com/tj-agents/marketplace/pull/135 | cfee5432ac2a1bff859a954306803fa217fbde88 | Paired Core and Agent pins plus the private caller pin |

All five PRs passed their required checks and merged. Core and Agent's generated payloads were produced
by their official publication jobs, and those exact generated commits passed CI. Marketplace published
both native catalogs from its one authored roster. No required review, queue or check was bypassed.

Core's final publication CI run 44098479706 passed on attempt 2. Attempt 1 stopped during a truncated
third-party npm archive download, before acceptance tests; the one rerun passed on the unchanged SHA.
Core merge/publication run 44097270036, Agent payload CI 44101035938 and parity 44101034798,

## Installed acceptance

Canonical evidence directory:
C:/Users/TommySeery/source/repos/tj-agents/core/.git/agent-workflow/runs/canonical-worktree-routes/artifacts/runtime/

- Both native plugin updaters completed successfully. A stale inherited bot_identity.py credential
  override was removed only from the update subprocess environment; no obsolete helper was recreated.
- Native enabled Base and Agent roots on both hosts match the final published code. Base files differ
  from Git blobs only by Windows CRLF line endings; installed and normalized hashes are retained.
- The actual Codex Desktop create_worktree tool was denied by the refreshed hook and pointed to the
  published creator. Direct Git creation and worktrunk mutations were also denied.
- Fresh Claude 2.1.306 through the normal C:/nvm4w/nodejs/claude.CMD launcher denied startup --worktree,
  Bash Git creation, Bash worktrunk, EnterWorktree and Agent worktree isolation. The tool sequence used
  a deterministic localhost provider; it made no remote model request.
- The published installed tj start creator actually created Core's canonical probe checkout through
  Codex's enabled Base inventory and reused the identical checkout through Claude's. Its owner matched
  this real session, its HEAD matched published main, and its clean probe was removed afterward.
- The native CLI, launch-check runtime, tj lifecycle commands and Codex hook-trust installer checks passed.
  skill is absent from all eight existing recorded project scopes and the current user payload.
  One historical registration whose temporary project no longer exists was preserved.

An initial Claude probe incorrectly preferred the explicit secondary .local/bin/claude.exe, which is
the pre-existing 2.1.282 executable. Its startup result was rejected as evidence about the normal launcher.
An attempted optional CLI update failed; the normal launcher was restored through npm to its original
2.1.306 version, and its original binary matched the integrity-verified official package. The corrected
full probe passed. No upgrade is claimed or needed for the tested normal launcher.

Coverage is bounded to direct supported routes. Arbitrary opaque programs are not sandboxed by this gate.
Claude's --worktree with --tmux occurs before plugin hooks and is outside this plugin lifecycle
(https://code.claude.com/docs/en/hooks#worktreecreate). Explicit use of the old secondary 2.1.282 binary
is outside the verified normal launcher. Already running peer sessions were not forcibly restarted.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/engineering/operation/open-worktree/scripts/create_worktree.py",
  "hosts": [
    {
      "host": "codex",
      "behavior": "Canonical worktree placement and shared creator routing",
      "source": ".agents/plugins/manifests/codex/base-hooks.json",
      "mapping": "Base embeds the canonical creator and composed tool gate",
      "verification": {
        "level": "installed",
        "result": "passed",
        "evidence": "runtime/acceptance.json; actual Desktop tool, direct shell Git and worktrunk denied; installed Agent creation/reuse passed"
      }
    },
    {
      "host": "claude",
      "behavior": "Canonical worktree placement and shared creator routing",
      "source": ".agents/plugins/manifests/claude/base-hooks.json",
      "mapping": "Base embeds the canonical creator and composed tool gate",
      "verification": {
        "level": "installed",
        "result": "passed",
        "evidence": "runtime/claude-worktree.txt and runtime/claude-tools.jsonl through normal 2.1.306 launcher"
      },
      "exception": {
        "constraint_evidence": "Native --tmux startup predates plugin hooks; the explicit older secondary 2.1.282 binary is not the tested normal launcher.",
        "supported_other_host_outcome": "Codex's actual Desktop route is intercepted."
      }
    }
  ]
}
```

## Preserved migration and ownership evidence

The original migration moved 66 clean unowned checkouts, removed 23 verified empty sibling containers
and reported 217 held checkouts. MIGRATION.md, migration.json and evidence/ retain those exact outcomes.
These historical moves were not repeated. No held, dirty or actively owned legacy checkout was moved
or deleted during this repair; the Dotnet concurrency checkout was preserved.

The original Feature-DeterministicWorktrees directory is retained detached at c8ffbf8a, with its dirty
generated output and migration evidence. Unrelated edits and active source primaries remain preserved.
This repair's clean completed delivery worktrees and disposable probes were individually proven safe
before removal; no bulk sweep or cleanup of unrelated checkouts was performed.

The original continuation owner 230df3f0c38f87923f1fa760 had already reached its terminal blocked budget
state. Its owning removal command reported no scheduler receipt to remove; no new continuation was
registered. A final read-only scheduler listing could not run because its Windows PowerShell command
was unavailable. The old approval command and waiting instructions are superseded. No human approval
remains for these merged deliveries.
A copy of the previous goal is retained as historical evidence in runtime/GOAL-before-closeout.md.

## Next Steps

No implementation, publication or installed-acceptance work remains for the authorized repair.
Any future move of a held checkout needs its own explicit authorization and fresh owner/dirty/binding
checks. Use current normal launchers and the shared creator for new work.

```completion
{
  "acceptance": [
    {"id": "command", "criterion": "Create or safely reuse the canonical checkout with the real owner", "evidence": [{"source": "runtime/agent-creator-verification.json", "result": "passed through both host inventories"}], "owner": "codex:01a1e945-2b55-7c21-a2a4-f1ce61aa72b0", "next_action": "none"},
    {"id": "host-enforcement", "criterion": "Verify supported installed shell and native routes", "evidence": [{"source": "runtime/acceptance.json", "result": "passed, including actual Desktop tool and normal Claude startup; explicit lifecycle limits recorded"}], "owner": "codex:01a1e945-2b55-7c21-a2a4-f1ce61aa72b0", "next_action": "none"},
    {"id": "safe-migration", "criterion": "Preserve verified migrations and exact held-tree evidence", "evidence": [{"source": "MIGRATION.md and migration.json", "result": "66 original moves, 23 original empty-container removals, 217 original holds preserved"}], "owner": "Tommy for any separately authorized held-tree migration", "next_action": "none within this repair"}
  ],
  "deliveries": [
    {"repository": "tj-agents/core", "pr": 605, "head": "0bee2671ccc3cb9b1bd719d5716548b988062464"},
    {"repository": "tj-agents/core", "pr": 635, "head": "ecd913b36f7522d2f5f28589b11019a6925cf13a"},
    {"repository": "tj-agents/agent", "pr": 230, "head": "6f0c659f3f7cbc72aba38cd850b90ec30c0dc468"},
    {"repository": "tj-agents/company", "pr": 50, "head": "d6f4a2ac0aa2796b8b17334d9aab011348cab915"},
    {"repository": "tj-agents/marketplace", "pr": 135, "head": "1465764b18c14eef35e07247571afd809ab3b64e"}
  ],
  "open_tasks": []
}
```
