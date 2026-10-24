"""Receipt-owned scheduler primitives for persistent continuation (Python 3.9+)."""

import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

TASK_PREFIX = "AgentStandards-Continuation-"
PROFILE_VARIABLES = ("CODEX_HOME", "CLAUDE_CONFIG_DIR", "GH_CONFIG_DIR", "PATH", "TJ_AGENT")
CONTROL_VARIABLES = ("CONTINUATION_OWNER_ID", "CONTINUATION_NONCE", "CONTINUATION_RESULT_PATH")
WINDOWS_READ_QUERY_TIMEOUT = 15


class SchedulerError(RuntimeError):
    pass


def exact_path(value):
    return str(Path(value).resolve()) if isinstance(value, str) and value else None


def reject_unsafe(value, label="path"):
    if not isinstance(value, str) or not value or "\x00" in value or "\n" in value or "\r" in value:
        raise SchedulerError("unsafe " + label)
    return value


def owner_task_name(owner_id):
    return TASK_PREFIX + hashlib.sha256(owner_id.encode("utf-8")).hexdigest()


def owner_unit_name(owner_id):
    return "agent-standards-continuation-" + hashlib.sha256(owner_id.encode("utf-8")).hexdigest()


def unit_directory(environment=None):
    environment = environment or os.environ
    base = environment.get("XDG_CONFIG_HOME")
    if base:
        if not Path(base).is_absolute():
            raise SchedulerError("XDG_CONFIG_HOME must be an absolute path")
        return Path(base) / "systemd" / "user"
    return Path.home() / ".config" / "systemd" / "user"


def systemd_quote(value):
    reject_unsafe(value)
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%").replace("$", "$$") + '"'


def systemd_environment_quote(value):
    reject_unsafe(value)
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%") + '"'


def unit_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_text(path, text):
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + next(tempfile._get_candidate_names()) + ".tmp")
    try:
        _write_text(temporary, json.dumps(value, sort_keys=True, indent=2) + "\n")
        os.replace(str(temporary), str(path))
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def atomic_text(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + next(tempfile._get_candidate_names()) + ".tmp")
    try:
        _write_text(temporary, value)
        os.replace(str(temporary), str(path))
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def lifecycle_lock(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "scheduler.lock"
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt
            if os.fstat(stream.fileno()).st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                yield False
                return
        else:
            import fcntl
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
        try:
            yield True
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


class SchedulerTransport:
    def run(self, args, *, input_text=None, timeout=15, environment=None):
        return subprocess.run(args, input=input_text, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              env=environment, check=False)

    def write(self, path, text):
        atomic_text(path, text)

    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

    def remove(self, path):
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass


def _result(transport, args, **kwargs):
    try:
        result = transport.run(args, **kwargs)
    except (OSError, subprocess.SubprocessError) as error:
        raise SchedulerError("scheduler command unavailable: " + args[0]) from error
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        raise SchedulerError("scheduler command failed: " + " ".join(args[:3]) + ((": " + detail) if detail else ""))
    return result


def systemd_available(transport):
    _result(transport, ["systemctl", "--user", "show-environment"], timeout=10)


def _profile_environment(environment):
    return {name: reject_unsafe(environment[name], name) for name in PROFILE_VARIABLES if environment.get(name)}


def runtime_command(receipt):
    return [receipt["python"], "-I", "-B", receipt["helper"], "wake", "--owner",
            receipt["owner_path"], "--host-command", receipt["host_executable"]]


def adapter_command(receipt):
    return [receipt["python"], "-I", "-B", receipt["script"], "wake", "--owner", receipt["owner_path"],
            "--host-executable", receipt["host_executable"]]


def linux_units(receipt):
    service = ["[Unit]", "Description=" + receipt["description"], "", "[Service]", "Type=oneshot",
               "TimeoutStartSec=7200", "WorkingDirectory=" + reject_unsafe(receipt["worktree"]).replace("%", "%%")]
    service.extend("Environment=" + systemd_environment_quote(key + "=" + value)
                   for key, value in receipt.get("profile_environment", {}).items())
    service.extend(["ExecStart=" + " ".join(systemd_quote(value) for value in receipt["adapter_command"]), ""])
    timer = ["[Unit]", "Description=" + receipt["description"] + " timer", "", "[Timer]",
             "OnActiveSec=" + str(receipt["interval_minutes"]) + "min",
             "OnUnitInactiveSec=" + str(receipt["interval_minutes"]) + "min",
             "Unit=" + receipt["service_unit"], "", "[Install]", "WantedBy=timers.target", ""]
    return "\n".join(service), "\n".join(timer)


def linux_receipt(owner, owner_path, adapter_path, runtime_path, python_path, host_path, interval, environment=None):
    owner_id = reject_unsafe(owner.get("owner_id"), "owner id")
    directory = unit_directory(environment)
    name = owner_unit_name(owner_id)
    receipt = {"version": 3, "platform": "linux-systemd", "owner_id": owner_id,
               "owner_path": str(Path(owner_path).resolve()), "worktree": str(Path(owner["worktree"]).resolve()),
               "harness": owner["harness"], "interval_minutes": interval,
               "description": "Continuation owner " + owner_id,
               "service_unit": name + ".service", "timer_unit": name + ".timer",
               "unit_directory": str(directory.resolve()),
               "service_path": str(directory.resolve() / (name + ".service")),
               "timer_path": str(directory.resolve() / (name + ".timer")),
               "timer_enable_path": str(directory.resolve() / "timers.target.wants" / (name + ".timer")),
               "helper": str(Path(runtime_path).resolve()), "python": str(Path(python_path).resolve()),
               "script": str(Path(adapter_path).resolve()), "host_executable": str(Path(host_path).resolve()),
               "profile_environment": _profile_environment(environment or os.environ)}
    receipt["adapter_command"] = adapter_command(receipt)
    receipt["runtime_command"] = runtime_command(receipt)
    service, timer = linux_units(receipt)
    receipt["service_sha256"] = unit_hash(service)
    receipt["timer_sha256"] = unit_hash(timer)
    return receipt


def _powershell():
    return os.environ.get("SystemRoot", r"C:\\Windows") + r"\System32\WindowsPowerShell\v1.0\powershell.exe"


WINDOWS_SCRIPT = r'''$ErrorActionPreference='Stop';[Console]::InputEncoding=[Text.UTF8Encoding]::new($false);[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);$payload=[Console]::In.ReadToEnd()|ConvertFrom-Json
if($payload.operation -eq 'query'){$tasks=@(Get-ScheduledTask|Where-Object {$_.TaskName -ieq $payload.task_name -and $_.TaskPath -ceq '\'});if($tasks.Count -eq 0){'null';exit};if($tasks.Count -ne 1){throw 'scheduled task query was ambiguous'};$task=$tasks[0];[pscustomobject]@{TaskName=$task.TaskName;TaskPath=$task.TaskPath;State=$task.State.ToString();Description=$task.Description;Actions=@($task.Actions|Select-Object Execute,Arguments,WorkingDirectory);Triggers=@($task.Triggers|Select-Object Enabled);Enabled=$task.Settings.Enabled}|ConvertTo-Json -Compress;exit}
if($payload.operation -eq 'remove'){Unregister-ScheduledTask -TaskName $payload.task_name -TaskPath '\' -Confirm:$false;exit}
$action=New-ScheduledTaskAction -Execute $payload.execute -Argument $payload.arguments -WorkingDirectory $payload.worktree;$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes([int]$payload.interval) -RepetitionInterval (New-TimeSpan -Minutes([int]$payload.interval));$settings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds 7200);Register-ScheduledTask -TaskName $payload.task_name -TaskPath '\' -Action $action -Trigger $trigger -Settings $settings -Description $payload.description -Force|Out-Null'''


def windows_description(receipt):
    profiles = json.dumps(receipt.get("profile_environment", {}), sort_keys=True, separators=(",", ":"))
    return "Continuation owner " + receipt["owner_id"] + " profiles " + unit_hash(profiles)


def windows_receipt(owner, owner_path, adapter_path, runtime_path, python_path, host_path, interval, environment=None):
    receipt = {"version": 3, "platform": "windows-scheduledtasks", "owner_id": owner["owner_id"],
               "owner_path": str(Path(owner_path).resolve()), "worktree": str(Path(owner["worktree"]).resolve()),
               "harness": owner["harness"], "interval_minutes": interval, "task_name": owner_task_name(owner["owner_id"]),
               "task_path": "\\", "description": "Continuation owner " + owner["owner_id"],
               "helper": str(Path(runtime_path).resolve()), "python": str(Path(python_path).resolve()),
               "script": str(Path(adapter_path).resolve()), "host_executable": str(Path(host_path).resolve()),
               "profile_environment": _profile_environment(environment or os.environ)}
    receipt["description"] = windows_description(receipt)
    receipt["adapter_command"] = adapter_command(receipt)
    receipt["runtime_command"] = runtime_command(receipt)
    receipt["execute"] = receipt["adapter_command"][0]
    receipt["arguments"] = subprocess.list2cmdline(receipt["adapter_command"][1:])
    return receipt


def _same_owner(receipt, owner_path, owner, root):
    return (isinstance(receipt, dict) and isinstance(owner.get("owner_id"), str) and bool(owner["owner_id"].strip())
            and receipt.get("owner_id") == owner["owner_id"]
            and exact_path(receipt.get("owner_path")) == str(Path(owner_path).resolve())
            and exact_path(receipt.get("worktree")) == str(Path(root).resolve()))


def _unit_matches(transport, path, expected, digest):
    try:
        value = transport.read(path)
    except (FileNotFoundError, UnicodeError):
        return False
    return unit_hash(value) == digest and unit_hash(expected) == digest


def _properties(text):
    result = {}
    for line in text.splitlines():
        if "=" not in line:
            raise SchedulerError("systemd show returned unnamed property")
        key, value = line.split("=", 1)
        result[key] = value
    return result


def _show_unit(unit, transport):
    return _properties(_result(transport, ["systemctl", "--user", "show", unit,
        "--property=LoadState,ActiveState,FragmentPath,UnitFileState,DropInPaths,NeedDaemonReload"], timeout=5).stdout)


def receipt_platform(receipt):
    if not isinstance(receipt, dict):
        raise SchedulerError("scheduler receipt is invalid")
    platform = receipt.get("platform")
    if platform in {"linux-systemd", "windows-scheduledtasks"}:
        return platform
    raise SchedulerError("scheduler receipt has no recognized platform identity")


def receipt_is_windows(receipt):
    return receipt_platform(receipt) == "windows-scheduledtasks"


def _link_points_to(link, target):
    try:
        value = os.readlink(str(link))
        actual = Path(value) if Path(value).is_absolute() else Path(link).parent / value
        return actual.resolve(strict=True) == Path(target).resolve(strict=True)
    except (OSError, RuntimeError):
        return False


def assert_linux_write_paths(receipt):
    for path in (receipt["service_path"], receipt["timer_path"]):
        if Path(path).is_symlink():
            raise SchedulerError("systemd unit path is a symlink; refusing to write it")
    link = Path(receipt["timer_enable_path"])
    if link.exists() or link.is_symlink():
        if not link.is_symlink() or not _link_points_to(link, Path(receipt["timer_path"])):
            raise SchedulerError("timer enable link differs from its exact ownership receipt")


def _linux_static(receipt, owner_path, owner, root, transport):
    try:
        platform = receipt_platform(receipt)
    except SchedulerError:
        return False
    if not _same_owner(receipt, owner_path, owner, root) or platform != "linux-systemd":
        return False
    required = ("service_unit", "timer_unit", "unit_directory", "service_path", "timer_path", "timer_enable_path", "service_sha256", "timer_sha256")
    if not all(isinstance(receipt.get(key), str) and receipt[key] for key in required):
        return False
    name = owner_unit_name(owner["owner_id"])
    if receipt["service_unit"] != name + ".service" or receipt["timer_unit"] != name + ".timer":
        return False
    if (Path(receipt["service_path"]).name != receipt["service_unit"] or Path(receipt["timer_path"]).name != receipt["timer_unit"]
            or Path(receipt["service_path"]).parent != Path(receipt["timer_path"]).parent
            or Path(receipt["service_path"]).parent != Path(receipt["unit_directory"]).resolve()
            or Path(receipt["timer_enable_path"]).parent != Path(receipt["unit_directory"]).resolve() / "timers.target.wants"
            or Path(receipt["service_path"]).is_symlink() or Path(receipt["timer_path"]).is_symlink()):
        return False
    try:
        service, timer = linux_units(receipt)
        if not _unit_matches(transport, receipt["service_path"], service, receipt["service_sha256"]):
            return False
        if not _unit_matches(transport, receipt["timer_path"], timer, receipt["timer_sha256"]):
            return False
        service_state = _show_unit(receipt["service_unit"], transport)
        timer_state = _show_unit(receipt["timer_unit"], transport)
    except SchedulerError:
        return False
    for state, path in ((service_state, receipt["service_path"]), (timer_state, receipt["timer_path"])):
        if (state.get("LoadState") != "loaded" or state.get("FragmentPath") != str(path)
                or state.get("DropInPaths", "") or state.get("NeedDaemonReload") != "no"):
            return False
    link = Path(receipt["timer_enable_path"])
    if link.exists() or link.is_symlink():
        if not link.is_symlink() or not _link_points_to(link, Path(receipt["timer_path"])):
            return False
    return True


def verify_linux_ownership(receipt, owner_path, owner, root, transport=None):
    return _linux_static(receipt, owner_path, owner, root, transport or SchedulerTransport())


def verify_linux(receipt, owner_path, owner, root, transport=None):
    transport = transport or SchedulerTransport()
    if not _linux_static(receipt, owner_path, owner, root, transport):
        return False
    try:
        timer = _show_unit(receipt["timer_unit"], transport)
    except SchedulerError:
        return False
    return timer.get("ActiveState") == "active" and timer.get("UnitFileState") == "enabled"


def _windows_task(receipt, transport):
    result = _result(transport, [_powershell(), "-NoProfile", "-NonInteractive", "-Command", WINDOWS_SCRIPT],
                     input_text=json.dumps({"operation": "query", "task_name": receipt["task_name"]}),
                     timeout=WINDOWS_READ_QUERY_TIMEOUT)
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise SchedulerError("ScheduledTasks query returned invalid JSON") from error


def _windows_static(receipt, owner_path, owner, root, transport):
    try:
        platform = receipt_platform(receipt)
    except SchedulerError:
        return False
    if not _same_owner(receipt, owner_path, owner, root) or platform != "windows-scheduledtasks":
        return False
    needed = ("task_name", "task_path", "description", "execute", "arguments")
    if not all(isinstance(receipt.get(key), str) and receipt[key] for key in needed):
        return False
    if receipt["task_name"] != owner_task_name(owner["owner_id"]) or receipt["task_path"] != "\\":
        return False
    if receipt.get("version") != 3 or not all(isinstance(receipt.get(key), str) and receipt[key]
                                              for key in ("python", "script", "host_executable")):
        return False
    command = adapter_command(receipt)
    if (receipt.get("adapter_command") != command or receipt["execute"] != command[0]
            or receipt["arguments"] != subprocess.list2cmdline(command[1:])
            or receipt["description"] != windows_description(receipt)):
        return False
    try:
        task = _windows_task(receipt, transport)
    except SchedulerError:
        return False
    actions = task.get("Actions") if isinstance(task, dict) else None
    action = actions[0] if isinstance(actions, list) and len(actions) == 1 else None
    return bool(isinstance(action, dict) and task.get("TaskName") == receipt["task_name"] and task.get("TaskPath") == "\\"
                and task.get("Description") == receipt["description"] and action.get("Execute") == receipt["execute"]
                and action.get("Arguments") == receipt["arguments"]
                and exact_path(action.get("WorkingDirectory")) == str(Path(root).resolve()))


def verify_windows_ownership(receipt, owner_path, owner, root, transport=None):
    return _windows_static(receipt, owner_path, owner, root, transport or SchedulerTransport())


def verify_windows(receipt, owner_path, owner, root, transport=None):
    transport = transport or SchedulerTransport()
    if not isinstance(receipt, dict) or receipt.get("version") != 3:
        return False
    if not _windows_static(receipt, owner_path, owner, root, transport):
        return False
    try:
        task = _windows_task(receipt, transport)
    except SchedulerError:
        return False
    triggers = task.get("Triggers") if isinstance(task, dict) else None
    return bool(task.get("Enabled") is True and task.get("State") != "Disabled" and isinstance(triggers, list)
                and any(isinstance(trigger, dict) and trigger.get("Enabled") is True for trigger in triggers))


def verify_ownership(receipt, owner_path, owner, root, transport=None, windows=None):
    windows = os.name == "nt" if windows is None else windows
    return verify_windows_ownership(receipt, owner_path, owner, root, transport) if windows else verify_linux_ownership(receipt, owner_path, owner, root, transport)


def verify_receipt(receipt, owner_path, owner, root, transport=None, windows=None):
    windows = os.name == "nt" if windows is None else windows
    return verify_windows(receipt, owner_path, owner, root, transport) if windows else verify_linux(receipt, owner_path, owner, root, transport)


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def _known_linux_files(candidate, transport):
    service, timer = linux_units(candidate)
    values = {}
    for path, expected in ((candidate["service_path"], service), (candidate["timer_path"], timer)):
        try:
            values[path] = transport.read(path)
        except FileNotFoundError:
            values[path] = None
    return values


def _cleanup_initial_linux(proposed, transport):
    service, timer = linux_units(proposed)
    actual = _known_linux_files(proposed, transport)
    if any(value not in (None, service, timer) for value in actual.values()):
        raise SchedulerError("pending systemd unit matches neither recorded identity; preserving transaction evidence")
    if any(value is not None for value in actual.values()):
        _result(transport, ["systemctl", "--user", "disable", "--now", proposed["timer_unit"]], timeout=15)
    for path, expected in ((proposed["service_path"], service), (proposed["timer_path"], timer)):
        if actual[path] == expected:
            transport.remove(path)
    _result(transport, ["systemctl", "--user", "daemon-reload"], timeout=15)


def _validate_linux_recovery_evidence(candidates, transport):
    expected = {}
    links = {}
    for candidate in candidates:
        if candidate is None:
            continue
        service, timer = linux_units(candidate)
        expected.setdefault(candidate["service_path"], set()).add(service)
        expected.setdefault(candidate["timer_path"], set()).add(timer)
        links.setdefault(candidate["timer_enable_path"], set()).add(candidate["timer_path"])
        for unit, path in ((candidate["service_unit"], candidate["service_path"]),
                           (candidate["timer_unit"], candidate["timer_path"])):
            state = _show_unit(unit, transport)
            if state.get("DropInPaths", ""):
                raise SchedulerError("pending systemd unit has foreign loaded drop-ins; preserving transaction evidence")
            fragment = state.get("FragmentPath", "")
            if state.get("LoadState") == "loaded" and fragment != str(path):
                raise SchedulerError("pending systemd unit has a foreign loaded fragment; preserving transaction evidence")
            if fragment and fragment != str(path):
                raise SchedulerError("pending systemd unit has a foreign fragment; preserving transaction evidence")
    for path, identities in expected.items():
        if Path(path).is_symlink():
            raise SchedulerError("pending systemd unit is a symlink; preserving transaction evidence")
        try:
            actual = transport.read(path)
        except FileNotFoundError:
            continue
        if actual not in identities:
            raise SchedulerError("pending systemd unit matches neither recorded identity; preserving transaction evidence")
    for path, targets in links.items():
        link = Path(path)
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or not any(_link_points_to(link, Path(target)) for target in targets):
                raise SchedulerError("pending systemd enable link differs from recorded identity; preserving transaction evidence")


def reconcile_pending(pending_path, receipt_path, owner_path, owner, root, transport=None, windows=None, dry_run=False):
    transport = transport or SchedulerTransport()
    windows = os.name == "nt" if windows is None else windows
    pending_path, receipt_path = Path(pending_path), Path(receipt_path)
    pending = _read_json(pending_path)
    if pending is None:
        return _read_json(receipt_path)
    proposed, previous = pending.get("proposed"), pending.get("previous")
    if not isinstance(proposed, dict):
        raise SchedulerError("scheduler pending receipt is invalid")
    for candidate in (proposed, previous):
        if candidate is not None and not _same_owner(candidate, owner_path, owner, root):
            raise SchedulerError("scheduler pending receipt has another owner")
    current = _read_json(receipt_path)
    if current not in (None, previous, proposed):
        raise SchedulerError("scheduler receipt matches neither pending registration record")
    previous_missing = pending.get("previous_missing", False)
    if not isinstance(previous_missing, bool) or (previous_missing and previous is None):
        raise SchedulerError("scheduler pending receipt has invalid prior absence state")
    if windows:
        actual = _windows_task(proposed, transport)
        if actual is None:
            resolved = previous
        elif verify_windows_ownership(proposed, owner_path, owner, root, transport):
            resolved = proposed
        elif previous and verify_windows_ownership(previous, owner_path, owner, root, transport):
            resolved = previous
        else:
            raise SchedulerError("pending scheduled task matches neither pending registration identity; preserving task and transaction evidence")
        if not dry_run:
            if resolved is None:
                pending_path.unlink()
            else:
                atomic_json(receipt_path, resolved)
                pending_path.unlink()
        return resolved
    _validate_linux_recovery_evidence((proposed, previous), transport)
    proposed_owned = verify_linux_ownership(proposed, owner_path, owner, root, transport)
    previous_owned = previous and verify_linux_ownership(previous, owner_path, owner, root, transport)
    if proposed_owned:
        resolved = proposed
    elif previous_owned:
        resolved = previous
    elif previous is None or previous_missing:
        if not dry_run:
            _cleanup_initial_linux(proposed, transport)
            if previous is None:
                pending_path.unlink()
            else:
                atomic_json(receipt_path, previous)
                pending_path.unlink()
        return previous
    else:
        if not dry_run:
            service, timer = linux_units(previous)
            transport.write(previous["service_path"], service)
            transport.write(previous["timer_path"], timer)
            _result(transport, ["systemctl", "--user", "daemon-reload"], timeout=15)
            if not verify_linux_ownership(previous, owner_path, owner, root, transport):
                raise SchedulerError("restored scheduler differs from its exact ownership receipt after reload; preserving transaction evidence")
            _result(transport, ["systemctl", "--user", "enable", "--now", previous["timer_unit"]], timeout=15)
            atomic_json(receipt_path, previous)
            pending_path.unlink()
        return previous
    if not dry_run:
        atomic_json(receipt_path, resolved)
        pending_path.unlink()
    return resolved
