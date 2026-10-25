"""Stage declared publisher runtime sources for self-contained Core packages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 120


def safe_path(root: Path, relative_path: str) -> Path:
    target = root / relative(relative_path)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Runtime path escapes its owner: {target}")
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise ValueError(f"Runtime path traverses a link: {part}")
    return target


def relative(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"Unsafe source path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise ValueError(f"Unsafe source path: {value!r}")
    return value


def files(directory: Path) -> dict[str, bytes]:
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError(f"Runtime source contains a link: {path}")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result[path.relative_to(directory).as_posix()] = path.read_bytes()
    return result


def digest(contents: dict[str, bytes]) -> str:
    value = hashlib.sha256()
    for name, body in sorted(contents.items()):
        value.update(name.encode("utf-8") + b"\0" + str(len(body)).encode("ascii") + b"\0" + body)
    return value.hexdigest()


def declarations(root: Path) -> dict[str, dict]:
    path = root / ".agents/plugins/runtime-sources.json"
    if not path.exists():
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    if set(document) != {"schema_version", "sources"} or document["schema_version"] != 1:
        raise ValueError("Invalid runtime source declaration")
    sources = document["sources"]
    if not isinstance(sources, dict):
        raise ValueError("Runtime sources must be an object")
    for name, source in sources.items():
        if not name.isascii() or not name.replace("-", "").isalnum() or name.lower() != name:
            raise ValueError(f"Invalid runtime source name: {name!r}")
        if not isinstance(source, dict) or set(source) != {"repository", "exports"}:
            raise ValueError(f"Invalid runtime source: {name}")
        repository = source["repository"]
        if not isinstance(repository, str) or not re.fullmatch(r"tj-agents/[a-z][a-z0-9-]*", repository):
            raise ValueError(f"Unapproved runtime publisher: {repository!r}")
        exports = source["exports"]
        if not isinstance(exports, list) or not exports or len(set(exports)) != len(exports):
            raise ValueError(f"Runtime exports must be nonempty and unique: {name}")
        for export in exports:
            if not relative(export).startswith(".agents/"):
                raise ValueError(f"Runtime export must belong to .agents: {export}")
    return sources


def export_contents(source: Path, exports: list[str]) -> dict[str, bytes]:
    result = {}
    for export in exports:
        target = safe_path(source, export)
        if not target.exists():
            raise ValueError(f"Missing runtime export: {target}")
        entries = files(target) if target.is_dir() else {"": target.read_bytes()}
        for suffix, body in entries.items():
            name = export + ("/" + suffix if suffix else "")
            if name in result:
                raise ValueError(f"Overlapping runtime export: {name}")
            result[name] = body
    return result


def git(*arguments: str) -> str:
    result = subprocess.run(["git", *arguments], stdin=subprocess.DEVNULL, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Runtime source Git command failed")
    return result.stdout.strip()


def stage(root: Path, overrides: dict[str, Path], check: bool = False) -> list[dict]:
    sources = declarations(root)
    if set(overrides) - set(sources):
        raise ValueError("Undeclared runtime source override")
    results = []
    for name, source in sources.items():
        destination = safe_path(root, ".agents/dependencies/" + name)
        receipt_path = destination / "source.json"
        if check:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            contents = export_contents(destination, source["exports"])
            if (receipt.get("repository") != source["repository"]
                    or receipt.get("exports") != source["exports"]
                    or receipt.get("sha256") != digest(contents)):
                raise ValueError(f"Stale or modified staged runtime: {name}; run scripts/runtime_sources.py")
            results.append({"name": name, "status": "verified", "revision": receipt["revision"]})
            continue
        with tempfile.TemporaryDirectory(prefix="tj-runtime-") as temporary:
            if name in overrides:
                checkout = overrides[name].resolve()
                revision = "local:" + digest(export_contents(checkout, source["exports"]))
            else:
                checkout = Path(temporary) / "source"
                git("clone", "--quiet", "--depth", "1", "--branch", "main",
                    f"https://github.com/{source['repository']}.git", str(checkout))
                revision = git("-C", str(checkout), "rev-parse", "HEAD")
            contents = export_contents(checkout, source["exports"])
            receipt = {"repository": source["repository"], "revision": revision,
                       "exports": source["exports"], "sha256": digest(contents)}
            destination.mkdir(parents=True, exist_ok=True)
            previous = files(destination)
            expected = {**contents, "source.json": (json.dumps(receipt, indent=2) + "\n").encode("utf-8")}
            for path, body in expected.items():
                output = safe_path(destination, path)
                output.parent.mkdir(parents=True, exist_ok=True)
                if previous.get(path) != body:
                    output.write_bytes(body)
            for path in set(previous) - set(expected):
                (destination / path).unlink()
            results.append({"name": name, "status": "staged", "revision": revision})
    return results


def ensure(root: Path) -> list[dict]:
    sources = declarations(root)
    present = all((root / ".agents/dependencies" / name / "source.json").is_file() for name in sources)
    return stage(root, {}, check=present)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source", action="append", default=[], metavar="NAME=CHECKOUT",
                        help="Explicit local build input; never used by installed runtime")
    parser.add_argument("--check", action="store_true", help="Verify staged bytes offline without writing")
    args = parser.parse_args()
    try:
        overrides = {}
        for value in args.source:
            name, separator, path = value.partition("=")
            if not separator or not name or not path or name in overrides:
                raise ValueError("Each --source must be a unique NAME=CHECKOUT")
            overrides[name] = Path(path)
        print(json.dumps({"sources": stage(args.root.resolve(), overrides, args.check)}, separators=(",", ":")))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
