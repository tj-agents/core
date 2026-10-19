#!/usr/bin/env python3
"""Set this machine up for automatic plugin updates; safe to run again at any time (Python 3.11+)."""

from __future__ import annotations

import argparse
import codecs
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape

import plugin_autoupdate

TASK_NAME = "tj-agents plugin autoupdate"
CRON_MARKER = "# tj-agents-plugin-autoupdate"
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


def install_script(source: Path, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / plugin_autoupdate.SCRIPT_NAME
    shutil.copyfile(source, target)
    return target


def windowless_python() -> str:
    candidate = Path(sys.executable).with_name("pythonw.exe")
    return str(candidate) if candidate.is_file() else sys.executable


def windows_task_xml(user: str, python: str, script: Path) -> str:
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger><Enabled>true</Enabled><UserId>{escape(user)}</UserId></LogonTrigger>
    <TimeTrigger>
      <Repetition><Interval>PT1H</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>
      <StartBoundary>2026-01-01T00:00:00</StartBoundary><Enabled>true</Enabled>
    </TimeTrigger>
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
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>{escape(python)}</Command><Arguments>-B "{escape(str(script))}"</Arguments></Exec>
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


def cron_lines(python: str, script: Path) -> list[str]:
    command = f'"{python}" -B "{script}"'
    return [f"@reboot {command} {CRON_MARKER}", f"17 * * * * {command} {CRON_MARKER}"]


def schedule_cron(script: Path, run=subprocess.run) -> None:
    current = run(["crontab", "-l"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                  timeout=COMMAND_TIMEOUT_SECONDS, check=False)
    lines = [line for line in (current.stdout if current.returncode == 0 else "").splitlines()
             if CRON_MARKER not in line]
    lines.extend(cron_lines(sys.executable, script))
    run(["crontab", "-"], input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=COMMAND_TIMEOUT_SECONDS, check=True)


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print("setup_machine requires Python 3.11 or newer", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-schedule", action="store_true")
    arguments = parser.parse_args(argv)
    home = Path.home()
    for name in enable_claude_autoupdate(plugin_autoupdate.claude_home()):
        print(f"Claude marketplace now auto-updates: {name}")
    for path in remove_retired_launchers(profile_paths(home)):
        print(f"Removed the retired launcher from {path}")
    script = install_script(Path(__file__).with_name(plugin_autoupdate.SCRIPT_NAME),
                            plugin_autoupdate.state_directory() / "bin")
    if not arguments.no_schedule:
        if os.name == "nt":
            schedule_windows(script)
            print(f"Scheduled '{TASK_NAME}' at logon and hourly")
        else:
            schedule_cron(script)
            print("Scheduled the plugin refresh at boot and hourly in crontab")
    plugin_autoupdate.main(["--no-self-update"])
    print("Plugins are up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
