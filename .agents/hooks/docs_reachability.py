import argparse
import json
import re
import sys
from pathlib import Path


REFERRER_NAMES = {"AGENTS.md", "CLAUDE.md", "SKILL.md"}
CLAUDE_BODY = "@AGENTS.md"
IGNORED_DIR_NAMES = {"node_modules", "bin", "obj", "dist", ".git"}
WORKING_DOC_DIRS = {"plans", "reviews"}
TEST_PROJECT_PATTERN = re.compile(r"<IsTestProject>\s*true\s*</IsTestProject>", re.IGNORECASE)
LINK_PATTERN = re.compile(r"\]\(([^)\s]+)\)")
FENCE_PATTERN = re.compile(r"^\s*(?:```|~~~)", re.MULTILINE)
AT_IMPORT_PATTERN = re.compile(r"(?<![\w@])@([\w./-]+\.md)")


def ignored(relative_path):
    return any(part in IGNORED_DIR_NAMES for part in relative_path.parts[:-1])


def hidden(relative_path):
    return any(part.startswith(".") for part in relative_path.parts[:-1])


def agents_md_files(root):
    return sorted(
        path
        for path in root.rglob("AGENTS.md")
        if not hidden(path.relative_to(root)) and not ignored(path.relative_to(root))
    )


def agents_dir_docs(root):
    return sorted(
        path
        for path in root.rglob("agents/*.md")
        if not hidden(path.relative_to(root)) and not ignored(path.relative_to(root))
    )


def all_md_files(root):
    return sorted(path for path in root.rglob("*.md") if not ignored(path.relative_to(root)))


def registered_agent_docs(root):
    docs = []
    for manifest in root.glob("plugins/*/workflows/hosts/claude.json"):
        try:
            host = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        directory = host.get("delivery", {}).get("plugin_directory")
        roles = host.get("roles", {})
        if not isinstance(directory, str) or not isinstance(roles, dict):
            continue
        plugin_root = manifest.parents[2].resolve()
        for role in roles.values():
            filename = role.get("filename") if isinstance(role, dict) else None
            if not isinstance(filename, str):
                continue
            target = (plugin_root / directory / filename).resolve()
            try:
                target.relative_to(plugin_root)
            except ValueError:
                continue
            if target.is_file():
                docs.append(target)
    return sorted(set(docs))


def repo_path(root, path):
    return path.relative_to(root).as_posix()


def resolve_reference(referrer, raw_ref):
    ref = raw_ref.strip().split("#", 1)[0].strip()
    if not ref or ref.startswith(("http://", "https://", "mailto:")):
        return None
    try:
        return (referrer.parent / ref).resolve()
    except OSError:
        return None


def without_fenced_blocks(text):
    out, fenced = [], False
    for line in text.splitlines():
        if FENCE_PATTERN.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def raw_references_in(path, skip_fenced=False):
    text = path.read_text(encoding="utf-8")
    if skip_fenced:
        text = without_fenced_blocks(text)
    for pattern in (LINK_PATTERN, AT_IMPORT_PATTERN):
        for match in pattern.finditer(text):
            raw = match.group(1)
            target = resolve_reference(path, raw)
            if target:
                yield raw, target


def references_in(path):
    return {target for _, target in raw_references_in(path)}


def sibling_errors(root):
    errors = []
    for path in agents_md_files(root):
        claude = path.with_name("CLAUDE.md")
        if not claude.is_file():
            errors.append(
                f"{repo_path(root, path)}: has no sibling CLAUDE.md "
                f"(every AGENTS.md must have a CLAUDE.md containing exactly `{CLAUDE_BODY}`)"
            )
            continue
        body = claude.read_text(encoding="utf-8").strip()
        if body != CLAUDE_BODY:
            errors.append(
                f"{repo_path(root, claude)}: must contain exactly `{CLAUDE_BODY}`, found `{body}`"
            )
    return errors


def test_project_errors(root):
    """A test project with no stub at all is the state that made the tier question skippable.

    The incident folder had no `AGENTS.md`, so there was nowhere for a pointer or an import to live and
    nothing to read at the moment the tier was being chosen. `sibling_errors` then adds the CLAUDE.md
    half, so this only has to require the AGENTS.md.
    """
    errors = []
    for project in sorted(root.rglob("*.csproj")):
        relative = project.relative_to(root)
        if ignored(relative) or hidden(relative):
            continue
        try:
            body = project.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if not TEST_PROJECT_PATTERN.search(body):
            continue
        if not (project.parent / "AGENTS.md").is_file():
            errors.append(
                f"{repo_path(root, project)}: declares <IsTestProject>true</IsTestProject> but its "
                "directory has no AGENTS.md - every test project states its tier at the point of use "
                "(a test needing a host, HTTP or a database is an integration test, not a unit test)"
            )
    return errors


def reachable_docs(root):
    files = all_md_files(root)
    edges = {path.resolve(): references_in(path) for path in files}
    queue = [path.resolve() for path in files if path.name in REFERRER_NAMES]
    queue.extend(path.resolve() for path in registered_agent_docs(root))
    visited = set()
    while queue:
        current = queue.pop()
        if current in visited:
            continue
        visited.add(current)
        queue.extend(edges.get(current, ()))
    return visited


def orphan_errors(root):
    reachable = reachable_docs(root)
    errors = []
    for doc in agents_dir_docs(root):
        if doc.resolve() not in reachable:
            errors.append(
                f"{repo_path(root, doc)}: not reachable (by plain link or @-import, followed "
                "transitively) from any AGENTS.md, CLAUDE.md, or SKILL.md in the repository"
            )
    return errors


def dead_links(root):
    """Split dead references by whether the referring doc is durable guidance or a working doc.

    Guidance docs are load-bearing, so a dead reference there is an error. `plans/` and `reviews/`
    are working docs that get deleted once spent, and enforcing link integrity across them would
    fail the whole gate on churn nobody is reading.
    """
    errors, warnings = [], []
    for doc in all_md_files(root):
        relative = doc.relative_to(root)
        if hidden(relative) and doc.name not in REFERRER_NAMES:
            continue
        bucket = warnings if relative.parts[0] in WORKING_DOC_DIRS else errors
        for raw, target in sorted(set(raw_references_in(doc, skip_fenced=True))):
            if raw.startswith("/"):
                errors.append(
                    f"{repo_path(root, doc)}: root-absolute reference `{raw}` resolves against the "
                    "filesystem root, not the repo - use a repo-relative path"
                )
            elif not target.exists():
                bucket.append(f"{repo_path(root, doc)}: reference does not exist: {raw}")
    return errors, warnings


def repository_report(root):
    dead_errors, dead_warnings = dead_links(root)
    errors = sibling_errors(root) + orphan_errors(root) + test_project_errors(root) + dead_errors
    return {"errors": errors, "warnings": dead_warnings}


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
        print(f"Docs reachability: {len(report['errors'])} error(s), {len(report['warnings'])} warning(s)")
    raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
