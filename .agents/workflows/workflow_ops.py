import argparse
import base64
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import delivery_runtime
import workflow_runtime
from pr_body import validate_pr_body


SCHEMA_VERSION = 1
GOAL_EVALUATOR_VARIABLE = "ANTHROPIC_DEFAULT_HAIKU_MODEL"
DEFAULT_SUMMARY_LINES = 8
DEFAULT_FAILURE_ITEMS = 20
DEFAULT_SUMMARY_BYTES = 4096
DEFAULT_POLL_SECONDS = 60
DEFAULT_MONITOR_SECONDS = 21600
DEFAULT_OFFLINE_GAP_SECONDS = 300
REVIEW_BUNDLE_RETENTION_SECONDS = 7 * 24 * 60 * 60
FAILURE_PATTERN = re.compile(
    r"(?:\bfailed\b|\bfailure\b|\berror\b|\bfatal\b|\bexception\b|\bpanic\b|\btimeout\b)",
    re.IGNORECASE,
)
SECRET_PATTERN = re.compile(r"(?:token|secret|password|key|authorization)", re.IGNORECASE)


class WorkflowOperationError(RuntimeError):
    pass


class MonitorLease:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                owner = json.loads(self.path.read_text(encoding="utf-8"))
                owner_pid = int(owner["pid"])
                if owner_pid != os.getpid():
                    os.kill(owner_pid, 0)
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                self.path.unlink(missing_ok=True)
                handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            else:
                raise WorkflowOperationError("another process already owns this exact monitor identity")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "started_at": utc_now()}, stream)
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.path.unlink(missing_ok=True)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def emit(value):
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def redact(text):
    text = re.sub(
        r"(?im)\bauthorization\s*[:=]\s*[^\r\n]+",
        "Authorization: [REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)(?<![A-Za-z0-9_-])([A-Za-z0-9_-]*(?:token|secret|password|api[_-]?key)[A-Za-z0-9_-]*)(\s*[:=]\s*)([^\s,;]+)",
        r"\1\2[REDACTED]",
        text,
    )
    return re.sub(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", text)


def run_process(arguments, cwd, text=True, check=True):
    executable = shutil.which(arguments[0]) or arguments[0]
    completed = subprocess.run(
        [executable, *arguments[1:]],
        cwd=str(cwd),
        capture_output=True,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    )
    if check and completed.returncode:
        stderr = completed.stderr if text else completed.stderr.decode("utf-8", errors="replace")
        raise WorkflowOperationError(redact(stderr.strip()) or f"{arguments[0]} exited {completed.returncode}")
    return completed


def git(root, *arguments):
    return run_process(["git", *arguments], root).stdout.strip()


def repository_root(start):
    return Path(git(start, "rev-parse", "--show-toplevel")).resolve()


def repository_slug(root):
    remote = git(root, "remote", "get-url", "origin")
    match = re.search(r"(?:[:/])([^/:]+)/([^/]+?)(?:\.git)?$", remote)
    if not match:
        raise WorkflowOperationError("origin is not a supported forge repository URL")
    return f"{match.group(1)}/{match.group(2)}"


def common_git_directory(root):
    common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    if not common.is_absolute():
        common = root / common
    return common.resolve()


def worktree_roots(root):
    listing = run_process(
        ["git", "worktree", "list", "--porcelain", "-z"], root, text=False
    ).stdout
    roots = []
    for record in listing.split(b"\0"):
        if record.startswith(b"worktree "):
            roots.append(Path(record[9:].decode("utf-8", errors="surrogateescape")).resolve())
    return roots


def state_root(root):
    target = common_git_directory(root) / "agent-workflow"
    target.mkdir(parents=True, exist_ok=True)
    return target


def run_root(root, workflow_run_id):
    if not isinstance(workflow_run_id, str) or not workflow_run_id.strip():
        raise WorkflowOperationError("workflow run id is required")
    runs = state_root(root) / "runs"
    candidate = runs / workflow_run_id
    try:
        parts = candidate.relative_to(runs).parts
    except ValueError as error:
        raise WorkflowOperationError("workflow run id escapes the workflow state root") from error
    current = runs
    if is_redirect(runs.parent) or is_redirect(current):
        raise WorkflowOperationError("workflow run id contains a redirected owned directory")
    for part in parts:
        current = current / part
        if is_redirect(current):
            raise WorkflowOperationError("workflow run id contains a redirected owned directory")
    runs = runs.resolve()
    candidate = candidate.resolve()
    try:
        candidate.relative_to(runs)
    except ValueError as error:
        raise WorkflowOperationError("workflow run id escapes the workflow state root") from error
    if candidate == runs:
        raise WorkflowOperationError("workflow run id must identify a run below the workflow state root")
    return candidate


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def append_event(root, workflow_run_id, event):
    path = run_root(root, workflow_run_id) / "telemetry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"schema_version": SCHEMA_VERSION, "at": utc_now(), **event}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return path


def bounded_lines(text, maximum_lines, maximum_bytes):
    selected = [line.strip() for line in text.splitlines() if line.strip()][-maximum_lines:]
    result = []
    used = 0
    for line in selected:
        encoded = line.encode("utf-8")
        remaining = maximum_bytes - used
        if remaining <= 0:
            break
        if len(encoded) > remaining:
            line = encoded[:remaining].decode("utf-8", errors="ignore")
            encoded = line.encode("utf-8")
        result.append(line)
        used += len(encoded)
    return result


def failing_items(text, maximum_items, maximum_bytes):
    matches = []
    used = 0
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate or not FAILURE_PATTERN.search(candidate):
            continue
        encoded = candidate.encode("utf-8")
        remaining = maximum_bytes - used
        if remaining <= 0:
            break
        if len(encoded) > remaining:
            candidate = encoded[:remaining].decode("utf-8", errors="ignore")
            encoded = candidate.encode("utf-8")
        if candidate not in matches:
            matches.append(candidate)
            used += len(encoded)
        if len(matches) >= maximum_items:
            break
    return matches


def command_identity(label, command):
    safe_program = Path(command[0]).name
    return {
        "label": label,
        "program": safe_program,
        "argument_count": max(0, len(command) - 1),
        "digest": digest(command),
    }


def compact_run(root, workflow_run_id, label, command, summary_lines, failure_items_limit, summary_bytes):
    if not command:
        raise WorkflowOperationError("a command is required after --")
    limits = load_budget(root)["mechanism_limits"]
    summary_bytes = min(max(0, summary_bytes), limits["failure_summary_bytes"])
    failure_items_limit = min(max(0, failure_items_limit), limits["failure_items"])
    summary_lines = min(max(0, summary_lines), limits["failure_items"])
    identity = command_identity(label, command)
    artifact_dir = run_root(root, workflow_run_id) / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = artifact_dir / f"{identity['digest'][:16]}-{re.sub(r'[^a-zA-Z0-9_.-]+', '-', label)}.log"
    started = time.monotonic()
    completed = run_process(command, root, check=False)
    duration = time.monotonic() - started
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined = redact(stdout + ("\n" if stdout and stderr else "") + stderr)
    artifact.write_text(combined, encoding="utf-8")
    failures = [] if completed.returncode == 0 else failing_items(combined, failure_items_limit, summary_bytes)
    summary = [] if completed.returncode == 0 else bounded_lines(combined, summary_lines, summary_bytes)
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation": "run",
        "command": identity,
        "duration_seconds": round(duration, 3),
        "exit_state": "succeeded" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "failing_items": failures,
        "summary": summary,
        "captured_lines": len(combined.splitlines()),
        "artifact": str(artifact),
    }
    append_event(
        root,
        workflow_run_id,
        {
            "kind": "operation",
            "operation": "run",
            "command_digest": identity["digest"],
            "duration_seconds": duration,
            "exit_state": result["exit_state"],
        },
    )
    return result


def inspect_repository(root, workflow_run_id):
    branch = git(root, "branch", "--show-current")
    head = git(root, "rev-parse", "HEAD")
    status = run_process(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "-z"], root
    ).stdout
    dirty_paths = []
    entries = iter(status.split("\0"))
    for entry in entries:
        if entry:
            dirty_paths.append(entry[3:])
            if "R" in entry[:2] or "C" in entry[:2]:
                dirty_paths.append(next(entries))
    upstream = run_process(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        root,
        check=False,
    ).stdout.strip()
    ahead = behind = None
    if upstream:
        counts = git(root, "rev-list", "--left-right", "--count", f"{upstream}...HEAD").split()
        if len(counts) == 2:
            behind, ahead = (int(counts[0]), int(counts[1]))
    plans = sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.glob("plans/**/*_PROGRESS.md"))
    reviews = sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.glob("reviews/*.md"))
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation": "inspect",
        "repository": repository_slug(root),
        "root": str(root),
        "branch": branch,
        "head": head,
        "upstream": upstream or None,
        "ahead": ahead,
        "behind": behind,
        "dirty_paths": dirty_paths,
        "progress_ledgers": plans,
        "review_work_orders": reviews,
    }
    append_event(root, workflow_run_id, {"kind": "operation", "operation": "inspect"})
    return result


def sha256_file(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            value.update(block)
    return value.hexdigest()


def tree_content_digest(path):
    records = []
    for item in sorted(path.rglob("*"), key=lambda candidate: candidate.relative_to(path).as_posix()):
        relative = item.relative_to(path).as_posix()
        if item.is_symlink():
            records.append({"path": relative, "kind": "symlink", "target": os.readlink(item)})
        elif item.is_file():
            records.append({"path": relative, "kind": "file", "sha256": sha256_file(item)})
    return digest(records)


def routed_skills(root, paths):
    return route_findings(root, paths)[0]


def route_findings(root, paths):
    """Every skill the route table owes for these paths, and its deny-pattern hits."""
    route_table = root / ".agents" / "skill-routes.json"
    if not route_table.is_file() or not paths:
        return [], []
    candidates = (
        Path(__file__).resolve().parents[1] / "hooks" / "skill_router.py",
        root / ".agents" / "hooks" / "skill_router.py",
    )
    router = next((candidate for candidate in candidates if candidate.is_file()), None)
    if router is None:
        raise WorkflowOperationError(
            ".agents/skill-routes.json exists but the engineering package has no skill_router.py"
        )
    completed = subprocess.run(
        [sys.executable, "-B", str(router), "--skills-for", "--json"],
        cwd=str(root),
        input="\n".join(paths) + "\n",
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        detail = completed.stdout.strip() or completed.stderr.strip() or "skill routing failed"
        raise WorkflowOperationError(redact(detail))
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise WorkflowOperationError("skill router did not return its JSON contract") from error
    if isinstance(value, list):
        return sorted({str(item) for item in value}), []
    if isinstance(value, dict) and isinstance(value.get("skills"), dict):
        violations = [list(item) for item in value.get("violations") or [] if isinstance(item, (list, tuple))]
        return sorted(str(item) for item in value["skills"]), violations
    raise WorkflowOperationError("skill router returned an invalid JSON contract")


def trunk_range(root, head):
    for trunk in ("origin/main", "main"):
        try:
            base = git(root, "merge-base", trunk, head)
        except WorkflowOperationError:
            continue
        return base, git(root, "diff", "--name-only", f"{base}..{head}").splitlines()
    return None, []


def security_classification(root, tree_path, head, paths):
    hooks = Path(__file__).resolve().parents[1] / "hooks"
    if str(hooks) not in sys.path:
        sys.path.insert(0, str(hooks))
    import merge_review_gate

    config = tree_path / merge_review_gate.CONFIG_FILE
    try:
        patterns = merge_review_gate.security_patterns(config) if config.is_file() else merge_review_gate._SECURITY_PATTERNS
    except merge_review_gate.ConfigUnusable as error:
        raise WorkflowOperationError(str(error)) from error
    trunk_base, trunk_paths = trunk_range(root, head)
    return {
        "first_path": merge_review_gate.touches_security(paths, patterns),
        "trunk_base": trunk_base,
        "trunk_first_path": merge_review_gate.touches_security(trunk_paths, patterns),
    }


def select_review_lenses(paths):
    lowered = [path.lower() for path in paths]
    lenses = ["native-general"]
    selectors = (
        ("security", ("auth", "security", "credential", ".github/workflows")),
        ("data-migration", ("migration", ".sql", "dbcontext", "entitytypeconfiguration")),
        ("api-contract", ("controller", "endpoint", "openapi", "proto", "contract")),
        ("frontend", (".tsx", ".jsx", ".css", "frontend", "client/")),
        ("workflow", (".agents/", ".claude/", ".codex/", "plugin", "workflow")),
    )
    for lens, needles in selectors:
        if any(any(needle in path for needle in needles) for path in lowered):
            lenses.append(lens)
    return lenses


def synchronize_for_review(root, base_ref):
    git(root, "fetch", "origin", "--prune")
    before = git(root, "rev-parse", "HEAD")
    base = git(root, "rev-parse", base_ref)
    behind = int(git(root, "rev-list", "--count", f"HEAD..{base_ref}"))
    if behind:
        if git(root, "status", "--porcelain"):
            raise WorkflowOperationError("pre-review synchronization requires a clean worktree")
        git(root, "merge", base_ref, "--no-edit")
    return {"base_ref": base_ref, "base": base, "head_before": before, "head_after": git(root, "rev-parse", "HEAD"), "behind": behind}


def materialize_tree(root, head, archive_path, tree_path):
    archive = run_process(["git", "archive", "--format=tar", head], root, text=False).stdout
    # Replace, never truncate in place: a filesystem filter on the shared .git can reject a truncating
    # open of an existing archive with EINVAL while a fresh create succeeds.
    archive_path.unlink(missing_ok=True)
    archive_path.write_bytes(archive)
    if tree_path.exists():
        shutil.rmtree(tree_path)
    tree_path.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
        for member in stream.getmembers():
            destination = (tree_path / member.name).resolve()
            try:
                destination.relative_to(tree_path.resolve())
            except ValueError as error:
                raise WorkflowOperationError("frozen tree archive escapes its bundle") from error
        stream.extractall(tree_path, filter="data")
    return archive


def is_redirect(path):
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    return path.is_symlink() or stat.S_ISLNK(metadata.st_mode) or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def review_candidate_key(value):
    return digest(
        {
            "base": value.get("base"),
            "head": value.get("head"),
            "path_digest": value.get("path_digest"),
            "patch_sha256": value.get("patch_sha256"),
        }
    )


def review_bundle_locations(root, workflow_run_id, candidate_key):
    root = repository_root(root)
    common = common_git_directory(root)
    temporary = Path(tempfile.gettempdir()).resolve()
    for protected in (*worktree_roots(root), common):
        try:
            temporary.relative_to(protected)
        except ValueError:
            continue
        raise WorkflowOperationError("review bundle cache cannot be inside the checkout or common Git directory")
    run = run_root(root, workflow_run_id).resolve()
    cache = temporary / "review"
    repository_cache = cache / compact_cache_key(os.path.normcase(str(common)))
    run_cache = repository_cache / compact_cache_key(os.path.normcase(str(run)))
    directory = run_cache / compact_candidate_key(candidate_key)
    for candidate in (cache, repository_cache, run_cache, directory):
        if candidate.exists() and (is_redirect(candidate) or not candidate.is_dir()):
            raise WorkflowOperationError("review bundle cache contains a redirected or invalid owned directory")
    private = run / "review" / candidate_key
    for candidate in (run, run / "review", private):
        if candidate.exists() and (is_redirect(candidate) or not candidate.is_dir()):
            raise WorkflowOperationError("review descriptor namespace contains a redirected or invalid owned directory")
    return {
        "private": private,
        "descriptor": private / "descriptor.json",
        "directory": directory,
        "patch": directory / "candidate.patch",
        "paths": directory / "paths.nul",
        "tree": directory / "tree",
        "tree_archive": directory / "tree.tar",
        "identity": directory / "identity.json",
    }


def compact_cache_key(value):
    return base64.urlsafe_b64encode(hashlib.sha256(value.encode("utf-8")).digest()).decode("ascii").rstrip("=")[:22]


def compact_candidate_key(value):
    return base64.urlsafe_b64encode(bytes.fromhex(value)).decode("ascii").rstrip("=")[:22]


def legacy_review_bundle_locations(locations):
    directory = locations["private"]
    return {
        "directory": directory,
        "patch": directory / "candidate.patch",
        "paths": directory / "paths.nul",
        "tree": directory / "tree",
        "tree_archive": directory / "tree.tar",
        "identity": directory / "identity.json",
    }


def bundle_matches_locations(bundle, locations):
    return all(bundle.get(name) == str(locations[name]) for name in (
        "directory", "patch", "paths", "tree", "tree_archive", "identity"
    ))


def remove_legacy_review_payload(locations):
    legacy = legacy_review_bundle_locations(locations)
    for name in ("patch", "paths", "tree", "tree_archive", "identity"):
        path = legacy[name]
        if not path.exists() and not is_redirect(path):
            continue
        if is_redirect(path):
            raise WorkflowOperationError("legacy review bundle contains a redirected artifact path")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def validate_legacy_review_bundle(root, value, locations):
    artifacts = [locations[name] for name in ("patch", "paths", "tree", "tree_archive", "identity")]
    present = [path.exists() or is_redirect(path) for path in artifacts]
    if not any(present):
        return
    if not all(present):
        raise WorkflowOperationError("legacy review bundle is incomplete")
    if any(is_redirect(path) for path in artifacts):
        raise WorkflowOperationError("legacy review bundle contains a redirected artifact path")
    if sha256_file(locations["patch"]) != value["patch_sha256"]:
        raise WorkflowOperationError("legacy review patch hash differs from its descriptor")
    path_bytes = locations["paths"].read_bytes()
    if hashlib.sha256(path_bytes).hexdigest() != value["path_digest"]:
        raise WorkflowOperationError("legacy review path manifest differs from its descriptor")
    if sha256_file(locations["tree_archive"]) != value["tree_archive_sha256"]:
        raise WorkflowOperationError("legacy review tree archive hash differs from its descriptor")
    if sha256_file(locations["identity"]) != value["bundle"]["identity_sha256"]:
        raise WorkflowOperationError("legacy review identity manifest hash differs from its descriptor")
    if json.loads(locations["identity"].read_text(encoding="utf-8")) != expected_identity(value, path_bytes):
        raise WorkflowOperationError("legacy review identity manifest differs from the frozen candidate")
    if tree_content_digest(locations["tree"]) != value["tree_content_sha256"]:
        raise WorkflowOperationError("legacy materialized review tree differs from its descriptor")
    if git(root, "rev-parse", f"{value['head']}^{{tree}}") != value["head_tree"]:
        raise WorkflowOperationError("review head tree differs from the repository object")
    patch = run_process(["git", "diff", "--binary", "--full-index", value["base"], value["head"]], root, text=False).stdout
    if hashlib.sha256(patch).hexdigest() != value["patch_sha256"]:
        raise WorkflowOperationError("review patch differs from the repository objects")


def create_review_bundle_directory(locations):
    directory = locations["directory"]
    if directory.exists() or is_redirect(directory):
        raise WorkflowOperationError("review bundle already exists without its authoritative descriptor")
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    if is_redirect(directory) or not directory.is_dir():
        raise WorkflowOperationError("review bundle cache contains a redirected owned directory")


def expected_identity(value, path_bytes):
    return {
        "schema_version": SCHEMA_VERSION,
        "descriptor_id": value["descriptor_id"],
        "repository": value["repository"],
        "base": value["base"],
        "head": value["head"],
        "head_tree": value["head_tree"],
        "patch_sha256": value["patch_sha256"],
        "paths_sha256": hashlib.sha256(path_bytes).hexdigest(),
        "path_digest": value["path_digest"],
        "tree_archive_sha256": value["tree_archive_sha256"],
        "tree_content_sha256": value["tree_content_sha256"],
        "rules": value["rules"],
    }


def restore_review_bundle(root, value, locations):
    create_review_bundle_directory(locations)
    paths_bytes = b"\0".join(item.encode("utf-8", errors="surrogateescape") for item in value["paths"])
    patch = run_process(
        ["git", "diff", "--binary", "--full-index", value["base"], value["head"]], root, text=False
    ).stdout
    if hashlib.sha256(patch).hexdigest() != value["patch_sha256"]:
        raise WorkflowOperationError("review patch differs from the repository objects")
    if hashlib.sha256(paths_bytes).hexdigest() != value["path_digest"]:
        raise WorkflowOperationError("review path manifest differs from its descriptor")
    locations["patch"].write_bytes(patch)
    locations["paths"].write_bytes(paths_bytes)
    archive = materialize_tree(root, value["head"], locations["tree_archive"], locations["tree"])
    if hashlib.sha256(archive).hexdigest() != value["tree_archive_sha256"]:
        raise WorkflowOperationError("review tree archive differs from the repository object")
    if tree_content_digest(locations["tree"]) != value["tree_content_sha256"]:
        raise WorkflowOperationError("repository tree differs from the materialized review identity")
    atomic_json(locations["identity"], expected_identity(value, paths_bytes))
    if sha256_file(locations["identity"]) != value["bundle"]["identity_sha256"]:
        raise WorkflowOperationError("review identity manifest differs from its descriptor")


def validate_review_bundle(root, value, locations):
    directory = locations["directory"]
    required = {name: locations[name] for name in ("patch", "paths", "tree", "tree_archive", "identity")}
    if is_redirect(directory) or any(is_redirect(path) for path in required.values()):
        raise WorkflowOperationError("review bundle contains a redirected artifact path")
    if not all(path.exists() for path in required.values()):
        raise WorkflowOperationError("review bundle is incomplete")
    if sha256_file(required["patch"]) != value["patch_sha256"]:
        raise WorkflowOperationError("review patch hash differs from its descriptor")
    path_bytes = required["paths"].read_bytes()
    paths = [item.decode("utf-8", errors="surrogateescape") for item in path_bytes.split(b"\0") if item]
    if paths != value["paths"] or hashlib.sha256(path_bytes).hexdigest() != value["path_digest"]:
        raise WorkflowOperationError("review path manifest differs from its descriptor")
    current_paths_bytes = run_process(
        ["git", "diff", "--name-only", "-z", value["base"], value["head"]], root, text=False
    ).stdout
    if [item.decode("utf-8", errors="surrogateescape") for item in current_paths_bytes.split(b"\0") if item] != paths:
        raise WorkflowOperationError("review path manifest differs from the repository objects")
    if sha256_file(required["identity"]) != value["bundle"]["identity_sha256"]:
        raise WorkflowOperationError("review identity manifest hash differs from its descriptor")
    if sha256_file(required["tree_archive"]) != value["tree_archive_sha256"]:
        raise WorkflowOperationError("review tree archive hash differs from its descriptor")
    if json.loads(required["identity"].read_text(encoding="utf-8")) != expected_identity(value, path_bytes):
        raise WorkflowOperationError("review identity manifest differs from the frozen candidate")
    if git(root, "rev-parse", f"{value['head']}^{{tree}}") != value["head_tree"]:
        raise WorkflowOperationError("review head tree differs from the repository object")
    if tree_content_digest(required["tree"]) != value["tree_content_sha256"]:
        raise WorkflowOperationError("materialized review tree differs from its descriptor")
    patch = run_process(["git", "diff", "--binary", "--full-index", value["base"], value["head"]], root, text=False).stdout
    if hashlib.sha256(patch).hexdigest() != value["patch_sha256"]:
        raise WorkflowOperationError("review patch differs from the repository objects")
    routed, violations = route_findings(required["tree"], paths)
    if (value.get("routed_skills"), value.get("route_violations")) != (routed, violations):
        raise WorkflowOperationError("review routing differs from the frozen tree routing evidence")
    rules = []
    for name in routed:
        rule_path = required["tree"] / ".agents" / "skills" / name / "SKILL.md"
        if rule_path.is_file():
            rules.append({
                "name": name,
                "path": str(rule_path.relative_to(required["tree"])).replace("\\", "/"),
                "sha256": sha256_file(rule_path),
            })
    if rules != value["rules"]:
        raise WorkflowOperationError("review rules differ from the frozen tree routing evidence")


def review_descriptor_paths(runs):
    if is_redirect(runs.parent) or is_redirect(runs) or not runs.is_dir():
        return
    for current_path, directory_names, file_names in os.walk(runs, topdown=True, followlinks=False):
        current = Path(current_path)
        legacy_candidate = current.parent.name == "review" and re.fullmatch(r"[0-9a-f]{64}", current.name)
        directory_names[:] = [
            name for name in directory_names
            if not is_redirect(current / name) and not (legacy_candidate and name == "tree")
        ]
        descriptor = current / "descriptor.json"
        if current.parent.name == "review" and "descriptor.json" in file_names and not is_redirect(descriptor):
            yield descriptor


def cleanup_review_bundles(root, now=None):
    root = repository_root(root)
    runs = state_root(root) / "runs"
    current = now or datetime.now(timezone.utc)
    for descriptor_path in review_descriptor_paths(runs):
        try:
            run_id = descriptor_path.parent.parent.parent.relative_to(runs).as_posix()
            value = json.loads(descriptor_path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or not isinstance(value.get("bundle"), dict):
                continue
            bundle = value["bundle"]
            validated_at = bundle.get("last_validated_at", value["created_at"])
            timestamp = datetime.fromisoformat(validated_at)
            if timestamp.tzinfo is None:
                continue
            if current - timestamp.astimezone(timezone.utc) < timedelta(seconds=REVIEW_BUNDLE_RETENTION_SECONDS):
                continue
            candidate_key = review_candidate_key(value)
            locations = review_bundle_locations(root, run_id, candidate_key)
            expected = ("directory", "patch", "paths", "tree", "tree_archive", "identity")
            owned = (
                value.get("repository") == repository_slug(root)
                and value.get("descriptor_id") == descriptor_identity(value)
                and descriptor_path.resolve() == locations["descriptor"].resolve()
                and not is_redirect(descriptor_path)
                and all(bundle.get(name) == str(locations[name]) for name in expected)
            )
            if not owned:
                continue
            directory = locations["directory"]
            artifacts = [locations[name] for name in expected if name != "directory"]
            if directory.exists() and not is_redirect(directory) and not any(is_redirect(path) for path in artifacts):
                shutil.rmtree(directory)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, WorkflowOperationError):
            continue


def descriptor_identity(value):
    excluded = {"artifact", "bundle", "descriptor_id"}
    return digest({key: item for key, item in value.items() if key not in excluded})


def review_prepare(root, workflow_run_id, base_ref, head_ref, synchronize):
    cleanup_review_bundles(root)
    sync = synchronize_for_review(root, base_ref) if synchronize else None
    base = git(root, "merge-base", base_ref, head_ref)
    head = git(root, "rev-parse", head_ref)
    changed = run_process(["git", "diff", "--name-only", "-z", base, head], root, text=False).stdout
    paths = [item.decode("utf-8", errors="surrogateescape") for item in changed.split(b"\0") if item]
    paths_bytes = b"\0".join(item.encode("utf-8", errors="surrogateescape") for item in paths)
    path_digest = hashlib.sha256(paths_bytes).hexdigest()
    patch = run_process(["git", "diff", "--binary", "--full-index", base, head], root, text=False).stdout
    candidate_key = digest({"base": base, "head": head, "path_digest": path_digest, "patch_sha256": hashlib.sha256(patch).hexdigest()})
    locations = review_bundle_locations(root, workflow_run_id, candidate_key)
    if locations["descriptor"].exists():
        stored = json.loads(locations["descriptor"].read_text(encoding="utf-8"))
        if stored.get("branch") != git(root, "branch", "--show-current"):
            raise WorkflowOperationError("review run belongs to another branch; use a distinct workflow run id")
        descriptor = load_descriptor(root, workflow_run_id, locations["descriptor"])
        descriptor["artifact"] = str(locations["descriptor"])
        return descriptor
    create_review_bundle_directory(locations)
    try:
        locations["patch"].write_bytes(patch)
        locations["paths"].write_bytes(paths_bytes)
        tree_archive = materialize_tree(root, head, locations["tree_archive"], locations["tree"])
        tree_sha256 = tree_content_digest(locations["tree"])
        skills, route_violations = route_findings(locations["tree"], paths)
        rules = []
        for name in skills:
            path = locations["tree"] / ".agents" / "skills" / name / "SKILL.md"
            if path.is_file():
                rules.append({"name": name, "path": str(path.relative_to(locations["tree"])).replace("\\", "/"), "sha256": sha256_file(path)})
        descriptor = {
            "schema_version": SCHEMA_VERSION,
            "operation": "review-prepare",
            "repository": repository_slug(root),
            "branch": git(root, "branch", "--show-current"),
            "base_ref": base_ref,
            "base": base,
            "head": head,
            "head_tree": git(root, "rev-parse", f"{head}^{{tree}}"),
            "tree_archive_sha256": hashlib.sha256(tree_archive).hexdigest(),
            "tree_content_sha256": tree_sha256,
            "paths": paths,
            "path_digest": path_digest,
            "patch_sha256": hashlib.sha256(patch).hexdigest(),
            "rules": rules,
            "routed_skills": skills,
            "route_violations": route_violations,
            "lenses": select_review_lenses(paths),
            "security": security_classification(root, locations["tree"], head, paths),
            "waves": 1,
            "context": {
                "immutable_artifacts": [f"git-base:{base}", f"git-head:{head}"],
                "repository_paths": paths,
                "rule_identities": rules,
            },
            "synchronization": sync,
            "created_at": utc_now(),
        }
        descriptor["context"]["immutable_artifacts"].extend(
            [f"sha256:{descriptor['patch_sha256']}", f"path-digest:{descriptor['path_digest']}"]
        )
        descriptor["descriptor_id"] = descriptor_identity(descriptor)
        identity = {
            "schema_version": SCHEMA_VERSION,
            "descriptor_id": descriptor["descriptor_id"],
            "repository": descriptor["repository"],
            "base": base,
            "head": head,
            "head_tree": descriptor["head_tree"],
            "patch_sha256": descriptor["patch_sha256"],
            "paths_sha256": hashlib.sha256(paths_bytes).hexdigest(),
            "path_digest": descriptor["path_digest"],
            "tree_archive_sha256": descriptor["tree_archive_sha256"],
            "tree_content_sha256": tree_sha256,
            "rules": rules,
        }
        descriptor["bundle"] = {
            "directory": str(locations["directory"]),
            "patch": str(locations["patch"]),
            "paths": str(locations["paths"]),
            "tree": str(locations["tree"]),
            "tree_archive": str(locations["tree_archive"]),
            "identity": str(locations["identity"]),
        }
        atomic_json(locations["identity"], identity)
        descriptor["bundle"]["identity_sha256"] = sha256_file(locations["identity"])
        atomic_json(locations["descriptor"], descriptor)
    except Exception:
        if not locations["descriptor"].exists() and not is_redirect(locations["directory"]):
            try:
                shutil.rmtree(locations["directory"])
            except OSError:
                pass
        raise
    load_descriptor(root, workflow_run_id, locations["descriptor"])
    descriptor["artifact"] = str(locations["descriptor"])
    append_event(root, workflow_run_id, {"kind": "review", "operation": "prepare", "waves": 1, "descriptor_id": descriptor["descriptor_id"]})
    return descriptor


def load_descriptor(root, workflow_run_id, path):
    descriptor_path = Path(path).absolute()
    value = json.loads(descriptor_path.read_text(encoding="utf-8"))
    required_fields = ("operation", "repository", "base", "head", "head_tree", "tree_archive_sha256", "tree_content_sha256", "paths", "path_digest", "patch_sha256", "rules", "descriptor_id", "bundle")
    if not isinstance(value, dict) or any(field not in value for field in required_fields):
        raise WorkflowOperationError("review descriptor is incomplete")
    if value.get("operation") != "review-prepare":
        raise WorkflowOperationError("review descriptor has the wrong operation")
    if any(key in value.get("context", {}) for key in ("transcript", "conversation", "messages")):
        raise WorkflowOperationError("review context cannot include implementation transcript content")
    if value.get("descriptor_id") != descriptor_identity(value):
        raise WorkflowOperationError("review descriptor identity does not match its contents")
    if value["repository"] != repository_slug(root):
        raise WorkflowOperationError("review descriptor belongs to a different repository")
    bundle = value["bundle"]
    bundle_fields = ("directory", "patch", "paths", "tree", "tree_archive", "identity", "identity_sha256")
    if not isinstance(bundle, dict) or any(not isinstance(bundle.get(field), str) or not bundle[field] for field in bundle_fields):
        raise WorkflowOperationError("review bundle identity is incomplete")
    candidate_key = review_candidate_key(value)
    locations = review_bundle_locations(root, workflow_run_id, candidate_key)
    if os.path.normcase(str(descriptor_path)) != os.path.normcase(str(locations["descriptor"])):
        raise WorkflowOperationError("review descriptor is outside the current workflow run")
    if is_redirect(descriptor_path):
        raise WorkflowOperationError("review descriptor is redirected")
    legacy = legacy_review_bundle_locations(locations)
    external_bundle = bundle_matches_locations(bundle, locations)
    legacy_bundle = bundle_matches_locations(bundle, legacy)
    if not external_bundle and not legacy_bundle:
        raise WorkflowOperationError("review descriptor is not bound to its expected external bundle")
    if legacy_bundle:
        validate_legacy_review_bundle(root, value, legacy)
        if locations["directory"].exists():
            validate_review_bundle(root, value, locations)
        else:
            restore_review_bundle(root, value, locations)
            validate_review_bundle(root, value, locations)
        value["bundle"].update({name: str(locations[name]) for name in (
            "directory", "patch", "paths", "tree", "tree_archive", "identity"
        )})
        atomic_json(descriptor_path, value)
        remove_legacy_review_payload(locations)
    directory = locations["directory"]
    required = {name: locations[name] for name in ("patch", "paths", "tree", "tree_archive", "identity")}
    expected_names = {"patch": "candidate.patch", "paths": "paths.nul", "tree": "tree", "tree_archive": "tree.tar", "identity": "identity.json"}
    if any(required[name].name != expected for name, expected in expected_names.items()):
        raise WorkflowOperationError("review bundle artifact names differ from the contract")
    if not directory.exists():
        restore_review_bundle(root, value, locations)
    if is_redirect(directory) or any(is_redirect(path) for path in required.values()):
        raise WorkflowOperationError("review bundle contains a redirected artifact path")
    if not all(path.exists() for path in required.values()):
        raise WorkflowOperationError("review bundle is incomplete")
    if sha256_file(required["patch"]) != value.get("patch_sha256"):
        raise WorkflowOperationError("review patch hash differs from its descriptor")
    path_bytes = required["paths"].read_bytes()
    paths = [item.decode("utf-8", errors="surrogateescape") for item in path_bytes.split(b"\0") if item]
    if paths != value.get("paths") or hashlib.sha256(path_bytes).hexdigest() != value.get("path_digest"):
        raise WorkflowOperationError("review path manifest differs from its descriptor")
    current_paths_bytes = run_process(
        ["git", "diff", "--name-only", "-z", value["base"], value["head"]], root, text=False
    ).stdout
    current_paths = [item.decode("utf-8", errors="surrogateescape") for item in current_paths_bytes.split(b"\0") if item]
    if current_paths != paths:
        raise WorkflowOperationError("review path manifest differs from the repository objects")
    if sha256_file(required["identity"]) != bundle.get("identity_sha256"):
        raise WorkflowOperationError("review identity manifest hash differs from its descriptor")
    if sha256_file(required["tree_archive"]) != value["tree_archive_sha256"]:
        raise WorkflowOperationError("review tree archive hash differs from its descriptor")
    identity = json.loads(required["identity"].read_text(encoding="utf-8"))
    frozen_identity = expected_identity(value, path_bytes)
    if identity != frozen_identity:
        raise WorkflowOperationError("review identity manifest differs from the frozen candidate")
    if git(root, "rev-parse", f"{value['head']}^{{tree}}") != value["head_tree"]:
        raise WorkflowOperationError("review head tree differs from the repository object")
    if tree_content_digest(required["tree"]) != value["tree_content_sha256"]:
        raise WorkflowOperationError("materialized review tree differs from its descriptor")
    current_patch = run_process(["git", "diff", "--binary", "--full-index", value["base"], value["head"]], root, text=False).stdout
    if hashlib.sha256(current_patch).hexdigest() != value["patch_sha256"]:
        raise WorkflowOperationError("review patch differs from the repository objects")
    expected_rules = []
    routed, violations = route_findings(required["tree"], paths)
    if "routed_skills" in value and (value["routed_skills"], value.get("route_violations")) != (routed, violations):
        raise WorkflowOperationError("review routing differs from the frozen tree routing evidence")
    for name in routed:
        rule_path = required["tree"] / ".agents" / "skills" / name / "SKILL.md"
        if rule_path.is_file():
            expected_rules.append(
                {
                    "name": name,
                    "path": str(rule_path.relative_to(required["tree"])).replace("\\", "/"),
                    "sha256": sha256_file(rule_path),
                }
            )
    if expected_rules != value.get("rules"):
        raise WorkflowOperationError("review rules differ from the frozen tree routing evidence")
    value["bundle"]["last_validated_at"] = utc_now()
    atomic_json(descriptor_path, value)
    remove_legacy_review_payload(locations)
    return value


def review_reconcile(root, workflow_run_id, descriptor_path, base_ref):
    descriptor = load_descriptor(root, workflow_run_id, descriptor_path)
    current_head = git(root, "rev-parse", "HEAD")
    current_base = git(root, "rev-parse", base_ref)
    reasons = []
    if current_head != descriptor["head"]:
        reasons.append("candidate-head-changed")
    if current_base != descriptor["base"]:
        changed = git(root, "diff", "--name-only", descriptor["base"], current_base).splitlines()
        sensitive = set(descriptor["paths"]) | {rule["path"] for rule in descriptor["rules"]}
        if sensitive.intersection(changed):
            reasons.append("base-changed-relevant-evidence")
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation": "review-reconcile",
        "descriptor_id": descriptor["descriptor_id"],
        "candidate_head": descriptor["head"],
        "current_head": current_head,
        "review_required": bool(reasons),
        "reasons": reasons,
        "base_moved": current_base != descriptor["base"],
        "exact_head": current_head == descriptor["head"],
    }
    append_event(root, workflow_run_id, {"kind": "review", "operation": "reconcile", "review_required": result["review_required"]})
    return result


def parse_status_checks(checks):
    failures = []
    pending = []
    for check in checks or []:
        name = check.get("name") or check.get("context") or "unknown"
        status = str(check.get("status") or "").lower()
        legacy_state = str(check.get("state") or "").lower()
        conclusion = str(check.get("conclusion") or "").lower()
        if legacy_state in {"error", "failure", "failed"}:
            failures.append(name)
        elif legacy_state in {"success", "neutral", "skipped"}:
            continue
        elif conclusion and conclusion not in {"success", "neutral", "skipped"}:
            failures.append(name)
        elif status not in {"completed", "success"} or not conclusion:
            pending.append(name)
    return failures, pending


def forge_observation(root, identity):
    if identity["target_kind"] == "run":
        fields = "databaseId,headSha,status,conclusion,workflowName,attempt,url,event"
        completed = run_process(["gh", "run", "view", str(identity["target_id"]), "--json", fields], root)
        value = json.loads(completed.stdout)
        if str(value.get("headSha")) != identity["head"]:
            raise WorkflowOperationError("run head differs from the bound head")
        if identity.get("workflow") and value.get("workflowName") != identity["workflow"]:
            raise WorkflowOperationError("run workflow differs from the bound workflow")
        if identity.get("attempt") is not None and value.get("attempt") != identity["attempt"]:
            raise WorkflowOperationError("run attempt differs from the bound attempt")
        return {
            "state": str(value.get("status") or "unknown").lower(),
            "conclusion": str(value.get("conclusion") or "").lower() or None,
            "workflow": value.get("workflowName"),
            "attempt": value.get("attempt"),
            "url": value.get("url"),
        }
    fields = "number,headRefOid,state,mergeStateStatus,autoMergeRequest,statusCheckRollup,url"
    completed = run_process(["gh", "pr", "view", str(identity["target_id"]), "--json", fields], root)
    value = json.loads(completed.stdout)
    if str(value.get("headRefOid")) != identity["head"]:
        raise WorkflowOperationError("PR head differs from the bound head")
    failures, pending = parse_status_checks(value.get("statusCheckRollup"))
    owner, name = identity["repository"].split("/", 1)
    query = "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){mergeQueueEntry{state}}}}"
    queue = run_process(
        [
            "gh",
            "api",
            "graphql",
            "-F",
            f"owner={owner}",
            "-F",
            f"name={name}",
            "-F",
            f"number={identity['target_id']}",
            "-f",
            f"query={query}",
        ],
        root,
    )
    queue_value = json.loads(queue.stdout)
    queue_entry = queue_value.get("data", {}).get("repository", {}).get("pullRequest", {}).get("mergeQueueEntry")
    runs = run_process(
        ["gh", "run", "list", "--event", "merge_group", "--limit", "50", "--json", "conclusion,headBranch,databaseId,headSha,status,workflowName,url"],
        root,
    )
    branch_marker = f"pr-{identity['target_id']}-{identity['head']}"
    merge_group_runs = [
        run
        for run in json.loads(runs.stdout)
        if branch_marker in str(run.get("headBranch") or "")
    ]
    merge_group_failures = [
        str(run.get("workflowName") or run.get("databaseId") or "merge-group")
        for run in merge_group_runs
        if str(run.get("conclusion") or "").lower() not in {"", "success", "neutral", "skipped"}
    ]
    return {
        "state": str(value.get("state") or "unknown").lower(),
        "merge_state": str(value.get("mergeStateStatus") or "unknown").lower(),
        "auto_merge": value.get("autoMergeRequest") is not None,
        "queue_state": str(queue_entry.get("state")).lower() if queue_entry else None,
        "failing_items": failures,
        "pending_items": pending,
        "merge_group_failures": merge_group_failures,
        "merge_group_runs": [str(run.get("databaseId")) for run in merge_group_runs],
        "url": value.get("url"),
    }


def observation_tuple(value):
    return digest(value)


def observation_terminal(kind, value):
    if kind == "run":
        return value.get("state") == "completed"
    return (
        value.get("state") in {"closed", "merged"}
        or value.get("merge_state") == "dirty"
        or bool(value.get("failing_items"))
        or bool(value.get("merge_group_failures"))
    )


def remote_identity(root, target_kind, target_id, head, workflow, attempt):
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": repository_slug(root),
        "repository_root": str(root),
        "branch": git(root, "branch", "--show-current"),
        "head": git(root, "rev-parse", head),
        "target_kind": target_kind,
        "target_id": str(target_id),
        "workflow": workflow,
        "attempt": attempt,
    }


def monitor_remote(root, workflow_run_id, target_kind, target_id, head, workflow, attempt, poll_seconds, timeout_seconds, observer=None):
    identity = remote_identity(root, target_kind, target_id, head, workflow, attempt)
    monitor_id = digest(identity)
    path = state_root(root) / "monitors" / f"{monitor_id}.json"
    with MonitorLease(path.with_suffix(".lock")):
        return monitor_remote_owned(root, workflow_run_id, target_kind, poll_seconds, timeout_seconds, observer, identity, monitor_id, path)


def monitor_remote_owned(root, workflow_run_id, target_kind, poll_seconds, timeout_seconds, observer, identity, monitor_id, path):
    if path.is_file():
        state = json.loads(path.read_text(encoding="utf-8"))
        expected = {key: identity[key] for key in identity}
        actual = {key: state["identity"][key] for key in identity}
        if expected != actual:
            raise WorkflowOperationError("persisted monitor identity differs from the requested identity")
        reconnected = True
    else:
        state = {
            "schema_version": SCHEMA_VERSION,
            "monitor_id": monitor_id,
            "identity": identity,
            "created_at": utc_now(),
            "last_observed_at": None,
            "last_observation": None,
            "last_signature": None,
            "active_execution_seconds": 0.0,
            "remote_waiting_seconds": 0.0,
            "suspended_offline_seconds": 0.0,
            "queries": 0,
            "unadmitted_observations": 0,
        }
        atomic_json(path, state)
        reconnected = False
    started = time.monotonic()
    while True:
        if time.monotonic() - started >= timeout_seconds:
            transition = "timeout"
            terminal = True
            observation = state["last_observation"]
            break
        wall_before = time.time()
        if state["last_observed_at"] is not None:
            gap = wall_before - state["last_observed_at"]
            expected_gap = poll_seconds
            if gap > max(DEFAULT_OFFLINE_GAP_SECONDS, expected_gap * 3):
                state["suspended_offline_seconds"] += max(0.0, gap - expected_gap)
        query_started = time.monotonic()
        try:
            observation = (observer or forge_observation)(root, state["identity"])
        except Exception as error:
            observation = {"state": "query-error", "error": str(error)[:DEFAULT_SUMMARY_BYTES]}
        state["active_execution_seconds"] += time.monotonic() - query_started
        state["queries"] += 1
        signature = observation_tuple(observation)
        changed = state["last_signature"] is not None and signature != state["last_signature"]
        terminal = observation_terminal(target_kind, observation) or observation.get("state") == "query-error"
        if (
            target_kind == "pr"
            and observation.get("state") == "open"
            and observation.get("merge_state") == "clean"
            and observation.get("auto_merge")
            and observation.get("queue_state") is None
            and not observation.get("pending_items")
            and not observation.get("failing_items")
            and not observation.get("merge_group_runs")
        ):
            state["unadmitted_observations"] += 1
        else:
            state["unadmitted_observations"] = 0
        if state["unadmitted_observations"] >= 6:
            observation["state"] = "green-unadmitted"
            terminal = True
        state["last_observed_at"] = time.time()
        state["last_observation"] = observation
        state["last_signature"] = signature
        atomic_json(path, state)
        if terminal or changed:
            transition = "terminal" if terminal else "material-transition"
            break
        wait_started = time.monotonic()
        time.sleep(poll_seconds)
        state["remote_waiting_seconds"] += time.monotonic() - wait_started
        atomic_json(path, state)
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation": "monitor",
        "monitor_id": monitor_id,
        "identity": state["identity"],
        "reconnected": reconnected,
        "transition": transition,
        "terminal": terminal,
        "observation": observation,
        "timing": {
            "active_execution_seconds": round(state["active_execution_seconds"], 3),
            "remote_waiting_seconds": round(state["remote_waiting_seconds"], 3),
            "suspended_offline_seconds": round(state["suspended_offline_seconds"], 3),
        },
        "queries": state["queries"],
        "state_artifact": str(path),
    }
    append_event(root, workflow_run_id, {"kind": "remote-monitor", "monitor_id": monitor_id, "transition": transition, **result["timing"]})
    return result


def skill_identities(root, workflow_run_id, lifecycle, technical, changed_paths=()):
    if not lifecycle:
        raise WorkflowOperationError("exactly one lifecycle skill is required")
    expected = set(routed_skills(root, changed_paths)) if changed_paths else set()
    supplied = {item.split("=", 1)[0] for item in technical}
    if supplied and supplied != expected:
        raise WorkflowOperationError(
            f"technical skill identities differ from direct routes: expected {sorted(expected)}, received {sorted(supplied)}"
        )
    technical = list(technical) if technical else sorted(expected)
    entries = [("lifecycle", lifecycle), *(("technical", item) for item in technical)]
    records = []
    for kind, entry in entries:
        if "=" in entry:
            name, raw_path = entry.split("=", 1)
        else:
            name = entry
            raw_path = f".agents/skills/{name}/SKILL.md"
        relative = Path(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise WorkflowOperationError("skill paths must stay inside the repository")
        path = (root / relative).resolve()
        ancestor = path
        for _ in relative.parts:
            ancestor = ancestor.parent
        if not ancestor.exists() or not os.path.samefile(root, ancestor):
            raise WorkflowOperationError("skill paths must stay inside the repository")
        if not path.is_file():
            raise WorkflowOperationError(f"skill body does not exist: {raw_path}")
        records.append({"kind": kind, "name": name, "path": relative.as_posix(), "sha256": sha256_file(path)})
    if len({record["name"] for record in records}) != len(records):
        raise WorkflowOperationError("skill identities must be unique")
    path = run_root(root, workflow_run_id) / "skills.json"
    previous = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"skills": []}
    known = {(item["kind"], item["name"], item["path"], item["sha256"]) for item in previous["skills"]}
    for record in records:
        record["action"] = "cached" if (record["kind"], record["name"], record["path"], record["sha256"]) in known else "load"
    stored = {"schema_version": SCHEMA_VERSION, "workflow_run_id": workflow_run_id, "skills": [{key: value for key, value in record.items() if key != "action"} for record in records]}
    atomic_json(path, stored)
    append_event(root, workflow_run_id, {"kind": "skills", "loads": sum(item["action"] == "load" for item in records), "cached": sum(item["action"] == "cached" for item in records)})
    return {"schema_version": SCHEMA_VERSION, "operation": "skills", "workflow_run_id": workflow_run_id, "skills": records, "identity_artifact": str(path)}


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def transcript_telemetry(path, host, offline_gap_seconds):
    counts = {"model_turns": 0, "tool_calls": 0, "wait_poll_calls": 0, "skill_load_calls": 0}
    token_usage = {"uncached_input_tokens": None, "cached_input_tokens": None, "output_tokens": None}
    turn_ids = set()
    reasoning_turns = 0
    assistant_turns = 0
    first_at = last_at = None
    last_tool_output = None
    suspended = 0.0
    pending = {}
    remote_wait = 0.0
    with Path(path).open("r", encoding="utf-8") as stream:
        for line in stream:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            at = parse_timestamp(item["timestamp"]) if item.get("timestamp") else None
            if at is not None:
                first_at = at if first_at is None else min(first_at, at)
                last_at = at if last_at is None else max(last_at, at)
            payload = item.get("payload", item)
            if item.get("type") == "token_usage_record":
                turn_ids.add(payload.get("turn_id"))
                usage = payload.get("thread_token_usage") or payload.get("usage") or {}
                input_tokens = usage.get("input_tokens")
                cached = usage.get("cached_input_tokens")
                token_usage = {
                    "uncached_input_tokens": input_tokens - cached if isinstance(input_tokens, int) and isinstance(cached, int) else None,
                    "cached_input_tokens": cached if isinstance(cached, int) else None,
                    "output_tokens": usage.get("output_tokens") if isinstance(usage.get("output_tokens"), int) else None,
                }
            response_type = payload.get("type")
            if response_type == "reasoning":
                reasoning_turns += 1
            elif response_type == "message" and payload.get("role") == "assistant":
                assistant_turns += 1
            if response_type in {"custom_tool_call", "function_call"}:
                counts["tool_calls"] += 1
                name = str(payload.get("name") or "")
                raw = str(payload.get("input") or payload.get("arguments") or "")
                nested_waits = len(re.findall(r"tools\.(?:write_stdin|wait)\s*\(", raw)) if name == "exec" else 0
                if name in {"wait", "write_stdin", "wait_agent"}:
                    counts["wait_poll_calls"] += 1
                elif nested_waits:
                    counts["wait_poll_calls"] += nested_waits
                elif re.search(r"\b(?:sleep|poll)\b", raw, re.IGNORECASE):
                    counts["wait_poll_calls"] += 1
                if "SKILL.md" in raw:
                    counts["skill_load_calls"] += 1
                pending[payload.get("call_id")] = (at, "workflow_ops.py" in raw and "monitor" in raw or "gh run watch" in raw)
                if last_tool_output is not None and at is not None and at - last_tool_output > offline_gap_seconds:
                    suspended += at - last_tool_output
                last_tool_output = None
            elif response_type in {"custom_tool_call_output", "function_call_output"}:
                started = pending.pop(payload.get("call_id"), None)
                if started and started[0] is not None and at is not None and started[1]:
                    remote_wait += max(0.0, at - started[0])
                last_tool_output = at
    counts["model_turns"] = reasoning_turns or assistant_turns or len({turn for turn in turn_ids if turn})
    elapsed = max(0.0, (last_at or 0) - (first_at or 0)) if first_at is not None else 0.0
    active = max(0.0, elapsed - remote_wait - suspended)
    return {
        **counts,
        **token_usage,
        "active_execution_seconds": round(active, 3),
        "remote_waiting_seconds": round(remote_wait, 3),
        "suspended_offline_seconds": round(suspended, 3),
        "host": host,
        "token_source": "host-transcript" if token_usage["uncached_input_tokens"] is not None else "unavailable",
    }


def load_budget(root):
    path = root / ".agents" / "workflow-budgets.json"
    if not path.is_file():
        path = Path(__file__).resolve().parent / "budgets.json"
    if not path.is_file():
        return {"soft": {}, "hard": {}, "mechanism_limits": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def budget_result(metrics, budget):
    breaches = []
    for level in ("soft", "hard"):
        for name, limit in budget.get(level, {}).items():
            value = metrics.get(name)
            if value is not None and value > limit:
                breaches.append({"level": level, "metric": name, "value": value, "limit": limit})
    return {"allowed": not any(item["level"] == "hard" for item in breaches), "breaches": breaches}


def telemetry(root, workflow_run_id, transcript, host, offline_gap_seconds):
    metrics = transcript_telemetry(transcript, host, offline_gap_seconds)
    policy = load_budget(root)
    result = {"schema_version": SCHEMA_VERSION, "operation": "telemetry", "workflow_run_id": workflow_run_id, "metrics": metrics, "budget": budget_result(metrics, policy), "policy": policy}
    append_event(root, workflow_run_id, {"kind": "telemetry-snapshot", **metrics})
    return result


def delivery_owner(root, workflow_run_id, ledger=None, pr_url=None):
    repository = repository_slug(root)
    branch = git(root, "branch", "--show-current")
    references = {}
    new_slice = False
    if ledger:
        provider = workflow_runtime.RepositoryStateProvider(root, workflow_runtime.WorkflowContract())
        state = provider.resolve(ledger, workflow_run_id, "delivery-preflight")
        artifacts = state["artifacts"]
        new_slice = "pull_request" in artifacts and artifacts["pull_request"] is None
        if artifacts.get("pull_request"):
            references["ledger"] = artifacts["pull_request"]
    if pr_url:
        references["argument"] = pr_url
    binding_path = root / delivery_runtime.BINDING_FILE
    if binding_path.is_file():
        binding = delivery_runtime.binding_from_artifact(json.loads(binding_path.read_text(encoding="utf-8")))
        delivery_runtime.PersistentDeliveryRouter().validate_binding(binding)
        if binding["repository"].casefold() != repository.casefold():
            raise WorkflowOperationError("delivery binding belongs to another repository")
        if Path(binding["worktree"]).resolve() != root.resolve():
            raise WorkflowOperationError("delivery binding belongs to another worktree")
        references["binding"] = binding["pr_url"]
    numbers = set()
    for reference in references.values():
        match = re.fullmatch(r"https://github\.com/([^/\s]+/[^/\s]+)/pull/([1-9][0-9]*)", reference)
        if not match or match[1].casefold() != repository.casefold():
            raise WorkflowOperationError("owning PR must be a GitHub URL in this repository")
        numbers.add(int(match[2]))
    if len(numbers) > 1:
        raise WorkflowOperationError("recorded delivery owners disagree; reconcile the ledger and binding")
    fields = "number,url,headRefName,headRefOid,baseRefName,state,isCrossRepository"
    if references:
        number = next(iter(numbers))
        value = json.loads(run_process(
            ["gh", "pr", "view", str(number), "--repo", repository, "--json", fields], root
        ).stdout)
        source = next(iter(references))
        if value.get("number") != number:
            raise WorkflowOperationError("forge returned a different owning PR")
    else:
        matches = json.loads(run_process(
            ["gh", "pr", "list", "--repo", repository, "--head", branch, "--state", "open",
             "--limit", "2", "--json", fields], root
        ).stdout)
        if len(matches) > 1:
            raise WorkflowOperationError("several open PRs use this branch; resolve the work's review")
        if not matches:
            return {"source": "ledger" if new_slice else "unresolved", "pr_url": None,
                    "action": "create" if new_slice else "assess-scope"}
        value = matches[0]
        source = "branch"
    if not all(value.get(key) for key in ("url", "headRefName", "headRefOid", "baseRefName", "state")):
        raise WorkflowOperationError("forge returned incomplete owning PR state")
    expected_url = f"https://github.com/{repository}/pull/{value.get('number')}"
    if str(value["url"]).casefold() != expected_url.casefold():
        raise WorkflowOperationError("forge returned a PR outside this repository")
    if value["state"].upper() != "OPEN" or value.get("isCrossRepository"):
        action = "reconcile-review"
    else:
        action = "update" if value["headRefName"] == branch else "integrate"
    return {"source": source, "pr_url": value["url"], "branch": value["headRefName"],
            "head": value["headRefOid"], "base": value["baseRefName"], "action": action}


def delivery_preflight(root, workflow_run_id, descriptor_path, base_ref, ledger=None, pr_url=None):
    ownership = delivery_owner(root, workflow_run_id, ledger, pr_url)
    owning_base = f"origin/{ownership['base']}" if ownership.get("base") else None
    base_ref = base_ref or owning_base or "origin/main"
    inspection = inspect_repository(root, workflow_run_id)
    review = review_reconcile(root, workflow_run_id, descriptor_path, base_ref) if descriptor_path else None
    counts = git(root, "rev-list", "--left-right", "--count", f"{base_ref}...HEAD").split()
    base_behind = int(counts[0]) if len(counts) == 2 else None
    branch_valid = bool(re.fullmatch(r"[A-Z][A-Za-z0-9-]*/[A-Z][A-Za-z0-9-]*", inspection["branch"]))
    code_dirty = [path for path in inspection["dirty_paths"] if Path(path).suffix.lower() != ".md"]
    reviewed_base_movement = bool(
        review
        and review["exact_head"]
        and review["base_moved"]
        and not review["review_required"]
    )
    blockers = []
    if ownership["action"] not in {"create", "update"}:
        blockers.append("delivery-" + ownership["action"])
    if owning_base and git(root, "rev-parse", base_ref) != git(root, "rev-parse", owning_base):
        blockers.append("owning-review-base-mismatch")
    if not branch_valid:
        blockers.append("invalid-feature-branch")
    if inspection["behind"]:
        blockers.append("local-behind-upstream")
    if base_behind and not reviewed_base_movement:
        blockers.append("base-ahead-before-final-review")
    if code_dirty:
        blockers.append("uncommitted-code")
    if review and review["review_required"]:
        blockers.append("review-invalidated")
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation": "delivery-preflight",
        "ownership": ownership,
        "identity": {key: inspection[key] for key in ("repository", "root", "branch", "head", "upstream", "ahead", "behind")},
        "base_behind": base_behind,
        "branch_valid": branch_valid,
        "code_dirty_paths": code_dirty,
        "documentation_dirty_paths": [path for path in inspection["dirty_paths"] if path not in code_dirty],
        "review": review,
        "blockers": blockers,
        "ready": not blockers,
    }
    append_event(root, workflow_run_id, {"kind": "operation", "operation": "delivery-preflight", "ready": result["ready"]})
    return result


def settings_env(path):
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    environment = parsed.get("env")
    if not isinstance(environment, dict):
        return None
    value = environment.get(GOAL_EVALUATOR_VARIABLE)
    return value if isinstance(value, str) and value.strip() else None


def goal_evaluator_scopes(root):
    """Every persisted home for the evaluator override, highest precedence first.

    A session reads `env` from settings at start, so the value this process sees proves only the
    session it is running in. A fresh session reads the files, which is why they are reported too.
    """
    home = Path(os.path.expanduser("~"))
    if os.name == "nt":
        managed = [Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "ClaudeCode" / "managed-settings.json"]
    else:
        managed = [
            Path("/Library/Application Support/ClaudeCode/managed-settings.json"),
            Path("/etc/claude-code/managed-settings.json"),
        ]
    return [("managed", path) for path in managed] + [
        ("local", root / ".claude" / "settings.local.json"),
        ("project", root / ".claude" / "settings.json"),
        ("user", home / ".claude" / "settings.json"),
    ]


def goal_preflight(root, workflow_run_id):
    """`persistent-workflow`'s `/goal` prerequisite, executed rather than asserted in prose."""
    scopes = []
    persisted = None
    for name, path in goal_evaluator_scopes(root):
        value = settings_env(path)
        scopes.append({"scope": name, "path": str(path), "model": value})
        if value is not None and persisted is None:
            persisted = {"scope": name, "model": value}
    session = os.environ.get(GOAL_EVALUATOR_VARIABLE) or None
    effective = session or (persisted or {}).get("model")
    sonnet = bool(effective) and "sonnet" in effective.lower()
    durable = bool(persisted) and "sonnet" in persisted["model"].lower()
    ready = sonnet and durable
    result = {
        "schema_version": SCHEMA_VERSION,
        "operation": "goal-preflight",
        "variable": GOAL_EVALUATOR_VARIABLE,
        "session_value": session,
        "effective_model": effective,
        "resolved_from": "session" if session else (persisted or {}).get("scope"),
        "persisted_scopes": scopes,
        "evaluator_is_sonnet": sonnet,
        "survives_a_fresh_session": durable,
        "ready": ready,
        "stop_reason": None if ready else "goal-evaluator-model-unavailable",
    }
    if not ready:
        result["exit_state"] = "failed"
    append_event(root, workflow_run_id, {"kind": "operation", "operation": "goal-preflight", "ready": ready})
    return result


def pull_request_state(root, pr, repo=None):
    fields = "number,url,body,headRefOid,headRefName,state,isDraft,labels,files,changedFiles,statusCheckRollup"
    arguments = ["gh", "pr", "view"]
    if pr is not None:
        arguments.append(str(pr))
    arguments += ["--json", fields]
    if repo is not None:
        arguments += ["--repo", repo]
    return json.loads(run_process(arguments, root).stdout)


def pr_body_check(root, pr, repo=None):
    value = pull_request_state(root, pr, repo)
    validation = validate_pr_body(value.get("body"))
    if not isinstance(value.get("number"), int) or not value.get("url") or not value.get("headRefOid"):
        raise WorkflowOperationError("gh pr view returned no usable PR identity")
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "pr-body-check",
        "pr": value["number"],
        "url": value["url"],
        "head": value["headRefOid"],
        "validation": validation,
        "exit_state": "passed" if validation["valid"] else "failed",
    }


def changed_paths(root, pr, reported, expected_count=None):
    """Every path the PR changes, from GitHub's paginated pull-files endpoint.

    `gh pr view --json files` stops at 100 entries and `gh pr diff` is unavailable once a pull request
    exceeds GitHub's unified-diff file limit. Standing authorization needs the complete path set, so use
    the paginated REST collection, require every summary path, and verify GitHub's authoritative count.
    """
    endpoint = f"repos/{repository_slug(root)}/pulls/{pr}/files?per_page=100"
    completed = run_process(
        ["gh", "api", "--paginate", endpoint, "--jq", ".[].filename"], root, check=False
    )
    if completed.returncode != 0:
        raise WorkflowOperationError(
            "cannot read the PR's complete changed-path set, so no authorization can be resolved: "
            + (completed.stderr or "").strip()[:DEFAULT_SUMMARY_BYTES]
        )
    paths = sorted({line.strip() for line in completed.stdout.splitlines() if line.strip()})
    missing = sorted(set(reported) - set(paths))
    count_disagrees = isinstance(expected_count, int) and len(paths) != expected_count
    if not paths or missing or count_disagrees:
        detail = f"; missing reported paths: {', '.join(missing[:5])}" if missing else ""
        if count_disagrees:
            detail += f"; API returned {len(paths)} of {expected_count} changed paths"
        raise WorkflowOperationError(
            "the paginated PR file set is empty or disagrees with the PR summary"
            + detail
            + "; the changed-path set is not established"
        )
    return paths

def pending_evidence(rollup, head):
    """Every not-yet-terminal check as an exact `(check id, run id, head)` triple.

    A CheckRun's run and job ids are only published in its details URL, and that pair is precisely
    the identity `persistent-delivery` refuses to merge without.
    """
    evidence = []
    seen = set()
    for check in rollup or []:
        if not isinstance(check, dict):
            continue
        name = check.get("name") or check.get("context")
        status = str(check.get("status") or "").lower()
        state = str(check.get("state") or "").lower()
        terminal = status in {"completed", "success"} or state in {
            "success",
            "failure",
            "error",
            "neutral",
            "skipped",
        }
        if terminal:
            continue
        url = str(check.get("detailsUrl") or check.get("targetUrl") or "")
        match = re.search(r"/actions/runs/(\d+)(?:/job/(\d+))?", url)
        run_id = match.group(1) if match else (name or "unknown")
        check_id = (match.group(2) if match and match.group(2) else None) or (name or "unknown")
        identity = (str(check_id), str(run_id))
        if identity in seen:
            continue
        seen.add(identity)
        evidence.append({"check_id": str(check_id), "run_id": str(run_id), "head_sha": head})
    return evidence


def resolved_commit(root, revision):
    """`revision` as a full SHA this checkout knows, or None. A work order may stamp an abbreviation."""
    completed = run_process(["git", "rev-parse", "--verify", f"{revision}^{{commit}}"], root, check=False)
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value if delivery_runtime.SHA_PATTERN.fullmatch(value) else None


def review_is_current(root, reviewed, head):
    """Whether review evidence at `reviewed` still covers `head`.

    Stamping the watermark is itself a commit, so evidence can never sit at the commit containing it.
    `merge_review_gate.review_only` already answers this for the merge; answering it differently here
    would have the binding call a head unreviewed that the gate calls reviewed, and send every
    delivery back through a full `review` after each stamp.
    """
    if reviewed == head:
        return True
    completed = run_process(["git", "diff", "--name-only", f"{reviewed}..{head}"], root, check=False)
    if completed.returncode != 0:
        return False
    changed = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    return bool(changed) and all(path.startswith("reviews/") for path in changed)


def review_binding(root, branch, head):
    slug = branch.replace("/", "-").replace("\\", "-")
    work_order = f"reviews/{slug}.md"
    watermark = None
    try:
        body = (root / work_order).read_text(encoding="utf-8")
    except OSError:
        body = ""
    match = re.search(r"Reviewed up to commit:\*{0,2}\s*`([0-9a-f]{7,40})`", body)
    # Resolve before comparing: an abbreviated stamp at the head is not string-equal to it, and the
    # empty diff that follows would read as "nothing reviewed" rather than "reviewed here".
    reviewed = resolved_commit(root, match.group(1)) if match else None
    if reviewed is not None and review_is_current(root, reviewed, head):
        watermark = reviewed
    return {"work_order": work_order, "work_order_order": ["full"], "reviewed_sha": watermark}


def standing_authorization(root, changed_paths, labels):
    path = root / delivery_runtime.STANDING_AUTHORIZATION_FILE
    if not path.is_file():
        resolution = delivery_runtime.StandingMergeAuthorization().resolve(
            {"standing_authorization": "absent", "instruction": None, "hold_label": "human-gate"},
            changed_paths, labels,
        )
        if resolution["stopped_by"] is None:
            resolution["stopped_by"] = {"class": "no-recorded-authorization"}
        return resolution
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise WorkflowOperationError(
            f"{delivery_runtime.STANDING_AUTHORIZATION_FILE} exists but could not be read: {error}"
        ) from error
    try:
        return delivery_runtime.StandingMergeAuthorization().resolve(policy, changed_paths, labels)
    except delivery_runtime.DeliveryContractViolation as error:
        raise WorkflowOperationError(str(error)) from error


def scoped_approval(root, repository, number, branch, supplied):
    expected = {"repository": repository, "pr_number": number, "worktree": str(root), "branch": branch}
    explicit = supplied is not None
    if explicit:
        try:
            record = json.loads(Path(supplied).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise WorkflowOperationError(f"approval record could not be read: {error}") from error
    else:
        path = root / delivery_runtime.BINDING_FILE
        record = json.loads(path.read_text(encoding="utf-8")).get("scoped_approval") if path.is_file() else None
    if record is None and not explicit:
        return None
    fields = set(expected) | {"mode", "instruction", "source"}
    if (not isinstance(record, dict) or set(record) != fields
            or type(record.get("pr_number")) is not int
            or not isinstance(record.get("mode"), str)
            or record.get("mode") not in {"auto", "merge"}
            or any(not isinstance(record.get(key), str) or not record[key].strip()
                   for key in ("worktree", "instruction", "source"))
            or not Path(record["worktree"]).is_absolute()):
        raise WorkflowOperationError("approval record requires exact identity, merge mode, user instruction and source")
    matches = all(record[key] == value for key, value in expected.items())
    matches = matches and git(root, "branch", "--show-current") == branch
    if not matches:
        if explicit:
            raise WorkflowOperationError("approval record does not match this repository/PR/worktree/branch")
        return None
    return record


def delivery_bind(root, workflow_run_id, pr, completion_condition, handoff, approval_record=None):
    value = pull_request_state(root, pr)
    validation = validate_pr_body(value.get("body"))
    if not validation["valid"]:
        raise WorkflowOperationError("; ".join(validation["errors"]))
    head = str(value.get("headRefOid") or "")
    branch = str(value.get("headRefName") or "")
    number = value.get("number")
    if not isinstance(number, int) or not re.fullmatch(r"[0-9a-f]{40}", head) or not branch:
        raise WorkflowOperationError("gh pr view returned no usable PR number, head, or branch")
    state = str(value.get("state") or "").lower()
    if state != "open":
        raise WorkflowOperationError(f"PR #{number} is {state or 'unknown'}, so it owns no delivery")
    reported = [str(item.get("path")) for item in value.get("files") or [] if item.get("path")]
    changed = changed_paths(root, number, reported, value.get("changedFiles"))
    labels = [str(item.get("name")) for item in value.get("labels") or [] if item.get("name")]
    repository = repository_slug(root)
    approval = scoped_approval(root, repository, number, branch, approval_record)
    resolution = standing_authorization(root, changed, labels)
    if approval is not None and (resolution["stopped_by"] is None
                                 or resolution["stopped_by"]["class"] == "no-recorded-authorization"):
        resolution["merge_authorization"] = {"mode": approval["mode"], "instruction": approval["instruction"]}
        resolution["stopped_by"] = None
    binding = {
        "repository": repository,
        "pr_url": str(value.get("url") or ""),
        "pr_number": number,
        "worktree": str(root),
        "branch": branch,
        "remote_head_sha": head,
        "pending_evidence": pending_evidence(value.get("statusCheckRollup"), head),
        "review": review_binding(root, branch, head),
        "merge_authorization": resolution["merge_authorization"],
        "completion_condition": completion_condition,
    }
    if handoff is not None:
        binding["workflow_handoff"] = handoff
    try:
        delivery_runtime.PersistentDeliveryRouter().validate_binding(binding)
    except delivery_runtime.DeliveryContractViolation as error:
        raise WorkflowOperationError(str(error)) from error
    artifact = delivery_runtime.artifact_from_binding(
        binding,
        schema_version=SCHEMA_VERSION,
        bound_at=utc_now(),
        authorization_resolution={
            "standing": resolution["standing"],
            "stopped_by": resolution["stopped_by"],
        },
        changed_path_count=len(changed),
    )
    if approval is not None:
        artifact["scoped_approval"] = approval
    atomic_json(root / delivery_runtime.BINDING_FILE, artifact)
    append_event(
        root,
        workflow_run_id,
        {
            "kind": "operation",
            "operation": "delivery-bind",
            "pr": number,
            "head": head,
            "authorization": resolution["merge_authorization"]["mode"],
        },
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "delivery-bind",
        "artifact": delivery_runtime.BINDING_FILE,
        "binding": artifact,
        "authorization_resolution": resolution,
    }


def delivery_release(root, workflow_run_id, reason):
    """Delete the binding artifact at a terminal, which is what ends unattended auto-merge."""
    path = root / delivery_runtime.BINDING_FILE
    existed = path.is_file()
    path.unlink(missing_ok=True)
    append_event(
        root,
        workflow_run_id,
        {"kind": "operation", "operation": "delivery-release", "reason": reason, "existed": existed},
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "delivery-release",
        "artifact": delivery_runtime.BINDING_FILE,
        "removed": existed,
        "reason": reason,
    }


def cleanup(root, workflow_run_id, retention_days):
    cutoff = time.time() - retention_days * 86400
    base = state_root(root)
    removed = []
    for path in base.rglob("*"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()
            removed.append(str(path))
    append_event(root, workflow_run_id, {"kind": "operation", "operation": "cleanup", "removed": len(removed)})
    return {"schema_version": SCHEMA_VERSION, "operation": "cleanup", "removed_count": len(removed), "retention_days": retention_days}


def parser():
    result = argparse.ArgumentParser()
    result.add_argument("--root", default=".")
    result.add_argument("--workflow-run-id", required=True)
    commands = result.add_subparsers(dest="operation", required=True)

    run = commands.add_parser("run")
    run.add_argument("--label", required=True)
    run.add_argument("--summary-lines", type=int, default=DEFAULT_SUMMARY_LINES)
    run.add_argument("--failure-items", type=int, default=DEFAULT_FAILURE_ITEMS)
    run.add_argument("--summary-bytes", type=int, default=DEFAULT_SUMMARY_BYTES)
    run.add_argument("command", nargs=argparse.REMAINDER)

    commands.add_parser("inspect")

    review = commands.add_parser("review-prepare")
    review.add_argument("--base", default="origin/main")
    review.add_argument("--head", default="HEAD")
    review.add_argument("--synchronize", action="store_true")

    reconcile = commands.add_parser("review-reconcile")
    reconcile.add_argument("--descriptor", required=True)
    reconcile.add_argument("--base", default="origin/main")

    monitor = commands.add_parser("monitor")
    monitor.add_argument("--kind", choices=("run", "pr"), required=True)
    monitor.add_argument("--id", required=True)
    monitor.add_argument("--head", default="HEAD")
    monitor.add_argument("--workflow")
    monitor.add_argument("--attempt", type=int)
    monitor.add_argument("--poll-seconds", type=float, default=DEFAULT_POLL_SECONDS)
    monitor.add_argument("--timeout-seconds", type=float, default=DEFAULT_MONITOR_SECONDS)

    skills = commands.add_parser("skills")
    skills.add_argument("--lifecycle", required=True)
    skills.add_argument("--technical", action="append", default=[])
    skills.add_argument("--changed-path", action="append", default=[])

    usage = commands.add_parser("telemetry")
    usage.add_argument("--transcript", required=True)
    usage.add_argument("--host", choices=("codex", "claude"), required=True)
    usage.add_argument("--offline-gap-seconds", type=float, default=DEFAULT_OFFLINE_GAP_SECONDS)

    preflight = commands.add_parser("delivery-preflight")
    preflight.add_argument("--descriptor")
    preflight.add_argument("--base")
    preflight.add_argument("--ledger")
    preflight.add_argument("--pr-url")

    commands.add_parser("goal-preflight")

    body_check = commands.add_parser("pr-body-check")
    body_check.add_argument("--pr", required=True)
    body_check.add_argument("--repo")

    bind = commands.add_parser("delivery-bind")
    bind.add_argument("--pr", type=int)
    bind.add_argument("--approval-record")
    bind.add_argument(
        "--completion-condition",
        default="the bound PR reaches MERGED, or a recorded terminal ends this delivery",
    )
    bind.add_argument("--workflow-id")
    bind.add_argument("--state-artifact")
    bind.add_argument("--next-stage")

    release = commands.add_parser("delivery-release")
    release.add_argument("--reason", required=True)

    cleanup_parser = commands.add_parser("cleanup")
    cleanup_parser.add_argument("--retention-days", type=int, default=14)
    return result


def main(argv=None):
    arguments = parser().parse_args(argv)
    root = repository_root(Path(arguments.root).resolve())
    if arguments.operation != "pr-body-check":
        run_root(root, arguments.workflow_run_id)
    if arguments.operation == "run":
        command = arguments.command[1:] if arguments.command[:1] == ["--"] else arguments.command
        result = compact_run(root, arguments.workflow_run_id, arguments.label, command, arguments.summary_lines, arguments.failure_items, arguments.summary_bytes)
    elif arguments.operation == "inspect":
        result = inspect_repository(root, arguments.workflow_run_id)
    elif arguments.operation == "review-prepare":
        result = review_prepare(root, arguments.workflow_run_id, arguments.base, arguments.head, arguments.synchronize)
    elif arguments.operation == "review-reconcile":
        result = review_reconcile(root, arguments.workflow_run_id, arguments.descriptor, arguments.base)
    elif arguments.operation == "monitor":
        result = monitor_remote(root, arguments.workflow_run_id, arguments.kind, arguments.id, arguments.head, arguments.workflow, arguments.attempt, arguments.poll_seconds, arguments.timeout_seconds)
    elif arguments.operation == "skills":
        result = skill_identities(root, arguments.workflow_run_id, arguments.lifecycle, arguments.technical, arguments.changed_path)
    elif arguments.operation == "telemetry":
        result = telemetry(root, arguments.workflow_run_id, arguments.transcript, arguments.host, arguments.offline_gap_seconds)
    elif arguments.operation == "delivery-preflight":
        result = delivery_preflight(root, arguments.workflow_run_id, arguments.descriptor, arguments.base,
                                    arguments.ledger, arguments.pr_url)
    elif arguments.operation == "goal-preflight":
        result = goal_preflight(root, arguments.workflow_run_id)
    elif arguments.operation == "pr-body-check":
        result = pr_body_check(root, arguments.pr, arguments.repo)
    elif arguments.operation == "delivery-bind":
        declared = (arguments.workflow_id, arguments.state_artifact, arguments.next_stage)
        if any(declared) and not all(declared):
            raise WorkflowOperationError(
                "a workflow handoff needs its id, state artifact, and next stage together"
            )
        handoff = (
            {
                "workflow_id": arguments.workflow_id,
                "state_artifact": arguments.state_artifact,
                "next_stage": arguments.next_stage,
            }
            if all(declared)
            else None
        )
        result = delivery_bind(
            root, arguments.workflow_run_id, arguments.pr, arguments.completion_condition, handoff,
            arguments.approval_record,
        )
    elif arguments.operation == "delivery-release":
        result = delivery_release(root, arguments.workflow_run_id, arguments.reason)
    else:
        result = cleanup(root, arguments.workflow_run_id, arguments.retention_days)
    emit(result)
    if arguments.operation == "delivery-preflight" and not result["ready"]:
        return 1
    return 0 if result.get("exit_state") != "failed" and result.get("budget", {}).get("allowed", True) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (WorkflowOperationError, OSError, ValueError, json.JSONDecodeError) as error:
        emit({"schema_version": SCHEMA_VERSION, "operation": "error", "error": str(error)[:DEFAULT_SUMMARY_BYTES]})
        raise SystemExit(2)
