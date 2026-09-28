import hashlib
import os
from pathlib import Path
import runpy
import shutil
import sys
import uuid


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(2)


def digest_tree(root, plugin):
    excluded = {"hooks/codex.json"}
    if plugin == "machine":
        excluded.add("catalog/catalog.json")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink():
            fail("Codex hook package contains a symbolic link")
        if path.is_dir():
            continue
        if not path.is_file():
            fail("Codex hook package contains an unsupported entry")
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        content = path.read_bytes()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            content = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(content)).encode("ascii"))
        digest.update(b"\0")
        digest.update(content)
    return "sha256:" + digest.hexdigest()


def verified(root, expected, plugin):
    if not root.is_dir() or root.is_symlink() or digest_tree(root, plugin) != expected:
        fail("Codex hook package integrity check failed")


def main():
    root = Path(sys.argv[1])
    expected = sys.argv[2]
    plugin = sys.argv[3]
    script = Path(sys.argv[4])
    relative = script.relative_to(root)
    if root.parent.name != plugin or relative.is_absolute() or ".." in relative.parts:
        fail("Codex hook package identity is invalid")
    data = os.environ.get("PLUGIN_DATA")
    if not data:
        fail("Codex hook data directory is unavailable")
    snapshot_dir = Path(data).resolve() / "hook-snapshots"
    key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()
    snapshot = snapshot_dir / key
    if not snapshot.is_dir():
        verified(root, expected, plugin)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        temporary = snapshot_dir / (key + "." + uuid.uuid4().hex)
        shutil.copytree(root, temporary, symlinks=True)
        try:
            verified(temporary, expected, plugin)
            try:
                temporary.rename(snapshot)
            except OSError:
                if not snapshot.is_dir():
                    raise
        finally:
            if temporary.is_dir():
                shutil.rmtree(temporary)
    selected = snapshot
    verified(snapshot, expected, plugin)
    target = selected / relative
    if not target.is_file():
        fail("Codex hook script is unavailable")
    sys.path.insert(0, str(target.parent))
    sys.argv = [str(target), *(value.replace(str(root), str(selected), 1) for value in sys.argv[5:])]
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        fail("Codex hook snapshot failed: " + str(error))
