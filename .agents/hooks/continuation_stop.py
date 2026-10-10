import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from workflow_route import direct_control, read_receipt

WINDOWS = os.name == "nt"


def workflow_root():
    root = Path(__file__).resolve().parent.parent
    for candidate in (root / ".agents" / "workflows", root / "workflows"):
        if candidate.is_dir():
            return candidate
    raise RuntimeError("continuation workflow resources are unavailable")


def module(name, root):
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, root / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def read_json(path, *, required=False):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, ValueError) as error:
        if required:
            raise RuntimeError(f"cannot read JSON artifact at {path}: {error}") from error
        return None
    if isinstance(value, dict):
        return value
    if required:
        raise RuntimeError(f"cannot read JSON artifact at {path}: expected an object")
    return None


def exact_path(value):
    return str(Path(value).resolve()) if isinstance(value, str) and value else None


def scheduler_ready(path, owner, root):
    receipt = read_json(path.parent / "scheduler.json")
    if receipt is None:
        return False
    if receipt.get("owner_id") != owner.get("owner_id"):
        return False
    if exact_path(receipt.get("owner_path")) != str(path.resolve()):
        return False
    if exact_path(receipt.get("worktree")) != str(root):
        return False
    if receipt.get("enabled") is False:
        return False
    if not all(isinstance(receipt.get(key), str) and receipt[key] for key in
               ("task_name", "task_path", "helper", "python", "script")):
        return False
    if not WINDOWS:
        return False
    try:
        environment = dict(os.environ, CONTINUATION_TASK_NAME=receipt["task_name"],
                           CONTINUATION_TASK_PATH=receipt["task_path"])
        result = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();$task = Get-ScheduledTask -TaskName $env:CONTINUATION_TASK_NAME "
                "-TaskPath $env:CONTINUATION_TASK_PATH; "
                "[pscustomobject]@{TaskName=$task.TaskName;TaskPath=$task.TaskPath;"
                "State=$task.State.ToString();Description=$task.Description;"
                "Actions=@($task.Actions | Select-Object Execute,Arguments,WorkingDirectory);"
                "Triggers=@($task.Triggers);Enabled=$task.Settings.Enabled} | ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    try:
        task = json.loads(result.stdout)
    except ValueError:
        return False
    if not isinstance(task, dict) or task.get("State") == "Disabled":
        return False
    actions = task.get("Actions")
    if not isinstance(actions, list) or len(actions) != 1:
        return False
    action = actions[0]
    triggers = task.get("Triggers")
    if not isinstance(action, dict) or task.get("Enabled") is not True or not triggers:
        return False
    if not any(isinstance(trigger, dict) and trigger.get("Enabled") is True for trigger in triggers):
        return False
    return (
        task.get("TaskName") == receipt["task_name"]
        and task.get("TaskPath") == receipt["task_path"]
        and task.get("Description") == receipt["description"]
        and action.get("Execute") == receipt["execute"]
        and action.get("Arguments") == receipt["arguments"]
        and exact_path(action.get("WorkingDirectory")) == str(root)
    )


def observed_wake(path, owner):
    try:
        lines = (path.parent / "events.jsonl").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return False
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("owner_id") == owner.get("owner_id") and event.get("event") == "wake":
            return True
    return False


def supervised(owner):
    result = exact_path(os.environ.get("CONTINUATION_RESULT_PATH"))
    return bool(
        owner.get("owner_id")
        and owner.get("launch_nonce")
        and owner.get("result_path")
        and os.environ.get("CONTINUATION_OWNER_ID") == owner["owner_id"]
        and os.environ.get("CONTINUATION_NONCE") == owner["launch_nonce"]
        and result == exact_path(owner["result_path"])
    )


def documented_blocker(owner):
    if not (isinstance(owner.get("reason"), str) and owner["reason"].strip()
            and isinstance(owner.get("next_action"), str) and owner["next_action"].strip()):
        return False
    if owner["reason"] in {
        "continuation-budget-exhausted",
        "host-capability-or-permission-unavailable",
    }:
        return True
    try:
        text = Path(owner["goal"]).read_text(encoding="utf-8")
    except (OSError, UnicodeError, KeyError):
        return False
    match = re.search(r"^##\s+Next Steps\s*$([\s\S]*?)(?=^##\s|\Z)", text, re.MULTILINE)
    if match is None:
        return False
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    fields = ("Blocked", "Blocked by", "Unblock action", "Resume when")
    return len(lines) >= len(fields) and all(
        line.startswith(f"{field}:") and line.removeprefix(f"{field}:").strip()
        for line, field in zip(lines, fields)
    )


def binding_active(runtime, root, artifact=None):
    if artifact is None:
        artifact = read_json(root / runtime.BINDING_FILE, required=True)
    if artifact is None:
        return False
    binding = runtime.binding_from_artifact(artifact)
    runtime.PersistentDeliveryRouter().validate_binding(binding)
    current = runtime.identity(root)
    for key in ("repo", "worktree", "branch", "head"):
        expected = str(Path(binding["worktree"]).resolve()) if key == "worktree" else binding.get(key)
        if expected != current[key]:
            raise RuntimeError(f"binding-{key}-changed")
    return True


def foreground_owns_current_process(owner, runtime):
    lease = owner.get("foreground")
    if not isinstance(lease, dict) or not isinstance(lease.get("pid"), int):
        return False
    if runtime.process_identity(lease["pid"]) != lease.get("identity"):
        return False
    target = lease["pid"]
    if os.getpid() == target:
        return True
    if WINDOWS:
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                 "$target=[int]$env:CONTINUATION_FOREGROUND_PID;$processes=@{};Get-CimInstance Win32_Process -ErrorAction Stop | ForEach-Object {$processes[[int]$_.ProcessId]=$_};$targetProcess=$processes[$target];"
                 "if(!$targetProcess -or !$targetProcess.ExecutablePath){exit 1};$targetExecutable=$targetProcess.ExecutablePath;$id=$PID;"
                 "while($id){$process=$processes[[int]$id];if(!$process -or !$process.ExecutablePath){exit 1};"
                 "if($id -eq $target){exit 0};if($process.ExecutablePath -eq $targetExecutable){exit 1};$id=$process.ParentProcessId};exit 1"],
                capture_output=True,
                timeout=5,
                env=dict(os.environ, CONTINUATION_FOREGROUND_PID=str(target)),
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0
    try:
        target_executable = os.readlink(f"/proc/{target}/exe")
    except OSError:
        return False
    current = os.getpid()
    while current:
        try:
            if current == target:
                return True
            if os.readlink(f"/proc/{current}/exe") == target_executable:
                return False
            fields = Path(f"/proc/{current}/stat").read_text().rsplit(") ", 1)[1].split()
            current = int(fields[1])
        except (OSError, ValueError, IndexError):
            return False
    return False


def outcome(data):
    if (data.get("hook_event_name") or data.get("hookEventName")) != "Stop":
        return None
    cwd = data.get("cwd")
    session = data.get("session_id") or data.get("sessionId")
    if not isinstance(cwd, str) or not isinstance(session, str) or not cwd or not session:
        return None
    root = Path(cwd).resolve()
    receipt = read_receipt(session)
    matching_receipt = receipt.get("worktree") == str(root)
    if matching_receipt and direct_control(str(receipt.get("prompt", ""))) in {"pause", "cancel", "stop"}:
        return None
    owner_path = root / ".agents" / "continuation" / "owner.json"
    obligation = matching_receipt and receipt.get("execution_obligation") is True
    if matching_receipt and receipt.get("execution_suspended") is True:
        return None
    try:
        owner = read_json(owner_path, required=True)
        binding_path = root / ".agents" / "persistent-workflow-binding.json"
        binding_artifact = read_json(binding_path, required=True)
        if owner is None and not obligation and binding_artifact is None:
            return None
        if owner is not None and exact_path(owner.get("worktree")) != str(root):
            return "Reconcile the canonical continuation owner before ending this turn: owner-worktree-changed"
        workflows = workflow_root()
        if str(workflows) not in sys.path:
            sys.path.insert(0, str(workflows))
        runtime = module("continuation_runtime", workflows)
        completion = module("completion", workflows)
        active_binding = binding_active(runtime, root, binding_artifact)
        if owner is None:
            if obligation or active_binding:
                return "Initialize persistent-workflow for the active delivery binding before ending this turn."
            return None
        binding = runtime.check_identity(owner, allow_terminal_release=owner.get("state") in {"complete", "blocked"})
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        return f"Reconcile the canonical continuation owner before ending this turn: {error}"
    if obligation and owner.get("updated_at", 0) < receipt.get("execution_obligation_at", 0):
        return "The routed execution has no current continuation owner; initialize persistent-workflow before ending this turn."
    if not obligation and owner.get("foreground") and not foreground_owns_current_process(owner, runtime):
        return None
    if supervised(owner):
        return None
    state = owner.get("state")
    if state == "complete":
        try:
            required = binding
            if required is None and owner.get("pr") is not None:
                required = {"repository": owner["repo"], "pr": owner["pr"], "head": owner["head"]}
            result = completion.completion_check(Path(owner["goal"]), required, root)
        except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
            return f"Verify completion through the canonical completion check before ending this turn: {error}"
        return None if result.get("ready") else "Completion is not verified; continue the canonical goal."
    if state == "blocked":
        if documented_blocker(owner):
            return None
        return "The blocked continuation owner lacks a genuine typed gate; reconcile it before ending this turn."
    if state not in {"waiting", "working"}:
        return "The continuation owner has an invalid state; reconcile it before ending this turn."
    if owner.get("foreground"):
        return "The canonical continuation still has foreground ownership; continue or yield it before ending this turn."
    if owner.get("child"):
        return "The canonical continuation has a headless writer; wait for its receipt before ending this turn."
    if state == "working":
        return "The canonical continuation is working without a released foreground lease; reconcile it before ending this turn."
    if not scheduler_ready(owner_path, owner, root) or not observed_wake(owner_path, owner):
        return "Register and enable the matching persistent-workflow scheduler before ending this turn."
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except (OSError, UnicodeError, ValueError):
        return
    if not isinstance(data, dict):
        return
    try:
        reason = outcome(data)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        reason = f"Cannot verify continuation ownership; continue the goal: {error}"
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))
    else:
        print("{}")


if __name__ == "__main__":
    main()
