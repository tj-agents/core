import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import time


root = Path.home() / ".claude" / "plans"
repos = Path.home() / "source" / "repos"
limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].strip().isdigit() else 20
scope = (sys.argv[3] if len(sys.argv) > 3 else "auto").lower()
here = Path.cwd()
SKIP = {".git", "node_modules"}
PLAN_DIRS = ("plans", "docs/plans")
NOT_PLANS = {"agents.md", "claude.md", "readme.md", "tech_debt.md", "technical_debt.md"}
WORK_ITEM_README = re.compile(
    r"^plans/features/([a-z0-9]+(?:-[a-z0-9]+)*)/work-items/"
    r"([a-z0-9]+(?:-[a-z0-9]+)*)/README\.md$")

WORD = re.compile(r"[a-z0-9]+")


def words(text):
    return WORD.findall(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text).lower())


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
    return all(any(akin(word, part) for word in found) for part in needle)


def is_repo(path):
    return (path / ".git").exists()


def package_root():
    skill = Path(__file__).resolve().parent.parent
    if skill.parent.name in {"skills", "codex-skills"}:
        return skill.parent.parent
    if (skill.parent.name == "utility" and skill.parent.parent.name == "workflow"
            and skill.parent.parent.parent.name == ".agents"):
        return skill.parents[3]
    raise RuntimeError("status capability failure: the script has no supported runtime anchor")


def owned_module(name, path):
    if not path.is_file():
        raise RuntimeError(f"status capability failure: own {name} is unavailable at {path}")
    spec = importlib.util.spec_from_file_location(f"workflow_status_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"status capability failure: own {name} cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (ImportError, OSError, ValueError) as error:
        raise RuntimeError(f"status capability failure: own {name} cannot be loaded: {error}") from error
    return module


def git(directory, *arguments):
    try:
        result = subprocess.run(["git", "-C", str(directory), *arguments],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"status repository identity unavailable: {error}") from error
    return result.stdout.strip() if result.returncode == 0 else None


def work_item_reader():
    package = package_root()
    runtime = package / ".agents/agent-store/runtime"
    store = owned_module("reader", runtime / "reader.py")
    identity = owned_module("repository_identity", runtime / "repository_identity.py")
    reader_type = getattr(store, "ReadOnlyWorkItemStore", None)
    if not all((callable(reader_type),
                callable(getattr(store, "StoreReadError", None)),
                callable(getattr(identity, "repository_identity", None)),
                callable(getattr(reader_type, "work_item", None)))):
        raise RuntimeError("status capability failure: own Agent Store reader lacks work-item support")
    return store, identity


def record_selection_reader():
    package = package_root()
    source = package / ".agents/hooks/problem_records.py"
    packaged = package / "hooks/problem_records.py"
    return owned_module("problem_records", source if source.is_file() else packaged)

def record_selection(directory):
    if not any((path / ".git").exists() for path in (directory, *directory.parents)):
        return None
    try:
        primary = records.primary_checkout(directory)
        selected = records.declaration(primary)
    except records.RecordError as error:
        raise RuntimeError("status record selection failed for %s: %s" % (directory, error)) from error
    return (primary, selected["provider"]) if selected else None


try:
    store, identity = work_item_reader()
    records = record_selection_reader()
    asked = record_selection(here)
except RuntimeError as error:
    print(error, file=sys.stderr)
    raise SystemExit(2)
selected_repositories = dict([asked]) if asked else {}
skipped = []


def group_of(project):
    if (repos / project).is_dir():
        return project
    if repos.is_dir():
        for container in repos.iterdir():
            if container.is_dir() and not is_repo(container) and is_repo(container / project):
                return container.name
    return None


mine = None
for parent in [here, *here.parents]:
    if parent.parent == repos:
        mine = parent.name
        break


def local_plans():
    """The root, each project directory, and any flat subfolder. A subfolder with its own
    directories is a copied repository tree and is skipped whole."""
    for path in root.glob("*.md"):
        yield path, "", "(loose)", "unfiled"
    for project in root.glob("*"):
        if not project.is_dir() or project.name in SKIP:
            continue
        group = group_of(project.name)
        for path in project.glob("*.md"):
            yield path, project.name, project.name, group
        for sub in project.iterdir():
            if sub.is_dir() and sub.name not in SKIP and not any(
                    child.is_dir() for child in sub.iterdir()):
                for path in sub.glob("*.md"):
                    yield path, project.name + "/" + sub.name, sub.name, group


def repo_plans():
    """Plans kept in the repo they concern. Only the invoking group's repos are opened, so another
    group's work never enters the session."""
    home = repos / mine if mine else None
    if not home or not home.is_dir():
        return
    members = [home] if is_repo(home) else [
        child for child in home.iterdir() if child.is_dir() and is_repo(child)]
    current = here.resolve()
    for member in members:
        if member.resolve() == current or member.resolve() in current.parents:
            selection = asked
        else:
            try:
                selection = record_selection(member)
            except RuntimeError as error:
                skipped.append(str(error))
                continue
        if selection:
            selected_repositories[selection[0]] = selection[1]
        for relative in PLAN_DIRS:
            first = member.joinpath(*relative.split("/"))
            if not first.is_dir():
                continue
            canonical_plans = relative == "plans" and any(
                child.is_dir() and child.name == "plans" for child in member.iterdir())
            for path in sorted(first.rglob("*.md")):
                parts = path.relative_to(first).parts
                relative_path = path.relative_to(member).as_posix()
                item = WORK_ITEM_README.fullmatch(relative_path) if canonical_plans else None
                if any(part in SKIP for part in parts) or (path.name.lower() in NOT_PLANS and item is None):
                    continue
                topic = parts[-2] if len(parts) > 1 else ""
                label = topic or member.name
                yield path, member.name + ("/" + topic if topic else ""), label, mine, member, item, selection


def plan_entries():
    yield from local_plans()
    yield from repo_plans()


DONE = re.compile(r"^\s*(?:\*\*)?status(?:\*\*)?\s*[:=]\s*(?:\*\*)?\s*(complete|done|landed|closed|shipped)", re.I | re.M)
NEXT = re.compile(r"^\s*[-*]?\s*\*\*(?:next|blocked|waiting|remaining|todo)\b[^*]*\*\*:?\s*(.+)", re.I | re.M)
RESOLVES = re.compile(r"\*\*resolves when:?\*\*:?\s*(.+)", re.I)
OPEN_BOX = re.compile(r"^\s*[-*]\s*\[ \]", re.M)
OPEN_ITEM = re.compile(r"^[ \t]*[-*][ \t]*\[ \][ \t]*(.+(?:\n[ \t]+\S.*)*)", re.M)
DONE_BOX = re.compile(r"^\s*[-*]\s*\[[xX]\]", re.M)

named, mentioned, hidden, elsewhere = [], [], 0, {}
named_seen = False
repositories = {}
for entry in plan_entries():
    path, folder, label, group = entry[:4]
    member, item, selection = entry[4:] if len(entry) > 4 else (None, None, None)
    work_item_key = "%s/%s" % item.groups() if item is not None else ""
    if scope != "all" and mine and group and group != mine:
        if about(folder) or about(path.stem) or (work_item_key and about(work_item_key)):
            elsewhere[group] = elsewhere.get(group, 0) + 1
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        mtime = path.stat().st_mtime
    except OSError:
        continue
    title = next((line for line in text.splitlines() if line.lstrip().startswith("#")), "")
    if about(folder) or about(path.stem) or about(title) or (work_item_key and about(work_item_key)):
        bucket, is_named = named, True
        named_seen = True
    elif about(text):
        bucket, is_named = mentioned, False
    else:
        continue
    status_reason = ""
    work_item = work_item_key
    if selection and item is not None:
        state = "supporting"
    elif item is not None:
        relative_path = path.relative_to(member).as_posix()
        work_item = work_item_key
        try:
            repository = repositories.get(member)
            if repository is None:
                repository = identity.repository_identity(member, git)
                if repository is None:
                    raise RuntimeError("work-item repository identity is unavailable")
                repositories[member] = repository
            state = store.ReadOnlyWorkItemStore().work_item(f"{repository}:{work_item_key}")["status"]
            if state == "done":
                if is_named:
                    hidden += 1
                continue
        except (store.StoreReadError, RuntimeError) as error:
            state = "unknown"
            status_reason = str(error)
    else:
        opens, dones = len(OPEN_BOX.findall(text)), len(DONE_BOX.findall(text))
        if not opens and (DONE.search(text) or dones):
            if is_named:
                hidden += 1
            continue
        if selection:
            state = "supporting"
        elif opens:
            state = "live %d/%d" % (dones, dones + opens)
        else:
            state = ""
    hit = NEXT.search(text) or RESOLVES.search(text) or OPEN_ITEM.search(text)
    nxt = re.sub(r"\s+", " ", hit.group(1)).strip()[:160] if hit else ""
    bucket.append((mtime, state, label, path.name, nxt, status_reason, work_item))

rows = named or mentioned
rows.sort(reverse=True)
for mtime, state, label, name, nxt, status_reason, work_item in rows[:limit]:
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
    key = " %s" % work_item if work_item else ""
    print("%s  %-10s %-18s%s %s" % (stamp, state, label, key, name))
    if status_reason:
        print("%30s -> status unknown: %s" % ("", status_reason))
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
        print("nothing in scope is named for '%s'; ~/.claude/plans is the whole corpus, so a plan or"
              " roadmap kept inside a repo is never searched." % subject)
for group, count in sorted(elsewhere.items(), key=lambda value: -value[1]):
    print("out of scope: %d in %s - rerun with the scope argument all to include." % (count, group))
for primary, provider in sorted(selected_repositories.items()):
    print("selected provider: %s owns live work items for %s; use its list/read commands."
          " Its plans above are supporting context." % (provider, primary))
for reason in skipped:
    print("skipped: %s" % reason)
