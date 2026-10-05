import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def git(checkout, *arguments):
    return subprocess.run(["git", "-C", str(checkout), *arguments], check=True, capture_output=True, text=True).stdout.strip()


def plugin_source(checkout, name):
    manifest_path = checkout / ".claude-plugin" / "marketplace.json"
    if not manifest_path.is_file():
        return None, None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("plugins", []):
        if entry.get("name") == name:
            source = entry.get("source")
            if isinstance(source, dict) and source.get("url"):
                return source["url"], source.get("ref")
    return None, None


def main(arguments):
    config = Path(os.environ["CLAUDE_CONFIG_DIR"])
    plugins = config / "plugins"
    entry = {"argv": arguments, "cwd": os.getcwd()}
    lock = os.environ.get("FAKE_CLAUDE_AGE_LOCK")
    if lock:
        entry["lock_age"] = time.time() - os.stat(lock).st_mtime
        aged = time.time() - 10_000
        os.utime(lock, (aged, aged))
    with open(os.environ["FAKE_CLAUDE_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps(entry) + "\n")
    if arguments[:3] == ["plugin", "marketplace", "update"]:
        known = json.loads((plugins / "known_marketplaces.json").read_text(encoding="utf-8"))
        if os.environ.get("FAKE_CLAUDE_FAIL") == arguments[3]:
            print("Failed to refresh marketplace", file=sys.stderr)
            return 1
        git(known[arguments[3]]["installLocation"], "pull", "--ff-only", "--quiet")
        print(f"Successfully updated marketplace: {arguments[3]}")
        return 0
    if arguments[:2] == ["plugin", "update"]:
        identity, scope = arguments[2], arguments[arguments.index("--scope") + 1]
        if os.environ.get("FAKE_CLAUDE_FAIL") == identity:
            print(json.dumps({"command": "update", "outcome": "failed", "message": "command needs acceptance"}))
            return 1
        name, marketplace = identity.split("@")
        known = json.loads((plugins / "known_marketplaces.json").read_text(encoding="utf-8"))
        checkout = Path(known[marketplace]["installLocation"])
        url, ref = plugin_source(checkout, name)
        with tempfile.TemporaryDirectory() as scratch:
            if url:
                subprocess.run(["git", "clone", "--quiet", url, scratch], check=True, capture_output=True, text=True)
                if ref:
                    git(scratch, "checkout", "--quiet", ref)
                content_root = Path(scratch)
            else:
                content_root = checkout
            version = git(content_root, "rev-parse", "HEAD")[:12]
            registry_path = plugins / "installed_plugins.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            for record in registry["plugins"][identity]:
                if record["scope"] != scope:
                    continue
                if scope in ("project", "local") and os.path.normcase(record["projectPath"]) != os.path.normcase(os.getcwd()):
                    continue
                if record["version"] == version:
                    print(json.dumps({"command": "update", "outcome": "ok", "message": "already at the latest version"}))
                    return 0
                target = plugins / "cache" / marketplace / name / version
                plugin_dir = content_root / "plugins" / name
                if plugin_dir.is_dir():
                    shutil.copytree(plugin_dir, target, dirs_exist_ok=True)
                else:
                    target.mkdir(parents=True, exist_ok=True)
                (Path(record["installPath"]) / ".orphaned_at").write_text(str(int(time.time() * 1000)), encoding="utf-8")
                record.update(version=version, installPath=str(target))
            registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        print(json.dumps({"command": "update", "outcome": "ok", "message": f"updated to {version}"}))
        return 0
    print(f"unexpected invocation: {arguments}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
