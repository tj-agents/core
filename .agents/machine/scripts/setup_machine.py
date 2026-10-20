#!/usr/bin/env python3
"""Install the supervised machine event listener (Python 3.11+)."""

from __future__ import annotations

import argparse
import codecs
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

import plugin_autoupdate
import machine_events

TASK_NAME = machine_events.SERVICE_NAME
RETIRED_TASKS = ("tj-agents plugin autoupdate", "tj-agents merge gates")
RETIRED_CRON_MARKERS = ("# tj-agents-plugin-autoupdate", "# tj-agents-merge-gates")
COMMAND_TIMEOUT_SECONDS = 60
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
    return [home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1", home / ".bashrc"]


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


def remove_retired_launchers(paths: list[Path]) -> list[Path]:
    cleaned = []
    for path in paths:
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        encoding = "utf-8-sig" if raw.startswith(codecs.BOM_UTF8) else "utf-8"
        try:
            text = raw.decode(encoding)
        except UnicodeError:
            continue
        updated = without_retired_blocks(text)
        if updated == text:
            continue
        shutil.copyfile(path, path.with_name(path.name + ".pre-autoupdate.bak"))
        path.write_bytes(updated.encode(encoding))
        cleaned.append(path)
    return cleaned


def windowless_python() -> str:
    candidate = Path(sys.executable).with_name("pythonw.exe")
    if candidate.is_file():
        return str(candidate)
    raise RuntimeError(f"pythonw.exe is required beside {sys.executable} for the hidden listener")


def windows_task_xml(user: str, python: str, script: Path) -> str:
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger><Enabled>true</Enabled><UserId>{escape(user)}</UserId></LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author"><UserId>{escape(user)}</UserId><LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel></Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RestartOnFailure><Interval>PT1M</Interval><Count>999</Count></RestartOnFailure>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>{escape(python)}</Command><Arguments>-B "{escape(str(script))}" --state-directory "{escape(str(script.parent.parent))}"</Arguments></Exec>
  </Actions>
</Task>
"""


def schedule_windows(script: Path, run=subprocess.run) -> None:
    user = run(["whoami"], capture_output=True, text=True, encoding="utf-8", errors="replace",
               timeout=COMMAND_TIMEOUT_SECONDS, check=True).stdout.strip()
    descriptor, path = tempfile.mkstemp(suffix=".xml")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-16") as stream:
            stream.write(windows_task_xml(user, windowless_python(), script))
        run(["schtasks.exe", "/create", "/tn", TASK_NAME, "/xml", path, "/f"], capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=COMMAND_TIMEOUT_SECONDS, check=True)
    finally:
        Path(path).unlink(missing_ok=True)


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


def systemd_unit(python: str, script: Path) -> str:
    def quoted(value):
        return '"' + str(value).replace("%", "%%").replace("\\", "\\\\").replace('"', '\\"') + '"'

    return ("[Unit]\nDescription=tj-agents machine events\nAfter=network.target\n\n[Service]\n"
            f"ExecStart={quoted(python)} -B {quoted(script)} --state-directory {quoted(script.parent.parent)}\nRestart=always\nRestartSec=5\n"
            "\n[Install]\nWantedBy=default.target\n")


def schedule_systemd(script: Path, home: Path, run=subprocess.run) -> None:
    unit = home / ".config/systemd/user/tj-agents-machine-events.service"
    unit.parent.mkdir(parents=True, exist_ok=True)
    unit.write_text(systemd_unit(sys.executable, script), encoding="utf-8", newline="\n")
    for command in (["systemctl", "--user", "daemon-reload"],
                    ["systemctl", "--user", "enable", "tj-agents-machine-events.service"],
                    ["systemctl", "--user", "restart", "tj-agents-machine-events.service"]):
        run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS, check=True)


def remove_retired_windows(run=subprocess.run) -> None:
    for name in RETIRED_TASKS:
        existing = run(["schtasks.exe", "/query", "/tn", name], capture_output=True, text=True,
                       timeout=COMMAND_TIMEOUT_SECONDS, check=False, creationflags=plugin_autoupdate.NO_WINDOW)
        if existing.returncode == 0:
            run(["schtasks.exe", "/end", "/tn", name], capture_output=True, text=True,
                timeout=COMMAND_TIMEOUT_SECONDS, check=False, creationflags=plugin_autoupdate.NO_WINDOW)
            run(["schtasks.exe", "/delete", "/tn", name, "/f"], capture_output=True, text=True,
                timeout=COMMAND_TIMEOUT_SECONDS, check=True, creationflags=plugin_autoupdate.NO_WINDOW)


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


def install_listener(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("plugin_autoupdate.py", "machine_events.py"):
        target = directory / name
        temporary = target.with_suffix(".next")
        shutil.copyfile(Path(__file__).with_name(name), temporary)
        os.replace(temporary, target)
    return directory / "machine_events.py"


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
    for path in remove_retired_launchers(profile_paths(home)):
        print(f"Removed the retired launcher from {path}")
    script = install_listener(directory / "bin")
    if os.name == "nt":
        schedule_windows(script)
        remove_retired_windows()
        subprocess.run(["schtasks.exe", "/end", "/tn", TASK_NAME], capture_output=True,
                       timeout=COMMAND_TIMEOUT_SECONDS, check=False, creationflags=plugin_autoupdate.NO_WINDOW)
        subprocess.run(["schtasks.exe", "/run", "/tn", TASK_NAME], capture_output=True,
                       timeout=COMMAND_TIMEOUT_SECONDS, check=True, creationflags=plugin_autoupdate.NO_WINDOW)
    else:
        remove_retired_cron()
        schedule_systemd(script, home)
    print("Machine event listener installed and started; it catches up on startup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
