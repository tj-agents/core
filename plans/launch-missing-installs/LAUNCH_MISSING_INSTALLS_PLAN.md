# Automatic declared-plugin recovery

Canonical delivery: https://github.com/tj-agents/core/pull/513 (bot-owned replacement for closed #452).

## Goal and authority

The handoff in codex-452.md authorizes repair, review, publication, merge and installed verification.
Launches and `agent:refresh-plugins` repair declared missing installations at their declaring scope, verify
admission, and adopt required runtime changes without asking Tommy to restart or run a command.
Tommy clarified the two-entry-point design: a failed running-session hook directs the agent to refresh
through the skill. No separate background hook installer or recovery receipt mechanism is needed.
Tommy delegated the host packaging choice: keep one `agent:refresh-plugins` identity with separate
Claude/Codex host entries and adoption adapters, sharing installation and verification logic.

## Source and assessment

Core #497 moved runtime to tj-agents/agent. Core owns the consumer skill router. Reuse Agent's native
installation, admission, session identity and same-conversation recovery mechanisms. Do not create
another installer or restore removed Machine code. Agent main already contains the source counterparts
of Core #505 and #507; Core #508 remains an independent machine-retirement delivery.
The original #452 tip is preserved in checkpoint/452-before-cutover-20261026.

Assessment complete for mechanism reuse: current code already provides repair_missing,
prepare_launch_roots, native Codex reload and exact-client relaunch. Primary host documentation and
installed behavior must establish adoption acceptance; source tests alone do not prove it.

## Execution

1. Reproduce missing installation, repository-resolution cost, inventory timeout and false child refusal.
2. Repair the shared admission/installation and adoption path in Agent with focused regressions.
3. Give Core's running-session router a bounded, informative failure directing the agent to `agent:refresh-plugins`.
4. Independently review immutable candidates, run Windows/Linux checks, publish Agent first, then
   revalidate Core against the published producer and land the bot-owned replacement #513.

## Acceptance

- Missing enabled declarations install at project/local scope and native readback proves activation.
- Disabled or untrusted selections remain blocked; failed install never becomes successful admission.
- The same running conversation adopts updates automatically; real subordinate sessions cannot close parents.
- Router failures name the failed gate and recovery action within the existing host deadlines; inventory
  startup and repository lookup have proportional bounds.
- Regressions and independent review cover Windows and Linux; publication and installed behavior are observed.

```agent-host-coverage
```

```completion
{
  "outcome": "Declared plugins are repaired and verified at launch or through agent:refresh-plugins, with the calling conversation adopting updates automatically and required hooks admitting real writes.",
  "acceptance": [
    {
      "id": "source-review-and-platform-checks",
      "criterion": "The producer and consumer repairs pass independent current-head review and Windows/Linux checks.",
      "evidence": [
        {
          "source": "Agent PR12, PR15 and PR17; Core PR513 review receipts and exact-head CI runs",
          "result": "Independent native and security reviews passed; Agent17 CI40449117741 and Core513 CI40444031032 passed Windows/Linux checks."
        },
        {
          "source": "Core513 e35 hosted40532709153; Agent25 bd49 hosted40540386047 and recorded immutable native/L2 reviews",
          "result": "Core seven checks green; Agent25 three checks green. Both exact-head reviews approved."
        }
      ],
      "owner": "Root foreground owner",
      "next_action": "Preserve current-head evidence; finish protected publication and remaining native acceptance."
    },
    {
      "id": "published-installed-runtime",
      "criterion": "Published Agent repairs are installed through supported setup and installed bytes match the merged producer.",
      "evidence": [
        {
          "source": "Agent94a70dc and supported install.ps1 launch-check runtime apply/check",
          "result": "Both commands exited0; installed reload_plugins.py and session_relaunch.py hashes match the merged source and receipt."
        },
        {
          "source": "Published Agent438 native caches and packaged install.py shell profiles apply/check on Windows and Linux",
          "result": "Supported apply/check both0 on each OS; installed startup e870b28f and installer693ab62d match published code. Linux both-host publisher-byte refresh0; Windows both-host refresh fails exact Claude project-registration readback."
        }
      ],
      "owner": "Root foreground owner",
      "next_action": "R1 successor Agent25 is merged. Hold Core513 due to Core512 hook removal; publisher PRs remain eligible for owner approval. Native acceptance remains incomplete."
    },
    {
      "id": "native-windows-same-conversation",
      "criterion": "Both native Windows clients complete default both-host refresh, retain their conversation through any automatic recovery, execute required hooks and perform a real marker edit/readback.",
      "evidence": [
        {
          "source": "Canonical progress native compatibility evidence2026-10-27",
          "result": "Windows refresh exited0, but automatic close refused after command-line identity lookup timed out. Automatic Windows adoption remains incomplete; no new native probes are authorized/needed for publisher cutover."
        }
      ],
      "owner": "Root foreground owner",
      "next_action": "Fresh managed Codex marker reached edit-ok but SessionStart launcher acknowledgment missed; identify exact live UUID before follow-up. Claude native update persistence mismatch remains causally unresolved; isolated tests do not yet reproduce missing-owner failure."
    },
    {
      "id": "native-linux-installed-entrypoints",
      "criterion": "Both Linux installed launch and refresh entrypoints execute with actual native clients and required hook success.",
      "evidence": [
        {
          "source": "Canonical progress native compatibility evidence2026-10-27",
          "result": "Linux Codex automatic same-UUID relaunch, tool/readback passed. Linux Claude remains at login onboarding; no new login or native probes performed."
        }
      ],
      "owner": "Root foreground owner",
      "next_action": "Current published438 runtime is installed and both-host verify refresh0; complete fresh managed native tools and actual exact-conversation automatic recovery for both hosts."
    },
    {
      "id": "declared-missing-native-repair",
      "criterion": "A native launch with a missing enabled declaration installs it at the declared scope and readback plus a real tool operation proves admission.",
      "evidence": [
        {
          "result": "Fresh profile initially lacked all7 selected native installs. Supported managed launch installed them; native project declarations remainenabled with trustedprojectorigin. Native apply_patch changed only the authorized marker towrite-ok thenedit-ok, with successful readbacks. Bothnativeinventories show all7installed/enabled; Claude reportsprojectscope. Same-conversation postrefreshadoption remainsseparate and incomplete."
        }
      ],
      "owner": "Root foreground owner",
      "next_action": "Retain native missing-install/tool evidence; finish both hosts automatic refresh recovery separately."
    },
    {
      "id": "published-update-hints",
      "criterion": "All selected publishers emit publish-update hints after default-branch updates; explicitly selected shared action SHA pins advance through deterministic normal PRs.",
      "evidence": [
        {
          "source": "github-actions34; Agent20; CLI14; Template43; Core519; Personal42",
          "result": "Shared publisher/updater implemented, bot-published and source reviewed; five PRs have all required hosted checks green, Agent final Windows check pending. Full-SHA consumer references target independently reviewed5a6f action bytes. No Renovate or automatic merge; export/digest hashes remain computed by existing Core CI."
        },
        {
          "source": "All six final saved bodies, frozen review receipts, exact-head forge readback and local delivery bindings2026-10-27T19:39Z",
          "result": "All six are bot-owned, pushed, ready and have passing required current-head CI; no GitHub auto-merge request is enabled. Agent7ba generated digest independently recomputes correctly and all23/68 local tests pass. CI-workflow approval stop and required owner reviews remain intact. Actions variables/secrets endpoints still403; environment returned404, so live enrollment/delivery is not claimed."
        },
        {
          "source": "Final exact-head frozen parent/L2 review receipts, canonical renderer equality and authoritative forge readback2026-10-27T21:29Z",
          "result": "Two canonical reusable workflows own job setup; five callers are10/14lines each. All six final heads independently approved, bot-pushed, ready, mergeable and all hosted checks passing; autoMergeRequest null. Content-aware updater passes29 Windows/Linux focused tests and real read-only immutable-object comparison; unchanged referenced content no longer creates pin-only loops. Live enrollment and consumer-scoped token access remain unverified."
        },
        {
          "source": "2026-10-27 merge readback and terminal main-branch runs40591416385/40591416931/40591506271/40591527427/40591527096",
          "result": "github-actions34 merged atc0691e7, Agent20 at8163e3a, CLI14 at7c30aef; all five causally linked main-branch validation runs succeeded. Publish-update jobs skipped without enrollment. Template43/Core519/Personal42 remain OPEN with REVIEW_REQUIRED; no approval bypass or automatic merge armed."
        },
        {
          "source": "Final three approved exact-head ordinary merges and main run40593753591/40593771894/40593789002",
          "result": "All six owned source PRs are merged. Template43 at3e4dc89, Core519 at2058970, Personal42 at78c67ab. Core main CI passed. Personal main conformance failed only for snapshot.py/bootstrap.py, unchanged by our merge; existing pre-merge Personal46 f3a85bd updates those two files for Template48/49 and all three hosted checks already pass. This pre-existing external repair is not adopted, duplicated or merged by this goal. Live publish jobs skipped without enrollment."
        },
        {
          "source": "2026-10-28 owner shell setup exit0; six publisher reruns attempt2 and correlated live channel readback",
          "result": "UPDATE_TOPIC variable/secret enrolled on all six repositories by the owner. All six default-branch publisher jobs succeeded and each has one matching v1 repository hint in the existing channel within its job execution window. Exact run IDs40597946822/40597881004/40597913414/40593754247/40597911312/40593788971. Publisher enrollment and real delivery are verified; no topic/key/token values exposed."
        },
        {
          "source": "2026-10-28 one-time owner updater enrollment prepared",
          "result": "Private setup script ~/.agents-state/update-pins-owner-setup.py at SHA256 f726697e57b04a57d7bc97ec4da8bb938936a68110d29436540a9b1337e608e5 passes13 focused isolated checks plus actual loopback/fake-API manifest-flow checks. Parent and independent L2 frozen review approve owner execution. Creates a private tj-agents App, verifies exact six selected repositories and contents/PR/workflows permissions, preserves other App/environment configurations, enrolls strict default-branch environment credentials and dispatches six workflows. Agent apply refusal verified before auth. No owner login used by agent, App created, credentials copied or live updater success claimed."
        }
      ],
      "owner": "Root foreground owner",
      "next_action": "Owner executes reviewed Bash setup command to create/install the dedicated App and configure/dispatch all six updaters. Root then verifies receipt-bound real workflow execution and ordinary pin-update PRs. Publisher delivery already complete; original native acceptance/Core513 hold remain separate."
    }
  ],
  "deliveries": [
    {
      "repository": "tj-agents/agent",
      "pr": 12,
      "head": "4ba13dd45e771e1701574551e4e1b85618311fca"
    },
    {
      "repository": "tj-agents/agent",
      "pr": 15,
      "head": "d82fd4a493f17b553f3d478a9db7f69463ac8c4a"
    },
    {
      "repository": "tj-agents/agent",
      "pr": 17,
      "head": "c4d81bbbc09efacefd4d34e9e21d79600dddbb82"
    },
    {
      "repository": "tj-agents/company",
      "pr": 30,
      "head": "e5c99069fbf1eef35b4557ecc6b76c632cb327e8"
    },
    {
      "repository": "tj-agents/core",
      "pr": 513,
      "head": "e35ecd99d1506e1eb6e4b93a7467fe68008132cd"
    },
    {
      "repository": "tj-agents/agent",
      "pr": 20,
      "head": "14dba7d0a3a632ecd6d2a2515e4b293c83d366b2"
    },
    {
      "repository": "tj-agents/cli",
      "pr": 14,
      "head": "5af9194ce3b9d43995f559bccc6f39897b52ede0"
    },
    {
      "repository": "tj-agents/template",
      "pr": 43,
      "head": "557ac4dc8ef4141118a7a68a322c80fd3b70e15d"
    },
    {
      "repository": "tj-agents/agent",
      "pr": 21,
      "head": "b07f93b0616bd07b03eeee03c60a61f87165ac2b"
    },
    {
      "repository": "tj-agents/agent",
      "pr": 25,
      "head": "bd49d666310039b422b598b95da85be3e8eafc9c"
    },
    {
      "repository": "tj-agents/github-actions",
      "pr": 34,
      "head": "8d0f28a33f6340f1cfa82dfb40796473ff3a1f27"
    },
    {
      "repository": "tj-agents/core",
      "pr": 519,
      "head": "ae1f3b1d9c319b0c68dae967da95e50fa8d58493"
    },
    {
      "repository": "tj-agents/personal",
      "pr": 42,
      "head": "3453fe276cd8838e17cbef30195119382c9d5fd4"
    }
  ],
  "open_tasks": [
    {
      "repository": "tj-agents/agent",
      "pr": 25,
      "head": "bd49d666310039b422b598b95da85be3e8eafc9c",
      "text": "Merged2026-10-27T16:28:24Z at4fad2409dd872ff7cf69bcc7e7b6f5952ab9f128 from reviewedbd49. All three exact-head hosted checks passed; ordinary exact-head merge and origin/main readback verified.",
      "owner": "Root foreground owner",
      "next_action": "Adopt published R1 through supported native refresh, verify installed bytes and actual same-conversation hooks/tools."
    },
    {
      "repository": "tj-agents/agent",
      "pr": 21,
      "head": "b07f93b0616bd07b03eeee03c60a61f87165ac2b",
      "text": "Externally merged at b217a3c on 2026-10-27T15:03:03Z from b07. Transcript/startup repairs published; reviewed R1 uninstall fix ec942 was not included.",
      "owner": "Root foreground owner",
      "next_action": "Agent25 is the exact four-path missing-R1 successor atbd49; finish its normal delivery, then actual native acceptance."
    },
    {
      "repository": "tj-agents/agent",
      "pr": 17,
      "head": "c4d81bbbc09efacefd4d34e9e21d79600dddbb82",
      "text": "Installed interactive refresh verification remains pending.",
      "owner": "Root foreground owner",
      "next_action": "Complete both native hosts' installed interactive verification and refresh the authoritative PR validation text."
    },
    {
      "repository": "tj-agents/core",
      "pr": 513,
      "head": "e35ecd99d1506e1eb6e4b93a7467fe68008132cd",
      "text": "e35 is pushed, independent source/security review approved and all seven current-head hosted checks passed. Saved body and exact-head binding pass. Auto-merge disabled and verified null after compatibility review: Core512 deletes the router and Codex adapter changed here. Hold this PR; do not request approval or rearm auto-merge.",
      "owner": "Tommy through GitHub; existing guarded continuation owns the resulting delivery",
      "next_action": "Hold Core513 because Core512 supersedes its runtime changes. Reconcile only remaining useful guidance after that cutover; do not automatically merge or rearm Core513. Publisher Agent20, CLI14 and Template43 remain independent."
    },
    {
      "repository": "tj-agents/agent",
      "pr": 20,
      "head": "14dba7d0a3a632ecd6d2a2515e4b293c83d366b2",
      "text": "Merged at 8163e3ae11e9a778d0907b8579019ac2e327885d on 2026-10-27T22:01:15Z after observed user instruction 'i approved can u get on with this shit please'. Exact-head source/security review, fresh body check, base reconciliation and all PR checks passed; ordinary merge retained GitHub review/check protections. All causally linked main-branch checks passed; publish-update skipped pending enrollment. Delivery binding released.",
      "owner": "Root foreground owner; repository owner retains review/configuration gates",
      "next_action": "Merged source and live publisher hint delivery are verified. Remaining: dedicated updater App credentials, protected environment enrollment and real scheduled/manual pin-update PR; original native acceptance remains separate."
    },
    {
      "repository": "tj-agents/cli",
      "pr": 14,
      "head": "5af9194ce3b9d43995f559bccc6f39897b52ede0",
      "text": "Merged at 7c30aefa7a09e026ef7a03ea964ef2f1a31edade on 2026-10-27T22:01:25Z after observed user instruction 'i approved can u get on with this shit please'. Exact-head source/security review, fresh body check, base reconciliation and all PR checks passed; ordinary merge retained GitHub review/check protections. All causally linked main-branch checks passed; publish-update skipped pending enrollment. Delivery binding released.",
      "owner": "Root foreground owner; repository owner retains review/configuration gates",
      "next_action": "Merged source and live publisher hint delivery are verified. Remaining: dedicated updater App credentials, protected environment enrollment and real scheduled/manual pin-update PR; original native acceptance remains separate."
    },
    {
      "repository": "tj-agents/template",
      "pr": 43,
      "head": "557ac4dc8ef4141118a7a68a322c80fd3b70e15d",
      "text": "Merged at 3e4dc89b48a16e785e654147f6d9bd8e26f0a04f on 2026-10-27T22:18:06Z after required GitHub approval, exact-head source/security review, fresh body check and base reconciliation. Post-merge run: success. Delivery binding released.",
      "owner": "Root foreground owner; repository owner retains review/configuration gates",
      "next_action": "Merged source and live publisher hint delivery are verified. Remaining: dedicated updater App credentials, protected environment enrollment and real scheduled/manual pin-update PR; original native acceptance remains separate."
    },
    {
      "repository": "tj-agents/core",
      "pr": 516,
      "head": "d5d222dcd684935166a4102ab4f541b7ec08c9a9",
      "text": "External prerequisite merged at b88ff16b696c3971b09589be115ece3605e61cdd; generated packages published at f847d301722ceb383f43c628d3ae99af82225b5e. Installed publisher-byte verification passed and affected normal native hook execution succeeded; required local Personal setup ACL drift was separately repaired and setup/check passed. This goal does not own that delivery.",
      "owner": "Verified live Claude owner22176c14-5e45-4d73-a2fb-c906e0147dea in core.worktrees/Refactor-PluginsRename",
      "next_action": "Hook/import recovery is verified. Supported no-relaunch refresh now reports current with no setup problems and explicitly rejects incomplete client adoption; complete automatic adoption only through the real managed entry points after Agent recovery publication."
    },
    {
      "repository": "tj-agents/github-actions",
      "pr": 34,
      "head": "8d0f28a33f6340f1cfa82dfb40796473ff3a1f27",
      "owner": "Root foreground owner; repository owner retains review/configuration gates",
      "text": "Merged at c0691e7a91ab85b7a61e278a016b7d93a9ed9e2c on 2026-10-27T22:00:37Z after observed user instruction 'i approved can u get on with this shit please'. Exact-head source/security review, fresh body check, base reconciliation and all PR checks passed; ordinary merge retained GitHub review/check protections. All causally linked main-branch checks passed; publish-update skipped pending enrollment. Delivery binding released.",
      "next_action": "Merged source and live publisher hint delivery are verified. Remaining: dedicated updater App credentials, protected environment enrollment and real scheduled/manual pin-update PR; original native acceptance remains separate."
    },
    {
      "repository": "tj-agents/core",
      "pr": 519,
      "head": "ae1f3b1d9c319b0c68dae967da95e50fa8d58493",
      "owner": "Root foreground owner; repository owner retains review/configuration gates",
      "text": "Merged at 205897076e3e0d954f0da05d74a7fb1b7ff0d56b on 2026-10-27T22:18:14Z after required GitHub approval, exact-head source/security review, fresh body check and base reconciliation. Post-merge run: success. Delivery binding released.",
      "next_action": "Merged source and live publisher hint delivery are verified. Remaining: dedicated updater App credentials, protected environment enrollment and real scheduled/manual pin-update PR; original native acceptance remains separate."
    },
    {
      "repository": "tj-agents/personal",
      "pr": 42,
      "head": "3453fe276cd8838e17cbef30195119382c9d5fd4",
      "owner": "Root foreground owner; repository owner retains review/configuration gates",
      "text": "Merged at 78c67ab829d1eea390f9bc8d3614ea7c64adb477 on 2026-10-27T22:18:21Z after required GitHub approval, exact-head source/security review, fresh body check and base reconciliation. Post-merge run: failure. Delivery binding released.",
      "next_action": "Merged source and live publisher hint delivery are verified. Remaining: dedicated updater App credentials, protected environment enrollment and real scheduled/manual pin-update PR; original native acceptance remains separate."
    }
  ]
}
```


### R1 successor inline publication assessment

PR: https://github.com/tj-agents/agent/pull/25, bot-owned at reviewedbd49; saved body and exact-head scoped goal binding pass, all three hosted checks green. Agent21 merged at b217a3c from b07 and omits the reviewed R1 repair. Retire only its completed local binding; the canonical Core goal and continuation remain active. The standalone missing-fix successor uses Fix/ClaudeRetiredRefresh in the reused Fix-ClaudeRefreshTurn checkout, base438783a2ba1049f2afbecc16d62677cb4b8fd1ac and headbd49d666310039b422b598b95da85be3e8eafc9c. Exact four-path scope is one authored Claude filter line, one meaningful project/local regression and generated runtime/hook digest output:37 insertions/8 deletions. Prior source commit/ec942 and all review history are preserved. Windows28 focused tests, generated and Template checks pass; independent immutable native/L2 review and host coverage are approved. Publish this small standalone repair for exact-head Linux/Windows CI; installed same-conversation acceptance remains separate. No new mechanism or policy scope is introduced.
