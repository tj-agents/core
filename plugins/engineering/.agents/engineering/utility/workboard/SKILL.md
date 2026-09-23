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

`~/.claude/plans/<project>/*.md`, plus loose `*.md` at the root and the contents of any **flat**
subfolder — one with no subdirectories of its own, like `Concertable/Post Launch Scalability/`.

A subfolder that has its own directory structure is a **copied repository tree**, and it is skipped
whole: `Concertable/pristine/` is an entire checkout, `Concertable/b2b/` mirrors the b2b repo. Their
`AGENTS.md`, `TECH_DEBT.md`, `ARCHITECTURE.md` and `reviews/` are most of the files on disk and none
of them are plans. Flatness is the test because a plan folder is flat and a checkout never is.

**The known cost: a plan someone dropped inside a mirror is invisible here** — `Concertable/b2b/`
holds two. Move such a file up to its project directory rather than teaching this to guess.

**One project spans several directories**: Concertable plans sit in `Concertable/`, `b2b/`, `system/`,
`platform-dotnet/` and `agent-standards/`.

Which directories belong together is **read from the repo layout, never hardcoded**: a plan directory
belongs to the container under `~/source/repos` that holds a repo of that name, so `b2b` and
`platform-dotnet` resolve to `Concertable`, `cris-*` resolve to `infonetica`, and a repo sitting
directly under `repos/` is its own group. A new sibling repo joins its group by existing.

**The invoking repo's group is the default scope, and it is not cosmetic.** Work plans must never be
listed into a personal session, or the reverse. Out-of-group matches are counted and named in one
line and never listed; `SCOPE=all` prints them. They are matched on directory and filename alone and
never read, so another company's prose does not enter this session at all. **A loose plan at the root
has no project directory, so it has no group** — it is `unfiled`, counted with the rest and shown only
under `SCOPE=all`, because one of them really is work material.

## What the filter matches

`FILTER` finds plans **about** a subject, not filenames that happen to contain the exact letters.
Three rules, all deliberately blunt:

**Both sides are split into words.** The needle is tokenized exactly like the text, so `AB-28884`,
`pr-633` and a stray leading space all work; every word you type must match something, so
`b2b accept` finds `B2B_ACCEPT_UNION_HANDOFF`. Matching the raw needle against words was the old bug:
any punctuation at all silently matched nothing.

**The needle leads: a word starts with it, or shares a stem with it.** `auth` finds `authorization`.
`authz` does **not** find `auth` — a word standing in for a longer needle made the auth *service* the
answer to a search for authorization. A stem match needs five shared leading characters and at most
three left over on each side, which gets `tenant` to `tenancy` without getting `authorization` to
`authored`. Those bounds are also why `postgres` does not match a stray `pos`.

**A name outranks a mention.** A plan's directory, filename and title say what it is about; its body
merely mentions things. Only name hits are listed. Text-only hits are counted in one line, and are
listed instead only when no *open* plan is named for the needle — so the filter never answers zero
while something matched, and never reports a passing mention as a plan about the subject. When every
plan named for the subject is finished, it says that rather than pretending none exists.

## Gather

```bash
python - "${FILTER:-}" "${LIMIT:-20}" "${SCOPE:-auto}" <<'PY'
import pathlib, re, sys, time

root = pathlib.Path.home() / ".claude" / "plans"
repos = pathlib.Path.home() / "source" / "repos"
limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].strip().isdigit() else 20
scope = (sys.argv[3] if len(sys.argv) > 3 else "auto").lower()
here = pathlib.Path.cwd()
SKIP = {".git", "node_modules"}

WORD = re.compile(r'[a-z0-9]+')

def words(text):
    return WORD.findall(re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text).lower())

needle = words(sys.argv[1] if len(sys.argv) > 1 else "")
subject = " ".join(needle)

def akin(word, part):
    if word.startswith(part):
        return True
    shared = 0
    while shared < min(len(word), len(part)) and word[shared] == part[shared]:
        shared += 1
    return shared >= 5 and len(word) - shared <= 3 and len(part) - shared <= 3

def about(text):
    found = words(text)
    return all(any(akin(w, part) for w in found) for part in needle)

def is_repo(path):
    return (path / ".git").exists()

def group_of(project):
    if (repos / project).is_dir():
        return project
    if repos.is_dir():
        for container in repos.iterdir():
            if container.is_dir() and not is_repo(container) and is_repo(container / project):
                return container.name
    return None

def plan_files():
    """The root, each project directory, and any flat subfolder. A subfolder with its own
    directories is a copied repository tree and is skipped whole."""
    yield from root.glob("*.md")
    for project in root.glob("*"):
        if not project.is_dir() or project.name in SKIP:
            continue
        yield from project.glob("*.md")
        for sub in project.iterdir():
            if sub.is_dir() and sub.name not in SKIP \
                    and not any(child.is_dir() for child in sub.iterdir()):
                yield from sub.glob("*.md")

mine = None
for parent in [here, *here.parents]:
    if parent.parent == repos:
        mine = parent.name
        break

DONE = re.compile(r'^\s*(?:\*\*)?status(?:\*\*)?\s*[:=]\s*(?:\*\*)?\s*(complete|done|landed|closed|shipped)', re.I | re.M)
# The keyword carries prose before its colon: "**Waiting on Tommy, and it is ...:** mint a token"
NEXT = re.compile(r'^\s*[-*]?\s*\*\*(?:next|blocked|waiting|remaining|todo)\b[^*]*\*\*:?\s*(.+)', re.I | re.M)
RESOLVES = re.compile(r'\*\*resolves when:?\*\*:?\s*(.+)', re.I)
OPEN_BOX = re.compile(r'^\s*[-*]\s*\[ \]', re.M)
DONE_BOX = re.compile(r'^\s*[-*]\s*\[[xX]\]', re.M)

named, mentioned, hidden, elsewhere = [], [], 0, {}
named_seen = False
for path in plan_files():
    rel = path.relative_to(root)
    loose = len(rel.parts) == 1
    folder = "" if loose else str(rel.parent).replace("\\", "/")
    label = "(loose)" if loose else rel.parent.name
    group = "unfiled" if loose else group_of(rel.parts[0])
    if scope != "all" and mine and group and group != mine:
        if about(folder) or about(path.stem):
            elsewhere[group] = elsewhere.get(group, 0) + 1
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        mtime = path.stat().st_mtime
    except OSError:
        continue
    title = next((line for line in text.splitlines() if line.lstrip().startswith("#")), "")
    if about(folder) or about(path.stem) or about(title):
        bucket, is_named = named, True
        named_seen = True
    elif about(text):
        bucket, is_named = mentioned, False
    else:
        continue
    opens, dones = len(OPEN_BOX.findall(text)), len(DONE_BOX.findall(text))
    if opens:
        state = "live %d/%d" % (dones, dones + opens)
    elif DONE.search(text) or dones:
        if is_named:
            hidden += 1
        continue
    else:
        state = ""
    hit = NEXT.search(text) or RESOLVES.search(text)
    nxt = re.sub(r'\s+', ' ', hit.group(1)).strip()[:100] if hit else ""
    bucket.append((mtime, state, label, path.name, nxt))

rows = named or mentioned
rows.sort(reverse=True)
for mtime, state, label, name, nxt in rows[:limit]:
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
    print("%s  %-10s %-18s %s" % (stamp, state, label, name))
    if nxt:
        print("%30s -> %s" % ("", nxt))
print("")
print("scope: %s. %d open, showing %d. %d named and marked done, hidden." % (
    "all" if scope == "all" else (mine or "all (cwd outside source/repos)"),
    len(rows), min(limit, len(rows)), hidden))
if needle:
    if named and mentioned:
        print("%d more mention '%s' only in their text - not plans about it." % (len(mentioned), subject))
    elif not named and named_seen:
        print("every plan named for '%s' is marked done%s." % (
            subject, "; these only mention it in their text" if mentioned else ""))
    elif not named and mentioned:
        print("no plan is named for '%s'; these only mention it in their text." % subject)
    elif not named:
        print("nothing in ~/.claude/plans is named for '%s'. Plans and roadmaps kept inside a repo"
              " are outside this corpus." % subject)
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

When a needle matches nothing at all the run says so and names the corpus it searched. Report that
verbatim rather than concluding the work does not exist — a plan or roadmap living in the repo it
concerns is invisible here, and `PLANS_AND_INSTRUCTIONS_MUST_BE_MACHINE_TRANSFERABLE.md` owns closing
that gap.

Nearly every row carries a blank state — only about one plan in forty uses checkboxes. That is not a
bug in the read: the corpus is prose handoffs. Say that plainly rather than implying every blank is
unknown-danger, and treat recency as the real signal.

## What this does not do

It reads plans, not roadmaps, and not git. A plan can look live because its work merged under a
different name — cross-check with `/unmerged` when a live-looking plan is suspiciously old.

State is inferred from prose, which is the underlying problem rather than a limitation of this skill.
The fix is tracked records with a real state field; see the plan-tracking handoff under
`~/.claude/plans/agent-workboard/`.

Grouping and the flatness test are both inferences over a machine-local corpus grouped by directory
name. `~/.claude/plans/base-agents/PLANS_AND_INSTRUCTIONS_MUST_BE_MACHINE_TRANSFERABLE.md` owns moving
plans into the repo they concern, which retires both — the repo becomes the grouping and a copied doc
tree has nowhere to sit. Keep this until that lands; do not design a competing mapping.
