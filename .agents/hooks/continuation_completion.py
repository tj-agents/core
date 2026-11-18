import importlib.util
import json
import os
import sys
from pathlib import Path


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


def completion_status(root):
    try:
        root = Path(root).resolve()
        owner_path = root / ".agents" / "continuation" / "owner.json"
        if not os.path.lexists(owner_path):
            return {"known": False, "ready": False}
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
        if not isinstance(owner, dict):
            return {"known": True, "ready": False, "reason": "owner-invalid"}
        if owner.get("state") != "complete":
            return {"known": True, "ready": False, "reason": "owner-not-complete", "owner": owner}
        if str(Path(owner.get("worktree", "")).resolve()) != str(root):
            return {"known": True, "ready": False, "reason": "owner-worktree-changed", "owner": owner}
        workflows = workflow_root()
        if str(workflows) not in sys.path:
            sys.path.insert(0, str(workflows))
        completion = module("completion", workflows)
        runtime = module("continuation_runtime", workflows)
        binding = runtime.check_identity(owner, allow_terminal_release=True)
        required = binding
        if required is None and owner.get("pr") is not None:
            required = {"repository": owner["repo"], "pr": owner["pr"], "head": owner["head"]}
        result = completion.completion_check(Path(owner["goal"]), required, root)
        pending = result.get("pending_cleanup")
        ready_for_cleanup = (
            result.get("report_ready") is True
            and isinstance(pending, list)
            and all(
                isinstance(item, dict)
                and str(Path(item.get("worktree", "")).resolve()) == str(root)
                for item in pending
            )
        )
        return {
            "known": True,
            "ready": result.get("ready") is True,
            "ready_for_cleanup": ready_for_cleanup,
            "reason": None if result.get("ready") is True else "completion-unverified",
            "owner": owner,
            "completion": result,
        }
    except (OSError, RuntimeError, ValueError, KeyError, TypeError):
        return {"known": True, "ready": False, "reason": "completion-unverified"}
