import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUTHORED_HOOKS = ROOT / ".agents" / "hooks"
CLAUDE_HOOKS = ROOT / ".claude" / "hooks"
CODEX_HOOKS = ROOT / ".codex" / "hooks"
PLUGIN = ROOT / "plugins" / "process-standards"
SCRIPTS = (
    "skill_router.py",
    "merge_review_gate.py",
    "model_routing_guard.py",
    "plan_handoff_stop_launcher.py",
    "session_floor.py",
)
# Codex's roster is NOT Claude's minus nothing: the router is registered for both harnesses, but
# merge_review_gate.py is Claude-only until Codex's shell tool name is observed in a real payload -
# its SHELL_TOOLS vocabulary is {bash, powershell}, so a Codex registration would act on nothing.
CODEX_SCRIPTS = (
    "skill_router.py",
    "model_routing_guard.py",
    "marketplace_refresh.py",
    "session_floor.py",
)
# A shipped .py that is deliberately not a harness hook, and why. Anything not here and not in a
# manifest is a hook nobody registered - which is how marketplace_refresh.py shipped dead.
NON_HOOK_HELPERS = {
    "hook_runtime.py": "shared library the hooks import",
    "dev_rules.py": "rule resolver the session hook imports",
    "plan_handoff_stop.py": "implementation the registered launcher execs",
    "plan_graph.py": "argparse CLI the plan skills invoke",
    "ci_change_classifier.py": "argparse CLI the CI workflow invokes",
    "docs_reachability.py": "argparse CLI the CI workflow invokes",
}


def handlers(manifest):
    for groups in manifest["hooks"].values():
        for group in groups:
            yield from group["hooks"]


class ShellVocabularyTests(unittest.TestCase):
    """The gate's matcher and its own vocabulary must name the same shells. A shell the matcher
    omits never reaches the script; a shell the script omits is waved through when it does. Either
    gap is enforcement that is inert while looking wired, so the two are asserted against each
    other rather than each against a hardcoded list."""

    def test_the_merge_gate_matcher_covers_every_shell_the_script_gates(self):
        sys.path.insert(0, str(AUTHORED_HOOKS))
        try:
            import merge_review_gate as gate
        finally:
            sys.path.pop(0)

        manifest = json.loads((CLAUDE_HOOKS / "hooks.json").read_text(encoding="utf-8"))
        matchers = [
            group["matcher"]
            for groups in manifest["hooks"].values()
            for group in groups
            if any("merge_review_gate.py" in h["command"] for h in group["hooks"])
        ]

        self.assertEqual(1, len(matchers), "merge_review_gate.py is not registered exactly once")
        wired = {name.lower() for name in matchers[0].split("|")}

        self.assertEqual(gate.SHELL_TOOLS, wired)


class HookManifestContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.plugin = Path(self.temp.name) / "plugin root with spaces"
        shutil.copytree(PLUGIN, self.plugin)
        self.repo = Path(self.temp.name) / "manifest repository"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.email", "manifest@example.test"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.name", "Manifest Test"],
            check=True,
        )
        agents = self.repo / ".agents"
        agents.mkdir()
        (agents / "skill-routes.json").write_text(
            json.dumps(
                {
                    "routes": [
                        {
                            "path": r"manifest-target\.txt$",
                            "skills": ["commit"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (agents / "merge-gate.json").write_text(
            json.dumps({"security_paths": []}), encoding="utf-8"
        )
        plan_dir = self.repo / "plans" / "manifest"
        plan_dir.mkdir(parents=True)
        (plan_dir / "MANIFEST_PLAN.md").write_text("# Manifest plan\n", encoding="utf-8")
        (plan_dir / "MANIFEST_ROADMAP.md").write_text(
            "# Manifest roadmap\n\n- [ ] **Verify** `manifest/verify`\n",
            encoding="utf-8",
        )
        (plan_dir / "MANIFEST_PROGRESS.md").write_text(
            "\n".join(
                [
                    "# Manifest progress",
                    "",
                    "- Plan: `plans/manifest/MANIFEST_PLAN.md`",
                    "- Roadmap: `plans/manifest/MANIFEST_ROADMAP.md`",
                    "- Roadmap item: `manifest/verify`",
                    f"- Worktree: `{self.repo}`",
                    "",
                    "## Next Steps",
                    "",
                    "Finish the manifest verification.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-q", "-m", "manifest fixture"],
            check=True,
        )

    def read(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_the_plugin_has_a_unique_marketplace_qualified_identity(self):
        marketplace = self.read(ROOT / ".claude-plugin" / "marketplace.json")
        codex = self.read(PLUGIN / ".codex-plugin" / "plugin.json")
        claude = self.read(PLUGIN / ".claude-plugin" / "plugin.json")

        self.assertEqual("base-agents", marketplace["name"])
        self.assertEqual("process-standards", marketplace["plugins"][0]["name"])
        self.assertEqual("./plugins/process-standards", marketplace["plugins"][0]["source"])
        self.assertEqual("process-standards", codex["name"])
        self.assertEqual("process-standards", claude["name"])

    def hook_environment(self, root_variable):
        environment = os.environ.copy()
        for name in ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "CODEX_PLUGIN_ROOT"):
            environment.pop(name, None)
        environment[root_variable] = str(self.plugin)
        return environment

    def claude_shell_environment(self):
        git = shutil.which("git")
        self.assertIsNotNone(git)
        if os.name == "nt":
            git_root = Path(git).parent.parent
            bash = git_root / "bin" / "bash.exe"
            shell_paths = (
                Path(sys.executable).parent,
                git_root / "bin",
                Path(git).parent,
                git_root / "usr" / "bin",
            )
        else:
            bash = Path(shutil.which("bash"))
            python3 = shutil.which("python3")
            self.assertIsNotNone(python3)
            shell_paths = (Path(python3).parent, bash.parent, Path(git).parent)
        self.assertTrue(bash.is_file())
        environment = self.hook_environment("CLAUDE_PLUGIN_ROOT")
        environment["PATH"] = os.pathsep.join(str(path) for path in shell_paths)
        self.assertIsNone(shutil.which("node", path=environment["PATH"]))
        node_probe = subprocess.run(
            [str(bash), "-c", "command -v node"],
            capture_output=True,
            text=True,
            env=environment,
        )
        self.assertNotEqual(0, node_probe.returncode, node_probe.stdout)
        return environment, str(bash)

    def claude_substitute(self, command):
        return command.replace("${CLAUDE_PLUGIN_ROOT}", str(self.plugin))

    def payload_for(self, script, harness):
        invocation = uuid.uuid4().hex
        payload = {
            "session_id": f"manifest-{harness}-{invocation}",
            "cwd": str(self.repo),
        }
        if harness == "codex":
            payload["turn_id"] = f"turn-{invocation}"
        if script == "skill_router.py":
            payload.update(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_use_id": f"skill-{invocation}",
                    "tool_name": "Write" if harness == "claude" else "apply_patch",
                    "tool_input": (
                        {
                            "file_path": str(self.repo / "manifest-target.txt"),
                            "content": "manifest test",
                        }
                        if harness == "claude"
                        else {
                            "patch": (
                                "*** Begin Patch\n"
                                "*** Add File: manifest-target.txt\n"
                                "+manifest test\n"
                                "*** End Patch"
                            )
                        }
                    ),
                }
            )
        elif script == "merge_review_gate.py":
            command = f'pushd "{self.repo}" && gh pr merge 1 --auto'
            payload.update(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_use_id": f"merge-{invocation}",
                    "tool_name": "Bash",
                    "tool_input": {"command": command},
                }
            )
        elif script == "model_routing_guard.py":
            payload.update(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_use_id": f"routing-{invocation}",
                    "tool_name": "PowerShell" if harness == "claude" else "exec_command",
                    "tool_input": {"command": "launch.ps1 -Model fixed"},
                }
            )
        elif script in ("marketplace_refresh.py", "session_floor.py"):
            payload.update({"hook_event_name": "SessionStart"})
            if script == "marketplace_refresh.py":
                payload["cwd"] = str(Path(self.temp.name))
        else:
            payload.update(
                {
                    "hook_event_name": "Stop",
                    "last_assistant_message": "Continue this work in a fresh context.",
                    "stop_hook_active": False,
                }
            )
        return json.dumps(payload)

    def assert_hook_behavior(self, script, result, harness):
        if script == "skill_router.py":
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("SKILL ROUTER - a standard owns this path", result.stderr)
            self.assertIn("Turn the working tree into clean, logical git commits", result.stderr)
        elif script == "merge_review_gate.py":
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("cannot resolve PR #1", result.stderr)
            self.assertNotIn("cannot prove this merge's checkout", result.stderr)
        elif script == "model_routing_guard.py":
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("MODEL ROUTING GUARD", result.stderr)
        elif script == "session_floor.py":
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("behavioral floor", result.stdout)
        elif script == "marketplace_refresh.py":
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", result.stdout)
            self.assertEqual("", result.stderr)
        else:
            self.assertEqual(0, result.returncode, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual("block", response["decision"])
            self.assertIn("MANIFEST_PROGRESS.md was selected for context transfer", response["reason"])
            self.assertNotIn("hook bundle differs from origin/main", response["reason"])

    def test_codex_manifest_selects_its_own_hook_file(self):
        manifest = self.read(PLUGIN / ".codex-plugin" / "plugin.json")

        self.assertEqual("./hooks/codex-hooks.json", manifest["hooks"])
        self.assertNotEqual(PLUGIN / "hooks" / "hooks.json", PLUGIN / manifest["hooks"])

    def test_codex_manifest_selects_its_own_skill_root(self):
        manifest = self.read(PLUGIN / ".codex-plugin" / "plugin.json")

        self.assertEqual("./codex-skills/", manifest["skills"])
        self.assertTrue((PLUGIN / manifest["skills"] / "persistent-workflow" / "SKILL.md").is_file())
        self.assertTrue((PLUGIN / "skills" / "persistent-workflow" / "SKILL.md").is_file())

    def test_claude_bash_form_covers_every_hook_on_native_platform_without_node(self):
        metacharacter_plugin = (
            Path(self.temp.name)
            / "plugin root $CLAUDE_HOOK_PATH_ATTACK $(false) `false`"
        )
        shutil.copytree(self.plugin, metacharacter_plugin)
        self.plugin = metacharacter_plugin
        manifest = self.read(PLUGIN / "hooks" / "hooks.json")
        actual = list(handlers(manifest))

        self.assertEqual(
            SCRIPTS,
            tuple(Path(item["command"].rsplit("/", 1)[1][:-1]).name for item in actual),
        )
        for item in actual:
            self.assertEqual("bash", item["shell"])
            self.assertNotIn("args", item)
            self.assertTrue(
                item["command"].startswith(
                    'plugin_root="$CLAUDE_PLUGIN_ROOT"; if command -v cygpath '
                )
            )
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", item["command"])
            script = Path(item["command"].rsplit("/", 1)[1][:-1]).name
            environment, bash = self.claude_shell_environment()
            environment["CLAUDE_HOOK_PATH_ATTACK"] = "mangled"
            result = subprocess.run(
                [bash, "-c", self.claude_substitute(item["command"])],
                input=self.payload_for(script, "claude"),
                capture_output=True,
                text=True,
                cwd=self.repo,
                env=environment,
            )
            self.assert_hook_behavior(script, result, "claude")

    def test_claude_launcher_selects_python_for_windows_and_python3_for_posix(self):
        launcher = (PLUGIN / "hooks" / "run-claude-hook.sh").read_text(encoding="utf-8")

        self.assertIn("CYGWIN*|MINGW*|MSYS*)", launcher)
        self.assertIn("python_command=python", launcher)
        self.assertIn('script="$(cygpath -w "$script")"', launcher)
        self.assertIn("*) python_command=python3 ;;", launcher)
        self.assertIn('exec "$python_command" -B "$script"', launcher)

    def test_codex_posix_commands_cover_every_hook(self):
        manifest = self.read(PLUGIN / "hooks" / "codex-hooks.json")
        actual = list(handlers(manifest))

        self.assertEqual(CODEX_SCRIPTS, tuple(Path(item["command"].split("/")[-1][:-1]).name for item in actual))
        for item in actual:
            self.assertIn("${PLUGIN_ROOT}/hooks/", item["command"])
            self.assertNotIn("CLAUDE_PLUGIN_ROOT", item["command"])
            if os.name != "nt":
                command = item["command"].replace("${PLUGIN_ROOT}", str(self.plugin))
                result = subprocess.run(
                    ["/bin/sh", "-c", command],
                    input=self.payload_for(Path(item["command"].split("/")[-1][:-1]).name, "codex"),
                    capture_output=True,
                    text=True,
                    cwd=self.repo,
                    env=self.hook_environment("PLUGIN_ROOT"),
                )
                self.assert_hook_behavior(
                    Path(item["command"].split("/")[-1][:-1]).name, result, "codex"
                )

    def test_codex_windows_commands_cover_every_hook(self):
        manifest = self.read(PLUGIN / "hooks" / "codex-hooks.json")
        actual = list(handlers(manifest))

        self.assertEqual(len(CODEX_SCRIPTS), len(actual))
        for script, item in zip(CODEX_SCRIPTS, actual):
            command = item["commandWindows"]
            self.assertEqual(
                'python -B "${PLUGIN_ROOT}/hooks/' + script + '"', command
            )
            self.assertEqual(2, command.count('"'))
            if os.name == "nt":
                resolved = command.replace("${PLUGIN_ROOT}", str(self.plugin))
                result = subprocess.run(
                    f'cmd.exe /D /S /C "{resolved}"',
                    input=self.payload_for(script, "codex"),
                    capture_output=True,
                    text=True,
                    cwd=self.repo,
                    env=self.hook_environment("PLUGIN_ROOT"),
                )
                self.assert_hook_behavior(script, result, "codex")

    def test_every_shipped_hook_is_registered_or_declared_a_helper(self):
        shipped = {path.name for path in (PLUGIN / "hooks").glob("*.py")}
        registered = set(SCRIPTS) | set(CODEX_SCRIPTS)

        self.assertEqual(
            set(),
            shipped - registered - set(NON_HOOK_HELPERS),
            "shipped hook is in no manifest and is not declared a helper",
        )
        self.assertEqual(
            set(),
            registered & set(NON_HOOK_HELPERS),
            "a declared helper is also registered as a hook",
        )
        self.assertEqual(
            set(),
            set(NON_HOOK_HELPERS) - shipped,
            "NON_HOOK_HELPERS names a file the plugin no longer ships",
        )

    def test_generated_manifests_match_the_authored_sources(self):
        # hooks.json/run-claude-hook.sh are Claude-only and codex-hooks.json is Codex-only -
        # each is authored under its own harness folder, never under the shared .agents/hooks.
        sources = {
            "hooks.json": CLAUDE_HOOKS,
            "run-claude-hook.sh": CLAUDE_HOOKS,
            "codex-hooks.json": CODEX_HOOKS,
        }
        for name, source_dir in sources.items():
            authored = (source_dir / name).read_bytes()
            generated = (PLUGIN / "hooks" / name).read_bytes()
            self.assertEqual(authored.replace(b"\r\n", b"\n"), generated.replace(b"\r\n", b"\n"))


if __name__ == "__main__":
    unittest.main()
