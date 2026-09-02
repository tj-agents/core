import argparse
import json
import re
import sys
from pathlib import Path


TERMINAL = {
    "",
    "closed",
    "complete",
    "completed",
    "done",
    "n/a",
    "na",
    "none",
    "nothing",
    "terminal",
}
LEDGER_MAX_LINES = 200
LEDGER_MAX_BYTES = 16000
BLOCKER_FIELDS = ("Blocked", "Blocked by", "Unblock action", "Resume when")
BLOCKED_OR_WAITING = re.compile(r"\b(?:blocked|waiting)\b", re.IGNORECASE)
REGISTERED_OWNER_WAIT = re.compile(r"\bdownstream handoffs\b", re.IGNORECASE)
SUPPRESS_RESUME_PROMPT = re.compile(
    r"\bdo not\b(?:(?![.!?](?:\s|$)).){0,240}"
    r"\b(?:emit|include|surface)\b(?:(?![.!?](?:\s|$)).){0,120}"
    r"\b(?:resume|continuation|handoff)(?:\s+prompt)?\b",
    re.IGNORECASE | re.DOTALL,
)
LEDGER_REFERENCE = re.compile(
    r"plans[\\/][A-Za-z0-9_.() \\/-]+?_PROGRESS\.md",
    re.IGNORECASE,
)
# A merge of THIS PR — not "merge origin/main" / "merge main" (that is a branch sync).
MERGE_INTENT = re.compile(
    r"/merge\b|gh pr merge|\bmerge[ -]?queue\b|\benqueue\b|"
    r"\bmerge\b(?!\s+(?:origin/|current\s+)?`?main`?\b)",
    re.IGNORECASE,
)
REVIEW_STEP = re.compile(r"/(?:incremental-|big-|security-)?review\b|\breview\b", re.IGNORECASE)
# A recorded review can live in `## Reviews` or in an established watermark/record form.
REVIEW_EVIDENCE = re.compile(
    r"review[\w /&-]{0,40}watermark|review record commit|reviewed[^.\n]{0,80}no open findings",
    re.IGNORECASE,
)


def section(text, name):
    match = re.search(
        rf"^##+\s*{re.escape(name)}\s*$(.*?)(^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def next_steps(text):
    return section(text, "Next Steps")


def metadata(text, name):
    match = re.search(rf"^- {re.escape(name)}:\s*`?([^`\r\n]+)`?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def is_terminal(body):
    if body is None:
        return True
    normalized = re.sub(r"[`*_#>\-\s.]", "", body).lower()
    return not normalized or normalized in TERMINAL


def is_paused(body):
    if body is None:
        return False
    first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
    return first_line.lower().startswith("paused:")


def review_recorded(text):
    body = section(text, "Reviews")
    if body is not None:
        normalized = re.sub(r"[`*_#>\-\s.]", "", body).lower()
        if normalized not in {"", "none", "noneyet", "na", "tbd"}:
            return True
    return REVIEW_EVIDENCE.search(text) is not None


def review_gate_error(path, body, text):
    if body is None:
        return None
    merge = MERGE_INTENT.search(body)
    if not merge:
        return None
    review = REVIEW_STEP.search(body)
    if review is not None and review.start() < merge.start():
        return None
    if review_recorded(text):
        return None
    return (
        f"{path.name}: `## Next Steps` proposes a merge (`{merge.group(0).strip()}`) with no `/review` "
        "step before it and no review recorded in `## Reviews` — review is a mandatory pre-merge gate"
    )


def blocker_details(body):
    if body is None:
        return None
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if len(lines) < len(BLOCKER_FIELDS):
        return None
    values = []
    for line, name in zip(lines, BLOCKER_FIELDS):
        prefix = f"{name}:"
        if not line.startswith(prefix):
            return None
        value = line.removeprefix(prefix).strip()
        if not value:
            return None
        values.append(value)
    return tuple(values)


def looks_like_legacy_blocker(body):
    if body is None:
        return False
    first_line = next((line.strip().lower() for line in body.splitlines() if line.strip()), "")
    return (
        first_line.startswith("waiting for ")
        or first_line.startswith("blocked:")
        or (
            BLOCKED_OR_WAITING.search(body)
            and REGISTERED_OWNER_WAIT.search(body)
            and SUPPRESS_RESUME_PROMPT.search(body)
        )
    )


def ledger_root(path):
    for parent in path.parents:
        if parent.name.lower() == "plans":
            return parent.parent
    raise ValueError(f"Ledger is not below plans/: {path}")


def repo_relative_path(root, value, suffix):
    normalized = value.replace("\\", "/")
    candidate = (root / normalized).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"path escapes the repository: {value}") from error
    if not candidate.name.upper().endswith(suffix.upper()):
        raise ValueError(f"path must end with {suffix}: {value}")
    return candidate


def plan_path(path):
    root = ledger_root(path)
    text = path.read_text(encoding="utf-8")
    declared = metadata(text, "Plan")
    plan = (
        repo_relative_path(root, declared, "_PLAN.md")
        if declared
        else path.with_name(path.name.removesuffix("_PROGRESS.md") + "_PLAN.md")
    )
    if not plan.is_file():
        source = f"declared Plan `{declared}`" if declared else "legacy filename convention"
        raise ValueError(f"Missing companion plan for {path} from {source}: {plan}")
    if plan.parent != path.parent:
        raise ValueError(f"Plan and ledger must share an epic folder: {plan} and {path}")
    return plan


def roadmap_errors(path, text):
    root = ledger_root(path)
    roadmap = metadata(text, "Roadmap")
    item = metadata(text, "Roadmap item")
    if not roadmap and not item:
        return [f"{path.name}: `Roadmap:` and `Roadmap item:` are required"]
    if not roadmap or not item:
        return [f"{path.name}: `Roadmap:` and `Roadmap item:` must be declared together"]
    try:
        roadmap_path = repo_relative_path(root, roadmap, "_ROADMAP.md")
    except ValueError as error:
        return [f"{path.name}: {error}"]
    if not roadmap_path.is_file():
        return [f"{path.name}: declared roadmap does not exist: {roadmap}"]
    if roadmap_path.parent != path.parent:
        return [f"{path.name}: roadmap and ledger must share an epic folder: {roadmap}"]
    epic = path.parent.relative_to(root / "plans").as_posix()
    if not re.fullmatch(rf"{re.escape(epic)}/[a-z0-9]+(?:-[a-z0-9]+)*", item):
        return [f"{path.name}: roadmap item key must match `{epic}/<slug>`: {item}"]
    marker = f"`{item}`"
    roadmap_text = roadmap_path.read_text(encoding="utf-8")
    checklist_item = re.compile(
        rf"^(?:- \[[ xX]\].*|\|\s*\[[ xX]\]\s*\|.*){re.escape(marker)}.*$",
        re.MULTILINE,
    )
    matches = checklist_item.findall(roadmap_text)
    if not matches:
        return [f"{path.name}: roadmap item marker {marker} is missing from {roadmap}"]
    if len(matches) > 1:
        return [f"{path.name}: roadmap item marker {marker} is duplicated in {roadmap}"]
    return []


def blocker_owner_references(value):
    return tuple(
        dict.fromkeys(match.group(0).replace("\\", "/") for match in LEDGER_REFERENCE.finditer(value))
    )


def owner_ledger_path(waiting_path, reference, live_owners):
    root = ledger_root(waiting_path)
    owner = repo_relative_path(root, reference, "_PROGRESS.md")
    if not owner.is_file():
        raise ValueError(f"blocker owner ledger does not exist: {reference}")
    if not live_owners:
        return owner
    text = owner.read_text(encoding="utf-8")
    worktree = metadata(text, "Worktree")
    if not worktree:
        return owner
    live_root = Path(worktree)
    if not live_root.is_dir():
        return owner
    live_owner = live_root / owner.relative_to(root)
    return live_owner if live_owner.is_file() else owner


def blocker_registration_errors(path, blocked_by, live_owners):
    errors = []
    waiting_reference = path.relative_to(ledger_root(path)).as_posix().casefold()
    for reference in blocker_owner_references(blocked_by):
        try:
            owner = owner_ledger_path(path, reference, live_owners)
        except ValueError as error:
            errors.append(f"{path.name}: {error}")
            continue
        handoffs = section(owner.read_text(encoding="utf-8"), "Downstream handoffs")
        normalized = (handoffs or "").replace("\\", "/").casefold()
        if waiting_reference not in normalized:
            errors.append(
                f"{path.name}: blocker owner {reference} must list "
                f"{path.relative_to(ledger_root(path)).as_posix()} under `## Downstream handoffs`"
            )
        owner_steps = next_steps(owner.read_text(encoding="utf-8"))
        if is_terminal(owner_steps):
            errors.append(
                f"{path.name}: blocker owner {reference} is terminal; it must update and dispatch the dependent"
            )
    return errors


def terminal_handoff_errors(path, text, body):
    handoffs = section(text, "Downstream handoffs")
    if is_terminal(body) and handoffs and not is_terminal(handoffs):
        return [f"{path.name}: terminal ledger still has undispatched `## Downstream handoffs`"]
    return []


def ledger_errors(path, live_owners=True):
    errors = []
    text = path.read_text(encoding="utf-8")
    if not metadata(text, "Plan"):
        errors.append(f"{path.name}: `Plan:` is required")
    try:
        plan_path(path)
    except ValueError as error:
        errors.append(str(error))
    errors.extend(roadmap_errors(path, text))
    body = next_steps(text)
    if body is None:
        errors.append(f"{path.name} is missing its required `## Next Steps` section")
        return errors
    details = blocker_details(body)
    if details:
        errors.extend(blocker_registration_errors(path, details[1], live_owners))
    elif looks_like_legacy_blocker(body):
        fields = ", ".join(f"`{name}:`" for name in BLOCKER_FIELDS)
        errors.append(f"{path.name}: blocked work must begin with non-empty {fields} lines")
    else:
        gate = review_gate_error(path, body, text)
        if gate:
            errors.append(gate)
    errors.extend(terminal_handoff_errors(path, text, body))
    return errors


def repository_report(root):
    errors = []
    warnings = []
    claims = {}
    for path in sorted((root / "plans").rglob("*_PROGRESS.md")):
        errors.extend(ledger_errors(path, live_owners=False))
        text = path.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        byte_count = len(text.encode("utf-8"))
        if line_count > LEDGER_MAX_LINES or byte_count > LEDGER_MAX_BYTES:
            warnings.append(
                f"{path.name}: compact the current snapshot; {line_count} lines and {byte_count} bytes "
                f"exceed the {LEDGER_MAX_LINES}-line/{LEDGER_MAX_BYTES}-byte continuation budget"
            )
        claim = (metadata(text, "Roadmap"), metadata(text, "Roadmap item"))
        plan = metadata(text, "Plan")
        if all(claim) and plan:
            claims.setdefault(claim, {}).setdefault(plan, []).append(path)
    for (roadmap, item), plans in claims.items():
        if len(plans) > 1:
            owners = ", ".join(sorted(plans))
            errors.append(f"roadmap item `{item}` in {roadmap} has multiple plan owners: {owners}")
    return {"errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = repository_report(args.root.resolve())
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for level in ("errors", "warnings"):
            for message in report[level]:
                print(f"{level[:-1].upper()}: {message}")
        print(f"Plan graph: {len(report['errors'])} error(s), {len(report['warnings'])} warning(s)")
    raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
