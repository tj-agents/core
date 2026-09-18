---
name: recents
description: Reconstruct what Tommy was recently working on from git activity — clusters recent commits into workstreams, flags what's still unmerged/open (the stuff to pick back up), and points at where to resume. Use whenever Tommy says "/recents", "what was I working on", "what did I do yesterday / this week", "what's still open", or "where did I leave off". Works in any repo.

kind: operation
domain: machine
---

Answer "what was I working on recently?" by mining git — not chat history (that's `/last-conversation`).
The goal is a short, ranked rundown of **workstreams**, with the **unfinished** ones surfaced first,
because those are what Tommy actually wants to resume.

## Window

Default: **last 2 days**. Honor an override in the invocation — "this week" → `7 days`,
"yesterday" → `2 days` (yesterday + today), "last 3 days" → `3 days`, a date → `--since=<date>`.
Map whatever Tommy said to a `--since` value and use it in every command below.

## Gather (one message, parallel Bash calls)

```bash
SINCE="2 days ago"   # ← replace from the window above
```

1. **Commits across all branches in the window** — the raw material:
```bash
git log --all --since="$SINCE" --date=short --pretty=format:'%h %ad%d %s' | head -80
```

2. **In-flight branches** — local branches with commits not yet in the main branch (this is the
   actionable list — unfinished work). Detect the main branch, then count each recent branch's lead:
```bash
main=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##'); main=${main:-master}
git for-each-ref --sort=-committerdate refs/heads --format='%(refname:short)' | head -25 | while read b; do
  [ "$b" = "$main" ] && continue
  n=$(git rev-list --count "$main".."$b" 2>/dev/null)
  [ "${n:-0}" -gt 0 ] && printf '%s\t%s ahead\t%s\n' "$n" "$n" "$b"
done | sort -rn | cut -f2,3
```

3. **Open PRs** (if `gh` is available and it's a GitHub repo) — ready vs draft matters:
```bash
gh pr list --state open --json number,headRefName,title,isDraft \
  --jq '.[] | "#\(.number) [\(if .isDraft then "draft" else "ready" end)] \(.headRefName) — \(.title)"' 2>/dev/null | head -20
```

4. **Recently-touched plans/docs** — working docs signal what was being designed:
```bash
git log --all --since="$SINCE" --name-only --pretty=format: -- 'plans/**' '**/TECH_DEBT.md' '**/*.md' 2>/dev/null \
  | grep -v '^$' | sort -u | head -25
```

5. **Concertable only — red platform-sync PR check** (a stranded platform is urgent to know about).
   Skip in other repos:
```bash
sp=$(gh pr list --state open --json number,headRefName --jq '.[]|select(.headRefName|startswith("chore/platform-sync-"))|.number' 2>/dev/null | head -1)
[ -n "$sp" ] && gh pr checks "$sp" 2>/dev/null | awk -F'\t' '$2=="fail"{print "RED platform-sync PR #'"$sp"': "$1}'
```

6. **Codex sessions in the window** — to attach a *resume hash* to each workstream. Run this
   PowerShell call (it's a separate tool, not part of the Bash batch above):
```powershell
. "$env:USERPROFILE\.Codex\Get-LastClaudeConversation.ps1"; Get-LastClaudeConversation -Count 40 | Select-Object Modified, Branch, Session, Msgs, Preview | Format-Table -AutoSize -Wrap
```
   Each row is one session: `Modified`, `Branch`, `Session` (the resume id), `Msgs`, and `Preview`
   (the first user message). `Codex --resume <Session>` reopens it.

## Cluster into workstreams

Group the commits into **themes**, don't list them raw. Cluster by, in order:
- **conventional-commit scope** — `feat(b2b/tenant)`, `refactor(pdf)`, `fix(payment)` → one theme per scope/subsystem;
- **phase markers** — `(Phase 6.1)`, `(Phase 3)` in the subject tie commits into one multi-phase effort;
- **branch** — commits sharing an in-flight branch are one workstream.

For each workstream capture: a **name**, the **subsystem**, whether it's **in-flight** (has an unmerged
branch or an open ready PR) or **done** (all merged), and a one-line **what**.

## Attach a resume hash to each workstream

Map every workstream to the Codex session that drove it, so each line ends in a `Codex --resume <id>`.

- **Match on the `Preview`, not the `Branch`.** Tommy works in git worktrees, so a session's `Branch`
  is often just whatever the *main* repo sat on at the time — unrelated to what the session actually
  did. The `Preview` (first user message) names the plan / worktree / feature and is the reliable key.
  Use `Branch` only as a tiebreaker.
- **One resume target per workstream:** the **most recent** matching session, preferring higher `Msgs`
  when two are close in time (that's the substantive one, not a quick offshoot).
- If a workstream's **design/origin** session is clearly distinct from where it was last worked
  (e.g. a big "look into X / design Y" session that later split into execution sessions), note that
  origin id too — sometimes Tommy wants to resume the thinking, not the last edit.
- No session matches a workstream → say so; don't force a wrong id onto it.

## Report

**Every `Codex --resume <id>` goes on its OWN line — never inline in a sentence, never trailing a
bullet after a `·`.** Put it in a fenced block on the line directly under the workstream it belongs to.
This is the one hard formatting rule of this skill; a resume hash buried mid-prose is unusable.

Open with the **Resume these** block — the whole point of the skill, so it comes first, before any
prose:

````
## Resume these

```
Codex --resume <id>   # <workstream name> — <3-6 words on what's left>
Codex --resume <id>   # <workstream name> — <3-6 words on what's left>
```
````

One line per **unfinished** workstream (unmerged branch, open PR, uncommitted worktree, or a plan with
outstanding phases), most-urgent first. Nothing else in that block — no merged work, no branch names,
no `git switch`. If Tommy reads only this block, he has what he needs.

Then the detail, in the same order:

**🔧 Still open (pick back up here)** — every unfinished workstream, most-urgent first. Per entry:
name · branch (`N ahead`) / PR # · what's actually left to do · then the resume command on its own
line in a fenced block, plus `git switch <branch>` (or the plan file if design-stage).

**✅ Landed recently** — merged workstreams, one line each. Resume ids here go in a single fenced
block at the end of the section (same one-per-line shape), not inline on the bullets.

**⚠️ Needs attention** — only if found: red platform-sync PR, an open draft that's gone stale, a
branch far ahead with no PR. Skip the heading entirely if nothing qualifies.

## Rules

- **Unfinished first.** An unmerged branch or open ready PR is worth ten merged commits here — that's
  what "what was I working on" is really asking. Rank by open-then-recent, never by commit count.
- **Check every in-flight worktree for uncommitted work** (`git -C <worktree> status --short`) before
  judging a branch's state. A branch whose commits look thin can be hiding the entire feature
  uncommitted on disk — that's the most at-risk item there is, and it must reach the resume block.
- Don't dump raw `git log`. If a workstream is one commit, one line; if it's fifteen across three
  phases, still one line (name it, note the phase span).
- Trust the phase markers in commit subjects for "how far along" — but state the phase as written
  (a `(Phase 6.2)` commit means Phase 6 is in progress, Phase 5 shipped); don't infer beyond them.
- `gh` may be absent or the repo non-GitHub — the PR/sync steps fail quietly; carry on with git-only
  data and say PR state was unavailable rather than inventing it.
- The resume-hash step depends on `Get-LastClaudeConversation.ps1` in `~/.Codex`. If it's missing or
  returns nothing for this project, drop the `Codex --resume` bit and fall back to `git switch` —
  don't guess a session id.
- Keep it tight — this is a standup-style recap, not a report. No preamble.
