"""Per-prompt and per-tool Claude hooks stay cheap to launch and bounded in what they touch."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ("base", "engineering", "machine")
PER_CALL_EVENTS = ("UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure", "Stop")
TOOLS = ("Bash", "PowerShell", "Read", "Edit", "Write", "MultiEdit", "Skill", "Agent", "Grep")
BUDGET_SECONDS = 10
AUDIT = r"""
import atexit, json, os, runpy, sys
events = []
def audit(event, arguments):
    if event in ("os.scandir", "os.listdir"):
        events.append([event, os.fsdecode(arguments[0]) if arguments and arguments[0] is not None else "."])
    elif event == "subprocess.Popen":
        events.append([event, str(arguments[0])])
atexit.register(lambda: open(os.environ["HOOK_AUDIT"], "w", encoding="utf-8").write(json.dumps(events)))
script = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path[0] = os.path.dirname(script)
sys.addaudithook(audit)
runpy.run_path(script, run_name="__main__")
"""


def manifest(plugin):
    return json.loads((ROOT / "plugins" / plugin / "hooks/claude.json").read_text(encoding="utf-8"))


def matches(matcher, tool):
    return not matcher or re.fullmatch(matcher, tool) is not None


class HookLaunchShape(unittest.TestCase):
    def test_claude_hooks_launch_python_directly_never_through_a_shell(self):
        for plugin in PLUGINS:
            for event, groups in manifest(plugin)["hooks"].items():
                for group in groups:
                    for hook in group["hooks"]:
                        with self.subTest(plugin=plugin, event=event):
                            self.assertEqual("python", hook["command"])
                            self.assertIsInstance(hook["args"], list)
                            self.assertEqual("-B", hook["args"][0])

    def test_each_plugin_launches_at_most_one_interpreter_per_prompt_or_tool_event(self):
        for plugin in PLUGINS:
            hooks = manifest(plugin)["hooks"]
            for event in PER_CALL_EVENTS:
                for tool in TOOLS:
                    launched = sum(
                        len(group["hooks"]) for group in hooks.get(event, [])
                        if matches(group.get("matcher"), tool)
                    )
                    with self.subTest(plugin=plugin, event=event, tool=tool):
                        self.assertLessEqual(launched, 1)


class HookBudgetUnderLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="hook budget ")
        root = Path(cls.temp.name)
        cls.home = root / "home"
        plans = cls.home / ".claude" / "plans"
        for directory in range(150):
            folder = plans / f"repo-{directory}" / "worktree" / "notes"
            folder.mkdir(parents=True)
            for index in range(20):
                (folder / f"plan-{index}.md").write_text("# Plan\n" + "x" * 512, encoding="utf-8")
        cache = cls.home / ".claude" / "plugins" / "cache" / "base-agents"
        for plugin in PLUGINS:
            for version in range(20):
                stale = cache / plugin / f"{version:012x}"
                (stale / ".claude-plugin").mkdir(parents=True)
                shutil.copy2(ROOT / "plugins" / plugin / ".claude-plugin/plugin.json",
                             stale / ".claude-plugin/plugin.json")
                tier = ROOT / "plugins" / plugin / "tier.json"
                if tier.is_file():
                    shutil.copy2(tier, stale / "tier.json")
        cls.scratch = root / "temp"
        cls.scratch.mkdir()
        cls.cwd = root / "repo"
        cls.cwd.mkdir()
        subprocess.run(["git", "init", "-q", str(cls.cwd)], check=True)
        (cls.cwd / "GOAL.md").write_text("# Goal\n\nStatus: in progress\n", encoding="utf-8")
        cls.prompt = "Continue and complete the active goal."
        cls.transcript = root / "session.jsonl"
        stamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        with cls.transcript.open("w", encoding="utf-8") as handle:
            for _ in range(1500):
                handle.write(json.dumps({"type": "assistant", "message": {
                    "content": [{"type": "text", "text": "y" * 1200}]}}) + "\n")
            handle.write(json.dumps({"type": "user", "origin": {"kind": "human"}, "timestamp": stamp,
                                     "message": {"role": "user", "content": cls.prompt}}) + "\n")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_registered(self, plugin, event, payload):
        package = ROOT / "plugins" / plugin
        environment = dict(
            os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
            CLAUDE_PLUGIN_ROOT=str(package), TEMP=str(self.scratch), TMP=str(self.scratch),
            TMPDIR=str(self.scratch), PYTHONIOENCODING="utf-8",
        )
        environment.pop("CLAUDE_CONFIG_DIR", None)
        environment.pop("CODEX_HOME", None)
        data = {"hook_event_name": event, "cwd": str(self.cwd), "session_id": self.session,
                "transcript_path": str(self.transcript), "tool_use_id": str(uuid.uuid4()),
                **payload}
        tool = payload.get("tool_name", "")
        runs = []
        for group in manifest(plugin)["hooks"].get(event, []):
            if not matches(group.get("matcher"), tool):
                continue
            for hook in group["hooks"]:
                arguments = [argument.replace("${CLAUDE_PLUGIN_ROOT}", str(package))
                             for argument in hook["args"]]
                audit = self.scratch / f"audit-{uuid.uuid4().hex}.json"
                environment["HOOK_AUDIT"] = str(audit)
                started = time.perf_counter()
                result = subprocess.run(
                    [hook["command"], "-B", "-c", AUDIT, *arguments[1:]],
                    input=json.dumps(data), capture_output=True, text=True, encoding="utf-8",
                    cwd=self.cwd, env=environment, timeout=hook["timeout"],
                )
                elapsed = time.perf_counter() - started
                events = json.loads(audit.read_text(encoding="utf-8")) if audit.exists() else []
                runs.append((hook, result, elapsed, events))
        return runs

    def assert_bounded(self, runs):
        plans = str(self.home / ".claude" / "plans").lower()
        for hook, result, elapsed, events in runs:
            with self.subTest(hook=hook["args"][1]):
                self.assertNotEqual(2, result.returncode, result.stderr)
                self.assertLess(elapsed, BUDGET_SECONDS)
                touched = [path for event, path in events
                           if event != "subprocess.Popen" and path.lower().startswith(plans)]
                self.assertEqual([], touched)

    def setUp(self):
        self.session = str(uuid.uuid4())

    def test_prompt_route_does_no_scans_or_subprocesses_under_load(self):
        runs = self.run_registered("engineering", "UserPromptSubmit", {"prompt": self.prompt})
        self.assertEqual(1, len(runs))
        self.assert_bounded(runs)
        hook, result, _, events = runs[0]
        self.assertIn("engineering:plan-execution automatically selected", result.stdout)
        self.assertEqual([], [event for event in events if event[0] == "subprocess.Popen"])
        watched = (str(self.home).lower(), str(self.cwd).lower())
        self.assertEqual([], [path for _, path in events if path.lower().startswith(watched)])

    def test_tool_hooks_stay_within_budget_and_recover_a_lost_route(self):
        recovered = []
        for plugin in PLUGINS:
            for event, payload in (
                ("PreToolUse", {"tool_name": "Bash", "tool_input": {"command": "git status"}}),
                ("PreToolUse", {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}),
                ("PostToolUse", {"tool_name": "Bash", "tool_input": {"command": "git status"},
                                 "tool_response": {"stdout": "", "stderr": ""}}),
                ("Stop", {"stop_hook_active": False}),
            ):
                runs = self.run_registered(plugin, event, payload)
                self.assert_bounded(runs)
                recovered.extend(result.stdout for _, result, _, _ in runs
                                 if "did not deliver this prompt's route" in result.stdout)
        self.assertEqual(1, len(recovered))


if __name__ == "__main__":
    unittest.main()
