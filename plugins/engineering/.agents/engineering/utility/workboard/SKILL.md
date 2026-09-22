---
name: workboard
description: List every plan across every project and say which are still awaiting continuation — reads the plan files themselves, not git, so work that has gone cold for days still shows up. Use whenever Tommy says "/workboard", "what work do I have open", "what plans are still going", "what have I not finished", "what else is active", or has lost track of which session he was on. Optional filter narrows to plans about one subject.

kind: utility
domain: process
---

# every plan across every project, and which still await continuation

Answer "what work have I got open?" by reading the plan corpus directly.

This exists because `/recents` and `/unmerged` both mine **git**, so a plan nobody has committed
against for two days is invisible to them — which is exactly when it is needed. Read the files.

## Where plans live, and which of them are yours right now

`~/.claude/plans/<project>/*.md`, plus loose `*.md` at the root. **The corpus is one directory deep,
and that is the rule for what counts as a plan.** Anything nested further is a copied repository
tree: `Concertable/pristine/` is a whole checkout, `Concertable/b2b/src/**` mirrors the b2b repo, and
the hundreds of files down there are those repos' own `AGENTS.md`, `TECH_DEBT.md`, `ARCHITECTURE.md`
and `reviews/`. They are four fifths of the files and none of them are plans, so the walk never
descends past one level — which is also what keeps this a single-shot read.

**One project spans several directories**: Concertable plans sit in `Concertable/`, `b2b/`, `system/`,
`platform-dotnet/` and `agent-standards/`.

Which directories belong together is **read from the repo layout, never hardcoded**: a plan directory
belongs to the container under `~/source/repos` that holds a repo of that name, so `b2b` and
`platform-dotnet` resolve to `Concertable`, `cris-*` resolve to `infonetica`, and a repo sitting
directly under `repos/` is its own group. A new sibling repo joins its group by existing.

**The invoking repo's group is the default scope, and it is not cosmetic.** Work plans must never be
listed into a personal session, or the reverse. Out-of-group matches are counted and named in one
line and never listed; `SCOPE=all` prints them. They are matched on project and filename alone and
never read, so another company's prose does not enter this session at all.

## What the filter matches

`FILTER` finds plans **about** a subject, not filenames that happen to contain the exact letters.
Two rules, both deliberately blunt:

**Whole words, prefixed either way, or sharing five letters.** The needle matches a word when one is
a prefix of the other — `auth` finds `authorization`, `authz` finds `auth` — or when the two agree on
their first five characters, which is what gets `tenant` to `tenancy`. A word must be at least four
characters to stand in for a longer needle. Between them those floors are why `postgres` does not
match a stray `pos` and `authz` does not match `authored`.

**A name outranks a mention.** A plan's project directory, filename and title say what it is about;
its body merely mentions things. Only name hits are listed. Text-only hits are counted in one line,
and are listed instead only when nothing is named for the needle — so the filter never answers zero
while something matched, and never reports a passing mention as a plan about the subject.

## Gather

```bash
python - "${FILTER:-}" "${LIMIT:-20}" "${SCOPE:-auto}" <<'PY'
import pathlib, re, sys, time

root = pathlib.Path.home() / ".claude" / "plans"
repos = pathlib.Path.home() / "source" / "repos"
needle = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
limit = int(sys.argv[2] or 20)
scope = (sys.argv[3] if len(sys.argv) > 3 else "auto").lower()
here = pathlib.Path.cwd()

def is_repo(path):
    return (path / ".git").exists()

def group_of(project):
    if (repos / project).is_dir():
        return project
    for container in repos.iterdir():
        if container.is_dir() and not is_repo(container) and is_repo(container / project):
            return container.name
    return None

mine = None
for parent in [here, *here.parents]:
    if parent.parent == repos:
        mine = parent.name
        break

WORD = re.compile(r'[a-z0-9]+')

def words(text):
    return WORD.findall(re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text).lower())

def matches(word):
    return (word.startswith(needle)
            or (len(word) >= 4 and needle.startswith(word))
            or (len(word) >= 5 and len(needle) >= 5 and word[:5] == needle[:5]))

def about(text):
    return any(matches(w) for w in words(text))

DONE = re.compile(r'^\s*(?:\*\*)?status(?:\*\*)?\s*[:=]\s*(?:\*\*)?\s*(complete|done|landed|closed|shipped)', re.I | re.M)
# The keyword carries prose before its colon: "**Waiting on Tommy, and it is ...:** mint a token"
NEXT = re.compile(r'^\s*[-*]?\s*\*\*(?:next|blocked|waiting|remaining|todo)\b[^*]*\*\*:?\s*(.+)', re.I | re.M)
RESOLVES = re.compile(r'\*\*resolves when:?\*\*:?\s*(.+)', re.I)
OPEN_BOX = re.compile(r'^\s*[-*]\s*\[ \]', re.M)
DONE_BOX = re.compile(r'^\s*[-*]\s*\[[xX]\]', re.M)

named, mentioned, hidden, elsewhere = [], [], 0, {}
for path in [*root.glob("*.md"), *root.glob("*/*.md")]:
    loose = path.parent == root
    project = "(loose)" if loose else path.parent.name
    group = None if loose else group_of(project)
    if scope != "all" and mine and group and group != mine:
        if not needle or about(project) or about(path.stem):
            elsewhere[group] = elsewhere.get(group, 0) + 1
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    title = next((line for line in text.splitlines() if line.lstrip().startswith("#")), "")
    if not needle or about(project) or about(path.stem) or about(title):
        bucket = named
    elif about(text):
        bucket = mentioned
    else:
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
    bucket.append((path.stat().st_mtime, state, project, path.name, nxt))

rows = named or mentioned
rows.sort(reverse=True)
for mtime, state, project, name, nxt in rows[:limit]:
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
    print("%s  %-10s %-18s %s" % (stamp, state, project, name))
    if nxt:
        print("%30s -> %s" % ("", nxt))
print("")
print("scope: %s. %d open, showing %d. %d marked done, hidden." % (
    "all" if scope == "all" else (mine or "all (cwd outside source/repos)"),
    len(rows), min(limit, len(rows)), hidden))
if needle and named and mentioned:
    print("%d more mention '%s' only in their text - not plans about it." % (len(mentioned), needle))
if needle and not named and mentioned:
    print("no plan is named for '%s'; these only mention it in their text." % needle)
for group, count in sorted(elsewhere.items(), key=lambda kv: -kv[1]):
    print("out of scope: %d in %s - rerun with SCOPE=all to include." % (count, group))
PY
```

`FILTER` narrows, `LIMIT` lengthens, `SCOPE=all` crosses groups — `FILTER=postgres`, `LIMIT=40`.

## Report

Lead with the list as printed, most recent first. Call out the top few by name in prose and say what
each is, because the filename alone rarely says it.

**Read the out-of-scope lines out, do not expand them.** "18 matches in infonetica, outside this
repo" is the whole report for another group's work; naming the files puts work material into a
personal session, which is the failure this scoping exists to stop. Only an explicit `SCOPE=all`
changes that.

The mention count is the same kind of line — read it, do not go looking. When the run fell back to
text-only matches it says so, and those rows are plans that mention the subject rather than plans
about it. Say which of the two you are reporting.

Most rows carry a blank state. That is not a bug in the read: the corpus is prose handoffs, and only
about one in eight uses checkboxes. Say that plainly rather than implying every blank is unknown-danger,
and treat recency as the real signal.

## What this does not do

It reads plans, not roadmaps, and not git. A plan can look live because its work merged under a
different name — cross-check with `/unmerged` when a live-looking plan is suspiciously old.

State is inferred from prose, which is the underlying problem rather than a limitation of this skill.
The fix is tracked records with a real state field; see the plan-tracking handoff under
`~/.claude/plans/agent-workboard/`.

Grouping and the one-level depth rule are both inferences over a machine-local corpus grouped by
directory name. `~/.claude/plans/base-agents/PLANS_AND_INSTRUCTIONS_MUST_BE_MACHINE_TRANSFERABLE.md`
owns moving plans into the repo they concern, which retires both — the repo becomes the grouping and
a copied doc tree has nowhere to sit. Keep this until that lands; do not design a competing mapping.
