"""Per-prompt and per-tool Claude hooks stay cheap to launch and bounded in what they touch."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ("base",)
PER_CALL_EVENTS = ("UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure", "Stop")
TOOLS = ("Bash", "PowerShell", "Read", "Edit", "Write", "MultiEdit", "Skill", "Agent", "Grep")
BUDGET_SECONDS = 10
WRITE_GATE_SECONDS = 1
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
                            self.assertEqual("tj_hook", hook["command"])
                            self.assertIsInstance(hook["args"], list)
                            self.assertEqual(["--", "python", "-B"], hook["args"][:3])

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
        cache = cls.home / ".claude" / "plugins" / "cache" / "tj-agents"
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

    def run_registered(self, plugin, event, payload, home=None, cwd=None):
        home = home or self.home
        cwd = cwd or self.cwd
        package = ROOT / "plugins" / plugin
        environment = dict(
            os.environ, HOME=str(home), USERPROFILE=str(home),
            CLAUDE_PLUGIN_ROOT=str(package), TEMP=str(self.scratch), TMP=str(self.scratch),
            TMPDIR=str(self.scratch), PYTHONIOENCODING="utf-8",
        )
        environment.pop("CLAUDE_CONFIG_DIR", None)
        environment.pop("CODEX_HOME", None)
        data = {"hook_event_name": event, "cwd": str(cwd), "session_id": self.session,
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
                    [hook["command"], *arguments[:2], "-B", "-c", AUDIT, *arguments[3:]],
                    input=json.dumps(data), capture_output=True, text=True, encoding="utf-8",
                    cwd=cwd, env=environment, timeout=hook["timeout"],
                )
                elapsed = time.perf_counter() - started
                events = json.loads(audit.read_text(encoding="utf-8")) if audit.exists() else []
                runs.append((hook, result, elapsed, events))
        return runs

    def assert_bounded(self, runs):
        plans = str(self.home / ".claude" / "plans").lower()
        for hook, result, elapsed, events in runs:
            with self.subTest(hook=hook["args"][3]):
                self.assertNotEqual(2, result.returncode, result.stderr)
                self.assertLess(elapsed, BUDGET_SECONDS)
                touched = [path for event, path in events
                           if event != "subprocess.Popen" and path.lower().startswith(plans)]
                self.assertEqual([], touched)

    def setUp(self):
        self.session = str(uuid.uuid4())

    def test_tool_hooks_stay_within_budget(self):
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

    def test_write_gate_decides_within_a_second_without_git_or_repository_scans(self):
        root = Path(self.temp.name) / "write gate"
        home = root / "home"
        cache = home / ".claude" / "plugins" / "cache"
        payload = cache / "tj-agents" / "python" / "1.0.0"
        header = "---\nname: style\ndescription: Style.\nkind: convention\nprofile: core\n---\n"
        (payload / "skills/style").mkdir(parents=True)
        (payload / "skills/style/SKILL.md").write_text(header + "Read the canonical file.\n", encoding="utf-8")
        canonical = payload / ".agents/python/convention/style/SKILL.md"
        canonical.parent.mkdir(parents=True)
        canonical.write_text(header + "Rule body.\n", encoding="utf-8")
        (payload / "tier.json").write_text(json.dumps({
            "schema_version": 1, "tier": "python", "applies": "stack-present",
            "detect": {"files": ["pyproject.toml"], "globs": ["*.py"]}}), encoding="utf-8")
        (cache.parent / "installed_plugins.json").write_text(json.dumps({"plugins": {
            "python@tj-agents": [{"scope": "user", "installPath": str(payload)}]}}), encoding="utf-8")
        repository = root / "repository"
        (repository / ".git").mkdir(parents=True)
        (repository / ".agents").mkdir()
        (repository / ".agents/plugins.json").write_text(json.dumps({
            "schema_version": 1, "plugins": ["python@tj-agents"],
            "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}}}), encoding="utf-8")
        for index in range(200):
            folder = repository / "src" / f"package_{index}"
            folder.mkdir(parents=True)
            (folder / "module.py").write_text("value = 1\n", encoding="utf-8")
        write = {"tool_name": "Write", "tool_input": {"file_path": str(repository / "src/app.py"), "content": ""}}
        read = {"tool_name": "Read", "tool_input": {"file_path": str(canonical)}}

        denied = self.run_registered("base", "PreToolUse", write, home, repository)
        recorded = self.run_registered("base", "PreToolUse", read, home, repository)
        allowed = self.run_registered("base", "PreToolUse", write, home, repository)

        decision = json.loads(denied[0][1].stdout)["hookSpecificOutput"]
        self.assertEqual("deny", decision["permissionDecision"])
        self.assertIn(str(canonical.resolve()), decision["permissionDecisionReason"])
        self.assertEqual("", allowed[0][1].stdout)
        for hook, result, elapsed, events in (*denied, *recorded, *allowed):
            with self.subTest(hook=hook["args"][4]):
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertLess(elapsed, WRITE_GATE_SECONDS)
                self.assertEqual([], [path for event, path in events if event == "subprocess.Popen"])
                scanned = [path for event, path in events if event != "subprocess.Popen"
                           and Path(path).resolve().is_relative_to(repository.resolve())]
                self.assertEqual([], scanned)


if __name__ == "__main__":
    unittest.main()
