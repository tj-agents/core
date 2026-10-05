from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tarfile
import threading
import time


GITHUB_SOURCE = re.compile(
    r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)?"
    r"(?P<owner>[A-Za-z0-9-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
TRUSTED_OWNER = "tj-agents"
TIMEOUT = 45


def github_repository(source):
    match = GITHUB_SOURCE.fullmatch(source) if isinstance(source, str) else None
    if not match or match["repo"] in {".", ".."}:
        return None
    return match["owner"].casefold(), match["repo"].casefold()


def command(executable):
    if Path(executable).suffix.casefold() == ".ps1":
        shell = shutil.which("pwsh") or shutil.which("powershell.exe")
        if not shell:
            raise RuntimeError("PowerShell is required to run the Codex shim")
        return [shell, "-NoProfile", "-File", executable]
    return [executable]


def run(arguments, cwd):
    return subprocess.run(
        arguments, cwd=cwd, check=True, capture_output=True,
        text=True, encoding="utf-8", timeout=TIMEOUT,
    ).stdout.strip()


class AppServer:
    def __init__(self, executable, cwd):
        self.process = subprocess.Popen(
            [*command(executable), "app-server"], cwd=cwd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self.messages = queue.Queue()
        self.sequence = 0
        threading.Thread(target=self.read, daemon=True).start()

    def read(self):
        try:
            for line in self.process.stdout:
                self.messages.put(json.loads(line))
        except (OSError, ValueError) as error:
            self.messages.put(error)
        finally:
            self.messages.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + TIMEOUT
        while True:
            try:
                message = self.messages.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as error:
                raise RuntimeError(f"Codex {method} timed out") from error
            if message is None or isinstance(message, Exception):
                raise RuntimeError(f"Codex app server stopped during {method}")
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(f"Codex {method} failed: {message['error']}")
            return message["result"]

    def __enter__(self):
        try:
            self.request("initialize", {
                "clientInfo": {"name": "tj_agents_hook_trust", "version": "1.0.0"},
                "capabilities": {"experimentalApi": True},
            })
            self.send({"method": "initialized"})
            return self
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()

    def __exit__(self, *_):
        self.close()


def source_package(plugin, cwd, published=None):
    marketplace = plugin.get("marketplaceSource", {})
    repository = github_repository(marketplace.get("source"))
    if marketplace.get("sourceType") != "git" or not repository or repository[0] != TRUSTED_OWNER:
        return None
    source = plugin.get("source", {})
    if source.get("source") != "local" or not source.get("path"):
        return None
    path = Path(source["path"]).resolve(strict=True)
    root = Path(run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], cwd)).resolve()
    origin = run(["git", "-C", str(root), "remote", "get-url", "origin"], cwd)
    if github_repository(origin) != repository:
        raise RuntimeError(f"Plugin source origin differs from its marketplace: {plugin['pluginId']}")
    published = {} if published is None else published
    if root not in published:
        head = run(["git", "-C", str(root), "rev-parse", "HEAD"], cwd)
        remote = run([
            "git", "-C", str(root), "ls-remote", f"https://github.com/{repository[0]}/{repository[1]}.git",
            "HEAD", "refs/heads/*", "refs/tags/*",
        ], cwd)
        if head not in {line.split()[0] for line in remote.splitlines() if line.split()}:
            raise RuntimeError(f"Plugin source revision is not published by tj-agents: {plugin['pluginId']}")
        published[root] = head
    relative = path.relative_to(root).as_posix()
    changes = run([
        "git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "--", relative,
    ], cwd)
    if changes:
        raise RuntimeError(f"Plugin source has local changes: {plugin['pluginId']}")
    return committed_files(root, published[root], relative, cwd)


def normalized_bytes(content):
    try:
        return content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    except UnicodeDecodeError:
        return content


def committed_files(root, revision, relative, cwd):
    tree = revision if relative == "." else f"{revision}:{relative}"
    archive = subprocess.run(
        ["git", "-C", str(root), "archive", "--format=tar", tree],
        cwd=cwd, check=True, capture_output=True, timeout=TIMEOUT,
    ).stdout
    result = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tree:
        for entry in tree:
            if entry.isdir():
                continue
            if not entry.isfile() or Path(entry.name).is_absolute() or ".." in Path(entry.name).parts:
                raise RuntimeError("Published plugin package contains an unsupported entry")
            result[entry.name] = normalized_bytes(tree.extractfile(entry).read())
    return result


def package_files(root):
    result = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"Plugin package contains a symbolic link: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = normalized_bytes(path.read_bytes())
    return result


def installed_package(hook):
    path = Path(hook["sourcePath"]).resolve(strict=True)
    for parent in path.parents:
        if (parent / ".codex-plugin/plugin.json").is_file() or (parent / "plugin.json").is_file():
            return parent
    raise RuntimeError(f"Cannot identify installed plugin package: {hook['pluginId']}")


def trust_updates(inventory, entries, cwd):
    candidates = {}
    for plugin in inventory.get("installed", []):
        if plugin.get("installed") and plugin.get("enabled"):
            marketplace = plugin.get("marketplaceSource", {})
            repository = github_repository(marketplace.get("source"))
            if marketplace.get("sourceType") == "git" and repository and repository[0] == TRUSTED_OWNER:
                candidates[plugin["pluginId"]] = plugin
    updates = {}
    verified = set()
    published = {}
    for entry in entries:
        if Path(entry["cwd"]).resolve() != cwd:
            continue
        if entry.get("errors"):
            raise RuntimeError("Codex could not load all hook definitions")
        for hook in entry.get("hooks", []):
            identity = hook.get("pluginId")
            if (
                identity not in candidates or hook.get("source") != "plugin"
                or hook.get("isManaged") or not hook.get("enabled")
                or hook.get("trustStatus") not in {"untrusted", "modified"}
            ):
                continue
            package = installed_package(hook)
            if (identity, package) not in verified:
                source = source_package(candidates[identity], cwd, published)
                if source is None:
                    continue
                if package_files(package) != source:
                    raise RuntimeError(f"Installed plugin differs from its Git source: {identity}")
                verified.add((identity, package))
            key, current_hash = hook["key"], hook["currentHash"]
            if not key.startswith(identity + ":") or not re.fullmatch(r"sha256:[0-9a-f]{64}", current_hash):
                raise RuntimeError(f"Invalid native hook identity: {identity}")
            updates[key] = {"trusted_hash": current_hash}
    return updates


def apply_trust(executable, cwd, preview=False):
    with AppServer(executable, cwd) as server:
        listing = server.request("hooks/list", {"cwds": [str(cwd)]})
        if not any(
            hook.get("source") == "plugin" and hook.get("enabled")
            and hook.get("trustStatus") in {"untrusted", "modified"}
            for entry in listing["data"] for hook in entry.get("hooks", [])
        ):
            return {}
        inventory = json.loads(run([*command(executable), "plugin", "list", "--json"], cwd))
        updates = trust_updates(inventory, listing["data"], cwd)
        if updates and not preview:
            server.request("config/batchWrite", {
                "edits": [{"keyPath": "hooks.state", "value": updates, "mergeStrategy": "upsert"}],
                "reloadUserConfig": True,
            })
        return updates


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex", required=True)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--preview", action="store_true")
    arguments = parser.parse_args(argv)
    if os.environ.get("BASE_AGENTS_CODEX_HOOK_TRUST", "").casefold() == "off":
        return 0
    try:
        updates = apply_trust(arguments.codex, arguments.project.resolve(strict=True), arguments.preview)
        if updates:
            action = "Would trust" if arguments.preview else "Trusted"
            print(f"standards: {action} {len(updates)} tj-agents hook definitions")
        return 0
    except (OSError, ValueError, RuntimeError, tarfile.TarError, subprocess.SubprocessError) as error:
        print(f"standards: tj-agents hook trust failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
