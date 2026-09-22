---
name: workboard
description: List every plan across every project and say which are still awaiting continuation — reads the plan files themselves, not git, so work that has gone cold for days still shows up. Use whenever Tommy says "/workboard", "what work do I have open", "what plans are still going", "what have I not finished", "what else is active", or has lost track of which session he was on. Optional filter narrows to one project.

kind: utility
domain: process
---

# every plan across every project, and which still await continuation

Answer "what work have I got open?" by reading the plan corpus directly.

This exists because `/recents` and `/unmerged` both mine **git**, so a plan nobody has committed
against for two days is invisible to them — which is exactly when it is needed. Read the files.

## Where plans live

`~/.claude/plans/<project>/*.md`, plus loose `*.md` at the root. **One project spans several
directories**: Concertable work sits in `Concertable/`, `b2b/`, `system/`, `platform-dotnet/` and
`agent-standards/`. Never answer "what is active on X" from a single directory — filter instead, which
matches project *and* filename.

## Gather

```bash
python - "${FILTER:-}" "${LIMIT:-20}" <<'PY'
import pathlib, re, sys, time

root = pathlib.Path.home() / ".claude" / "plans"
needle = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
limit = int(sys.argv[2] or 20)

DONE = re.compile(r'^\s*(?:\*\*)?status(?:\*\*)?\s*[:=]\s*(?:\*\*)?\s*(complete|done|landed|closed|shipped)', re.I | re.M)
# The keyword carries prose before its colon: "**Waiting on Tommy, and it is ...:** mint a token"
NEXT = re.compile(r'^\s*[-*]?\s*\*\*(?:next|blocked|waiting|remaining|todo)\b[^*]*\*\*:?\s*(.+)', re.I | re.M)
RESOLVES = re.compile(r'\*\*resolves when:?\*\*:?\s*(.+)', re.I)
OPEN_BOX = re.compile(r'^\s*[-*]\s*\[ \]', re.M)
DONE_BOX = re.compile(r'^\s*[-*]\s*\[[xX]\]', re.M)

rows, hidden = [], 0
for path in root.rglob("*.md"):
    if any(part in {".git", "node_modules"} for part in path.parts):
        continue
    project = path.parent.name if path.parent != root else "(loose)"
    if needle and needle not in project.lower() and needle not in path.name.lower():
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    opens, dones = len(OPEN_BOX.findall(text)), len(DONE_BOX.findall(text))
    if opens:
        state = "live %d/%d" % (dones, dones + opens)
    elif DONE.search(text) or dones:
        hidden += 1
        continue
    else:
        state = ""
    hit = NEXT.search(text) or RESOLVES.search(text)
    nxt = re.sub(r'\s+', ' ', hit.group(1)).strip()[:100] if hit else ""
    rows.append((path.stat().st_mtime, state, project, path.name, nxt))

rows.sort(reverse=True)
for mtime, state, project, name, nxt in rows[:limit]:
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
    print("%s  %-10s %-18s %s" % (stamp, state, project, name))
    if nxt:
        print("%30s -> %s" % ("", nxt))
print("")
print("%d open, showing %d. %d marked done, hidden." % (len(rows), min(limit, len(rows)), hidden))
PY
```

`FILTER` narrows, `LIMIT` lengthens — `FILTER=concertable`, `FILTER=authz`, `LIMIT=40`.

## Report

Lead with the list as printed, most recent first. Call out the top few by name in prose and say what
each is, because the filename alone rarely says it.

**Flag the split.** When one logical project's plans span several directories, say so — that is the
thing that loses work.

Most rows carry a blank state. That is not a bug in the read: the corpus is prose handoffs, and only
about one in eight uses checkboxes. Say that plainly rather than implying every blank is unknown-danger,
and treat recency as the real signal.

## What this does not do

It reads plans, not roadmaps, and not git. A plan can look live because its work merged under a
different name — cross-check with `/unmerged` when a live-looking plan is suspiciously old.

State is inferred from prose, which is the underlying problem rather than a limitation of this skill.
The fix is tracked records with a real state field; see the plan-tracking handoff under
`~/.claude/plans/agent-workboard/`.
