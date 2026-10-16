import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path


class ReviewEvidenceError(RuntimeError):
    pass


def git_text(root, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=str(root), check=True, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=30,
    ).stdout.strip()


def normalized(path):
    return os.path.normcase(str(Path(path).resolve()))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def legacy_path(root, branch):
    slug = branch.replace("/", "-").replace("\\", "-")
    path = Path(root) / "reviews" / f"{slug}.md"
    reject_redirects((path.parent, path))
    return path


def reject_redirects(paths):
    for path in paths:
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ReviewEvidenceError("review state contains a redirected path")


def private_paths(root, branch, git=None):
    root = Path(root).resolve()
    marker = root / ".git"
    if not marker.exists():
        return None
    if marker.is_symlink():
        raise ReviewEvidenceError("review state cannot use a redirected Git directory")
    if marker.is_dir():
        common = marker
    else:
        reader = git or (lambda *args: git_text(root, *args))
        common = Path(reader("rev-parse", "--path-format=absolute", "--git-common-dir"))
        if not common.is_absolute():
            common = root / common
    common = common.resolve()
    identity = {"repository": normalized(common), "checkout": normalized(root), "branch": branch}
    key = digest(json.dumps(identity, sort_keys=True).encode("utf-8"))
    directory = common / "agent-workflow" / "reviews" / key
    reject_redirects((directory.parent.parent, directory.parent, directory,
                      directory / "work-order.md", directory / "proof.json"))
    return {"body": directory / "work-order.md", "receipt": directory / "proof.json", "identity": identity}


def work_order_path(root, branch, git=None):
    locations = private_paths(root, branch, git)
    if locations and any(locations[key].exists() for key in ("body", "receipt")):
        return locations["body"]
    legacy = legacy_path(root, branch)
    if legacy.exists():
        return legacy
    if locations is None:
        raise ReviewEvidenceError("private review requires a Git checkout")
    return locations["body"]


def prepare_path(root, branch, durable=False):
    path = work_order_path(root, branch)
    if durable:
        target = legacy_path(root, branch)
        if path != target and path.exists():
            if target.exists():
                raise ReviewEvidenceError("both private and durable review bodies exist")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
            locations = private_paths(root, branch)
            locations["receipt"].unlink(missing_ok=True)
            path.unlink()
        path = target
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve(root, branch, head, git=None):
    reader = git or (lambda *args: git_text(root, *args))
    locations = private_paths(root, branch, reader)
    if locations and any(locations[key].exists() for key in ("body", "receipt")):
        try:
            raw = locations["body"].read_bytes()
            proof = json.loads(locations["receipt"].read_text(encoding="utf-8"))
            expected = {"schema_version", "identity", "head", "descriptor_id", "body_sha256"}
            if (not isinstance(proof, dict) or set(proof) != expected
                    or type(proof["schema_version"]) is not int or proof["schema_version"] != 1):
                raise ReviewEvidenceError("private review proof has an invalid shape")
            if proof["identity"] != locations["identity"]:
                raise ReviewEvidenceError("private review belongs to another repository, checkout or branch")
            if proof["head"] != head:
                raise ReviewEvidenceError("private review evidence is stale")
            if proof["body_sha256"] != digest(raw):
                raise ReviewEvidenceError("private review body changed after completion")
            descriptor_id = proof["descriptor_id"]
            if not isinstance(descriptor_id, str) or len(descriptor_id) != 64 or any(
                char not in "0123456789abcdef" for char in descriptor_id
            ):
                raise ReviewEvidenceError("private review descriptor identity is invalid")
            return {"body": raw.decode("utf-8"), "path": locations["body"], "private": True}
        except (OSError, ValueError, UnicodeError) as error:
            raise ReviewEvidenceError("private review proof is missing or unreadable") from error
    path = legacy_path(root, branch)
    relative = path.relative_to(Path(root)).as_posix()
    try:
        body = reader("show", f"{head}:{relative}")
    except (OSError, RuntimeError, subprocess.SubprocessError):
        try:
            body = path.read_text(encoding="utf-8")
        except OSError as error:
            raise ReviewEvidenceError("current review work order is absent") from error
    return {"body": body, "path": path, "private": False}


def record(root, branch, head, descriptor_id, path, body):
    locations = private_paths(root, branch)
    if locations is None or Path(path).resolve() != locations["body"]:
        raise ReviewEvidenceError("private proof must use the canonical private review body")
    proof = {
        "schema_version": 1, "identity": locations["identity"], "head": head,
        "descriptor_id": descriptor_id, "body_sha256": digest(body),
    }
    target = locations["receipt"]
    handle, temporary = tempfile.mkstemp(prefix="proof-", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(proof, stream, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return proof
