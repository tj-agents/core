import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


HOOKS = Path(__file__).resolve().parents[1]
LAUNCHER = r"C:\plugins\machine\skills\handoff-claude\scripts\launch-claude.ps1"

GATED = {
    "engineering:open-pr": [
        'gh pr create --draft --title "Add tiers" --body-file body.md',
        "git push -u origin HEAD && gh pr create --fill",
        "gh -R tj-agents/core pr new",
        "gh pr edit 54 --body-file body.md",
        'gh pr edit 54 --title "Better title"',
        "gh.exe pr edit 54 -b text",
        'bash -lc "gh pr create --fill"',
    ],
    "engineering:merge": [
        "gh pr merge 54 --merge --auto",
        "gh pr merge --admin",
        "gh api graphql -f query='mutation { enqueuePullRequest(input: {pullRequestId: \"x\"}) { clientMutationId } }'",
        "gh api -X PUT repos/tj-agents/core/pulls/54/merge",
    ],
    "engineering:handoff": [
        f"& '{LAUNCHER}' -WorkingDirectory 'C:\\repo' -PromptPath 'C:\\p.md' -Title t",
        f"pwsh -NoProfile -ExecutionPolicy Bypass -File '{LAUNCHER}' -WorkingDirectory C:\\repo",
        f"pwsh -NoProfile -Command \"& '{LAUNCHER}' -WorkingDirectory C:\\repo\"",
    ],
}

UNGATED = [
    "gh pr view 54 --json body",
    "gh pr checks 54 --watch",
    "gh pr list --head Feature/X",
    "gh pr diff 54",
    "gh pr edit 54 --add-label e2e",
    'grep -rn "gh pr merge" .agents',
    'echo "done && gh pr create"',
    "gh api repos/tj-agents/core/pulls/54/merge",
    "gh issue create --title 'pr create'",
    f"Get-Content '{LAUNCHER}'",
    f"pwsh -NoProfile -Command \"Get-Content '{LAUNCHER}'\"",
    "cat > body.md <<'EOF'\ngh pr merge 54\nEOF",
    "pwsh ./tests/handoff-launchers.tests.ps1",
]


class PackageCommandRouteTests(unittest.TestCase):
    """The engineering package gates its delivery commands on the procedures that own them."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.cwd = self.base / "any repo"
        self.cwd.mkdir()
        self.plugin = self.base / "engineering"
        hooks = self.plugin / "hooks"
        hooks.mkdir(parents=True)
        for name in ("skill_router.py", "hook_runtime.py", "command-routes.json"):
            shutil.copy2(HOOKS / name, hooks / name)
        self.router = hooks / "skill_router.py"
        for name in ("open-pr", "merge", "handoff"):
            skill = self.plugin / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: The {name} procedure.\nkind: workflow\n---\n\n# {name}\n",
                encoding="utf-8",
            )

    def environment(self):
        env = dict(os.environ)
        env["CLAUDE_PLUGIN_ROOT"] = str(self.plugin)
        env["PLUGIN_ROOT"] = str(self.plugin)
        env["HOME"] = str(self.base / "home")
        env["USERPROFILE"] = str(self.base / "home")
        env["CODEX_HOME"] = str(self.base / "home" / ".codex")
        env["CLAUDE_CONFIG_DIR"] = str(self.base / "home" / ".claude")
        return env

    def transcript(self, *loaded):
        path = self.base / f"transcript-{uuid.uuid4()}.jsonl"
        lines = []
        for index, name in enumerate(loaded):
            lines.append({"message": {"content": [
                {"type": "tool_use", "name": "Skill", "id": f"t{index}", "input": {"skill": name}}
            ]}})
            lines.append({"message": {"content": [{"type": "tool_result", "tool_use_id": f"t{index}"}]}})
        path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
        return str(path)

    def run_command(self, command, transcript=None, tool_name="Bash", arguments=("--package-routes",), **extra):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_use_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "cwd": str(self.cwd),
            "tool_name": tool_name,
            "tool_input": {"command": command, "description": "gh pr merge in a description is metadata"},
        }
        if transcript is not None:
            payload["transcript_path"] = transcript
        payload.update(extra)
        return subprocess.run(
            [sys.executable, "-B", str(self.router), *arguments],
            cwd=self.cwd, input=json.dumps(payload), capture_output=True, text=True,
            encoding="utf-8", env=self.environment(), timeout=20,
        )

    def test_each_delivery_command_blocks_until_its_skill_is_proven_loaded(self):
        for skill, commands in GATED.items():
            for command in commands:
                with self.subTest(command=command):
                    blocked = self.run_command(command)
                    other = [name for name in GATED if name != skill]
                    wrong = self.run_command(command, self.transcript(*other))
                    allowed = self.run_command(command, self.transcript(skill))

                    self.assertEqual(2, blocked.returncode, blocked.stderr)
                    self.assertIn(f"* {skill}", blocked.stderr)
                    self.assertIn("a procedure owns this command", blocked.stderr)
                    self.assertIn("The command was NOT run", blocked.stderr)
                    self.assertEqual(2, wrong.returncode, wrong.stderr)
                    self.assertEqual(0, allowed.returncode, allowed.stderr)

    def test_read_only_and_unrelated_commands_never_block(self):
        for command in UNGATED:
            with self.subTest(command=command):
                result = self.run_command(command)

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)

    def test_powershell_and_codex_shells_are_gated_alike(self):
        powershell = self.run_command("gh pr merge 54 --auto", tool_name="PowerShell")
        codex = self.run_command(
            "", tool_name="exec_command", tool_input={"cmd": "gh pr merge 54 --auto"}
        )

        self.assertEqual(2, powershell.returncode, powershell.stderr)
        self.assertEqual(2, codex.returncode, codex.stderr)
        self.assertIn("READ THIS WHOLE FILE", codex.stderr)

    def test_edit_tools_are_not_commands(self):
        result = self.run_command(
            "", tool_name="Write", tool_input={"file_path": "x.md", "content": "gh pr merge 54\n"}
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_a_package_without_command_routes_gates_nothing(self):
        (self.plugin / "hooks" / "command-routes.json").unlink()

        result = self.run_command("gh pr merge 54")

        self.assertEqual(0, result.returncode, result.stderr)

    def test_an_unusable_shipped_file_is_a_loud_packaging_fault(self):
        (self.plugin / "hooks" / "command-routes.json").write_text(
            json.dumps({"routes": [{"command": "^gh pr merge", "deny": [{"pattern": "x"}]}]}),
            encoding="utf-8",
        )

        result = self.run_command("gh pr view 54")

        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("packaging fault", result.stderr)

    def test_the_engineering_package_ships_and_wires_its_command_routes(self):
        package = HOOKS.parents[1] / "plugins" / "engineering" / "hooks"
        self.assertEqual(
            (HOOKS / "command-routes.json").read_bytes(), (package / "command-routes.json").read_bytes()
        )
        for host, matcher in (("claude", "Bash"), ("codex", "exec_command")):
            with self.subTest(host=host):
                hooks = json.loads((package / f"{host}.json").read_text(encoding="utf-8"))
                wired = [
                    group for group in hooks["hooks"]["PreToolUse"]
                    if any("--package-routes" in hook["command"] for hook in group["hooks"])
                ]
                self.assertEqual(1, len(wired))
                self.assertIn(matcher, wired[0]["matcher"])

    def test_the_repo_hook_ignores_package_routes(self):
        result = self.run_command("gh pr merge 54", arguments=())

        self.assertEqual(0, result.returncode, result.stderr)


class RepoCommandRouteTests(unittest.TestCase):
    """A repo table may add its own command routes; the base hook evaluates them with its path routes."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / "repo"
        (self.repo / ".agents").mkdir(parents=True)
        (self.repo / ".git").mkdir()
        self.plugin = self.base / "base"
        hooks = self.plugin / "hooks"
        hooks.mkdir(parents=True)
        for name in ("skill_router.py", "hook_runtime.py"):
            shutil.copy2(HOOKS / name, hooks / name)
        self.router = hooks / "skill_router.py"
        skill = self.plugin / "skills" / "release"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: release\ndescription: Cut a release.\nkind: workflow\n---\n", encoding="utf-8"
        )

    environment = PackageCommandRouteTests.environment

    def routes(self, routes):
        (self.repo / ".agents" / "skill-routes.json").write_text(
            json.dumps({"routes": routes}), encoding="utf-8"
        )

    def run_command(self, command):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_use_id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "cwd": str(self.repo),
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }
        return subprocess.run(
            [sys.executable, "-B", str(self.router)],
            cwd=self.repo, input=json.dumps(payload), capture_output=True, text=True,
            encoding="utf-8", env=self.environment(), timeout=20,
        )

    def test_a_repo_command_route_blocks_its_command_only(self):
        self.routes([{"command": "^gh release create(?: |$)", "skills": ["release"]}])

        blocked = self.run_command("gh release create v1")
        allowed = self.run_command("gh release view v1")

        self.assertEqual(2, blocked.returncode, blocked.stderr)
        self.assertIn("* release", blocked.stderr)
        self.assertEqual(0, allowed.returncode, allowed.stderr)

    def test_a_route_with_both_keys_is_unusable(self):
        self.routes([{"path": "^src/", "command": "^gh release", "skills": ["release"]}])

        result = self.run_command("gh release view v1")

        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("carries both `path` and `command`", result.stderr)

    def test_an_invalid_command_regex_is_unusable(self):
        self.routes([{"command": "^gh (release", "skills": ["release"]}])

        result = self.run_command("gh release view v1")

        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("not a valid regex", result.stderr)


if __name__ == "__main__":
    unittest.main()
