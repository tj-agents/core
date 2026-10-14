import importlib.util
from pathlib import Path
import re
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


def workflow_root():
    script = Path(__file__).resolve()
    skill_directory = script.parent.parent
    if (script.parent.name == "scripts" and skill_directory.parent.name == "utility"
            and skill_directory.parent.parent.name == "engineering"
            and skill_directory.parent.parent.parent.name == ".agents"):
        package_root = skill_directory.parents[3]
        candidates = (package_root / ".agents" / "workflows", package_root / "workflows")
    elif script.parent.name == "scripts" and skill_directory.parent.name in {"skills", "codex-skills"}:
        candidates = (skill_directory.parent.parent / "workflows",)
    else:
        raise RuntimeError("list-work capability failure: the script has no supported runtime anchor")
    for workflows in candidates:
        if (workflows / "workflow_runtime.py").is_file():
            return workflows
    raise RuntimeError("list-work capability failure: own workflow runtime is unavailable")


def work_item_reader():
    workflows = workflow_root()
    runtime_path = workflows / "workflow_runtime.py"
    spec = importlib.util.spec_from_file_location("list_work_workflow_runtime", runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("list-work capability failure: own workflow runtime cannot be loaded")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    provider_type = getattr(runtime, "RepositoryStateProvider", None)
    contract_type = getattr(runtime, "WorkflowContract", None)
    violation_type = getattr(runtime, "ContractViolation", None)
    if not all((callable(provider_type), callable(contract_type), callable(violation_type))):
        raise RuntimeError("list-work capability failure: own workflow runtime lacks work-item status support")
    if not callable(getattr(provider_type, "work_item_status", None)):
        raise RuntimeError("list-work capability failure: own workflow runtime lacks work-item status support")
    try:
        contract = contract_type(workflows)
    except (OSError, ValueError, KeyError) as error:
        raise RuntimeError("list-work capability failure: own workflow contract is unavailable") from error
    return runtime, contract


try:
    runtime, contract = work_item_reader()
except RuntimeError as error:
    print(error, file=sys.stderr)
    raise SystemExit(2)


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
    for member in members:
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
                yield path, member.name + ("/" + topic if topic else ""), label, mine, member, item


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
providers = {}
for entry in plan_entries():
    path, folder, label, group = entry[:4]
    member, item = entry[4:] if len(entry) > 4 else (None, None)
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
    work_item = ""
    if item is not None:
        relative_path = path.relative_to(member).as_posix()
        work_item = work_item_key
        try:
            provider = providers.get(member)
            if provider is None:
                provider = runtime.RepositoryStateProvider(member, contract)
                providers[member] = provider
            state = provider.work_item_status(relative_path)
            if state not in {"proposed", "active", "delivery-gated", "blocked", "paused", "done"}:
                raise runtime.ContractViolation("work-item status is unavailable")
            if state == "done":
                if is_named:
                    hidden += 1
                continue
        except runtime.ContractViolation as error:
            state = "unknown"
            status_reason = str(error)
    else:
        opens, dones = len(OPEN_BOX.findall(text)), len(DONE_BOX.findall(text))
        if opens:
            state = "live %d/%d" % (dones, dones + opens)
        elif DONE.search(text) or dones:
            if is_named:
                hidden += 1
            continue
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
    print("out of scope: %d in %s - rerun with SCOPE=all to include." % (count, group))
