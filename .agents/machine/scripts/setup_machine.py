#!/usr/bin/env python3
"""Configure the machine event channel and the claude/codex launch check (Python 3.11+)."""

from __future__ import annotations

import argparse
import codecs
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

import launch_check
import plugin_autoupdate
import machine_events

RETIRED_TASKS = ("tj-agents plugin autoupdate", "tj-agents merge gates", "tj-agents machine events")
RETIRED_CRON_MARKERS = ("# tj-agents-plugin-autoupdate", "# tj-agents-merge-gates")
RETIRED_SERVICE = "tj-agents-machine-events.service"
COMMAND_TIMEOUT_SECONDS = 60
LAUNCH_START = "# >>> tj-agents launch check >>>"
LAUNCH_END = "# <<< tj-agents launch check <<<"
HOSTS = ("claude", "codex")
RETIRED_BLOCKS = (
    ("# >>> base-agents claude launcher >>>", "# <<< base-agents claude launcher <<<"),
    ("# >>> base-agents codex launcher >>>", "# <<< base-agents codex launcher <<<"),
    ("# >>> core codex no-daemon >>>", "# <<< core codex no-daemon <<<"),
)


def enable_claude_autoupdate(config: Path) -> list[str]:
    settings = plugin_autoupdate.read_json(config / "settings.json")
    enabled = settings.get("enabledPlugins")
    if not isinstance(enabled, dict):
        return []
    wanted = {identity.rsplit("@", 1)[1] for identity, on in enabled.items() if on is True and "@" in identity}
    path = config / "plugins" / "known_marketplaces.json"
    known = plugin_autoupdate.read_json(path)
    changed = sorted(name for name in wanted
                     if isinstance(known.get(name), dict) and known[name].get("autoUpdate") is not True)
    for name in changed:
        known[name]["autoUpdate"] = True
    if changed:
        plugin_autoupdate.write_json(path, known)
    return changed


def profile_paths(home: Path) -> list[Path]:
    if os.name == "nt":
        documents = Path(os.environ.get("USERPROFILE") or home) / "Documents"
        return [documents / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
                documents / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"]
    return [home / ".bashrc", home / ".zshrc", home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1"]


def powershell_block(python: str, script: Path, newline: str) -> str:
    def quoted(value: object) -> str:
        return "'" + str(value).replace("'", "''") + "'"

    lines = [LAUNCH_START]
    for name in HOSTS:
        lines += [
            f"function global:{name} {{",
            f"    $tjAgentsTarget = Get-Command {name} -CommandType Application, ExternalScript"
            " -ErrorAction SilentlyContinue | Select-Object -First 1",
            f"    if (-not $tjAgentsTarget) {{ Write-Error '{name} was not found on PATH'; return }}",
            f"    if (Test-Path -LiteralPath {quoted(python)}) {{ & {quoted(python)} -I -B {quoted(script)} }}",
            "    & $tjAgentsTarget.Source @args",
            "}",
        ]
    return newline.join([*lines, LAUNCH_END])


def posix_block(python: str, script: Path) -> str:
    def quoted(value: object) -> str:
        return "'" + str(value).replace("'", "'\\''") + "'"

    return "\n".join([LAUNCH_START, *(
        f'{name}() {{ [ -x {quoted(python)} ] && {quoted(python)} -I -B {quoted(script)}; command {name} "$@"; }}'
        for name in HOSTS), LAUNCH_END])


def without_retired_blocks(text: str) -> str:
    for start, end in RETIRED_BLOCKS:
        while start in text and end in text[text.index(start):]:
            begin = text.index(start)
            finish = text.index(end, begin) + len(end)
            if text[finish:finish + 2] == "\r\n":
                finish += 2
            elif text[finish:finish + 1] == "\n":
                finish += 1
            text = text[:begin] + text[finish:]
    return text


def with_launch_block(text: str, block: str) -> str:
    text = without_retired_blocks(text)
    if LAUNCH_START in text and LAUNCH_END in text[text.index(LAUNCH_START):]:
        begin = text.index(LAUNCH_START)
        return text[:begin] + block + text[text.index(LAUNCH_END, begin) + len(LAUNCH_END):]
    newline = "\r\n" if "\r\n" in block else "\n"
    return text + (newline if text and not text.endswith("\n") else "") + block + newline


def install_launchers(paths: list[Path], python: str, script: Path) -> list[Path]:
    changed = []
    for path in [path for path in paths if path.is_file()] or paths[:1]:
        try:
            raw = path.read_bytes() if path.is_file() else b""
        except OSError:
            continue
        encoding = "utf-8-sig" if raw.startswith(codecs.BOM_UTF8) else "utf-8"
        try:
            text = raw.decode(encoding)
        except UnicodeError:
            continue
        if path.suffix.casefold() == ".ps1":
            windows = "\r\n" in text or (not text and os.name == "nt")
            block = powershell_block(python, script, "\r\n" if windows else "\n")
        else:
            block = posix_block(python, script)
        updated = with_launch_block(text, block)
        if updated == text:
            continue
        if raw:
            shutil.copyfile(path, path.with_name(path.name + ".pre-launch-check.bak"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(updated.encode(encoding))
        changed.append(path)
    return changed


def remove_retired_cron(run=subprocess.run) -> None:
    try:
        current = run(["crontab", "-l"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                      timeout=COMMAND_TIMEOUT_SECONDS, check=False)
    except FileNotFoundError:
        return
    if current.returncode and "no crontab" not in current.stderr.lower():
        raise RuntimeError("Cannot inspect crontab: " + current.stderr)
    original = (current.stdout if current.returncode == 0 else "").splitlines()
    lines = [line for line in original if not any(marker in line for marker in RETIRED_CRON_MARKERS)]
    if lines == original:
        return
    run(["crontab", "-"], input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=COMMAND_TIMEOUT_SECONDS, check=True)


def remove_retired_windows(run=subprocess.run) -> None:
    for name in RETIRED_TASKS:
        existing = run(["schtasks.exe", "/query", "/tn", name], capture_output=True, text=True,
                       timeout=COMMAND_TIMEOUT_SECONDS, check=False, creationflags=plugin_autoupdate.NO_WINDOW)
        if existing.returncode == 0:
            run(["schtasks.exe", "/end", "/tn", name], capture_output=True, text=True,
                timeout=COMMAND_TIMEOUT_SECONDS, check=False, creationflags=plugin_autoupdate.NO_WINDOW)
            run(["schtasks.exe", "/delete", "/tn", name, "/f"], capture_output=True, text=True,
                timeout=COMMAND_TIMEOUT_SECONDS, check=True, creationflags=plugin_autoupdate.NO_WINDOW)


def systemctl(arguments: list[str], run=subprocess.run) -> None:
    try:
        run(["systemctl", "--user", *arguments], capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=COMMAND_TIMEOUT_SECONDS, check=False)
    except FileNotFoundError:
        pass


def remove_retired_service(home: Path, run=subprocess.run) -> bool:
    unit = home / ".config" / "systemd" / "user" / RETIRED_SERVICE
    if not unit.exists():
        return False
    systemctl(["disable", "--now", RETIRED_SERVICE], run)
    unit.unlink()
    systemctl(["daemon-reload"], run)
    return True


def configure_topic(directory: Path, api=machine_events.gh) -> str:
    endpoint = "repos/tj-agents/core/actions/variables"
    values = api([endpoint + "?per_page=100"])
    remote = next((item["value"] for item in values["variables"]
                   if item["name"] == machine_events.TOPIC_VARIABLE), None)
    saved = plugin_autoupdate.read_json(directory / "machine-events.json").get("topic")
    topic = machine_events.topic_value(remote or saved or secrets.token_hex(24))
    if not remote:
        api(["--method", "POST", endpoint, "--input", "-"],
            {"name": machine_events.TOPIC_VARIABLE, "value": topic})
    plugin_autoupdate.write_json(directory / "machine-events.json", {"topic": topic})
    return topic


def set_topic_secret(repository: str, topic: str) -> None:
    machine_events.github_cli(["secret", "set", machine_events.TOPIC_VARIABLE, "--repo", repository], input=topic)


def configure_publishers(topic: str, repositories, api=machine_events.gh, secret=set_topic_secret) -> int:
    changed = 0
    for repository in repositories:
        if repository.get("isArchived") or repository.get("isFork"):
            continue
        name = repository["nameWithOwner"]
        if not machine_events.valid_repository(name):
            raise ValueError("Unsupported publisher repository")
        endpoint = f"repos/{name}/actions/variables"
        values = api([endpoint + "?per_page=100"])
        existing = next((item for item in values["variables"]
                         if item["name"] == machine_events.TOPIC_VARIABLE), None)
        different = existing is None or existing["value"] != topic
        secrets = api([f"repos/{name}/actions/secrets?per_page=100"])
        saved = next((item for item in secrets["secrets"]
                      if item["name"] == machine_events.TOPIC_VARIABLE), None)
        stale = bool(existing and saved and existing.get("updated_at", "") > saved.get("updated_at", ""))
        if different:
            if existing:
                endpoint += "/" + machine_events.TOPIC_VARIABLE
            api(["--method", "PATCH" if existing else "POST", endpoint, "--input", "-"],
                {"name": machine_events.TOPIC_VARIABLE, "value": topic})
        if different or saved is None or stale:
            secret(name, topic)
            changed += 1
    return changed


def install_runtime(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name in plugin_autoupdate.RUNTIME:
        target = directory / name
        temporary = target.with_suffix(".next")
        shutil.copyfile(Path(__file__).with_name(name), temporary)
        os.replace(temporary, target)
    return directory / "launch_check.py"


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print("setup_machine requires Python 3.11 or newer", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    home = Path.home()
    machine_events.require_tommy()
    directory = plugin_autoupdate.state_directory()
    topic = configure_topic(directory)
    repositories = list(machine_events.catch_up_states())
    configured = configure_publishers(topic, repositories)
    print(f"Channel configured for {configured} repository publishers")
    for name in enable_claude_autoupdate(plugin_autoupdate.claude_home()):
        print(f"Claude marketplace now auto-updates: {name}")
    if os.name == "nt":
        remove_retired_windows()
    else:
        remove_retired_cron()
        remove_retired_service(home)
    script = install_runtime(directory / "bin")
    for path in install_launchers(profile_paths(home), plugin_autoupdate.console_python(), script):
        print(f"claude and codex now check for published plugin updates before starting: {path}")
    try:
        launch_check.mark_current()
    except (OSError, ValueError) as error:
        print(f"Event channel unreachable ({type(error).__name__}); the first launch replays recent events")
    if machine_events.main([]):
        print("Catch-up left failures; see machine-events.log")
        return 1
    print("Plugins and merge policies are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
