import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexWindowsHookCommands(unittest.TestCase):
    def test_authored_pretool_budgets_leave_time_for_host_response(self):
        names = []
        for name in ("base", "engineering"):
            manifest = json.loads(
                (ROOT / ".agents" / "plugins" / "manifests" / "codex" / f"{name}-hooks.json")
                .read_text(encoding="utf-8")
            )
            for group in manifest["hooks"]["PreToolUse"]:
                for hook in group["hooks"]:
                    command = hook["commandWindows"]
                    budget = float(re.search(r"--timeout (\d+)", command)[1])
                    script = command.rsplit("/", 1)[-1].split('"', 1)[0]
                    names.append(script)
                    self.assertEqual(budget, {"tier_gate.py": 7, "delivery_binding_gate.py": 57}.get(script, 12))
                    self.assertEqual(hook["timeout"] - budget, 3)
        self.assertCountEqual(names, [
            "skill_router.py", "tier_gate.py", "git_auth_scope_gate.py",
            "forge_poll_gate.py", "compact_output_gate.py", "delivery_binding_gate.py",
        ])

    def test_every_plugin_uses_host_expanded_plugin_root_and_pretool_adapter(self):
        for name in ("base", "engineering", "machine"):
            with self.subTest(plugin=name):
                manifest = json.loads((ROOT / "plugins" / name / "hooks" / "codex.json").read_text(encoding="utf-8"))
                for event, groups in manifest["hooks"].items():
                    for group in groups:
                        for hook in group["hooks"]:
                            command = hook["commandWindows"]
                            self.assertIn("${PLUGIN_ROOT}", command)
                            self.assertNotIn("%PLUGIN_ROOT%", command)
                            if event == "PreToolUse":
                                self.assertIn("/hooks/pre_tool_use_adapter.py", command)
                                self.assertTrue((ROOT / "plugins" / name / "hooks" / "pre_tool_use_adapter.py").is_file())

    @unittest.skipUnless(os.name == "nt", "Windows shell compatibility test")
    def test_missing_marketplace_and_hook_failure_block_in_windows_shells(self):
        shells = [shell for shell in ("pwsh", "powershell.exe", "cmd.exe") if shutil.which(shell)]
        if not shells:
            self.skipTest("No Windows shell is available")

        with tempfile.TemporaryDirectory(prefix="codex windows hook ", dir=ROOT) as temporary:
            root = Path(temporary)
            plugin = root / "cache with spaces" / "base-agents" / "base" / "2.1.16"
            repo = root / "repo"
            shutil.copytree(ROOT / "plugins" / "base", plugin)
            (repo / ".agents").mkdir(parents=True)
            (repo / ".agents" / "skill-routes.json").write_text(
                json.dumps({"routes": [{"path": "^src/", "skills": ["missing-marketplace:never-shipped"]}]}),
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
            manifest = json.loads((plugin / "hooks" / "codex.json").read_text(encoding="utf-8"))
            command = manifest["hooks"]["PreToolUse"][0]["hooks"][0]["commandWindows"]
            expanded = command.replace("${PLUGIN_ROOT}", str(plugin))
            payload = {
                "cwd": str(repo),
                "tool_name": "apply_patch",
                "tool_input": {"command": "*** Begin Patch\n*** Add File: src/probe.cpp\n+int probe = 1;\n*** End Patch"},
            }
            environment = dict(os.environ)
            environment.pop("PLUGIN_ROOT", None)
            environment["PLUGIN_DATA"] = str(root / "plugin data")
            codex_profile = root / "codex profile"
            codex_profile.mkdir()
            environment["CODEX_HOME"] = str(codex_profile)
            crash = root / "crash.py"
            crash.write_text("raise RuntimeError('probe failure')\n", encoding="utf-8")
            adapter = plugin / "hooks" / "pre_tool_use_adapter.py"
            failed_command = f'python -B "{adapter}" "{crash}"'
            hung = root / "hung.py"
            hung.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
            hung_command = f'python -B "{adapter}" --timeout 1.5 "{hung}"'

            for shell in shells:
                for active_command, expected_reason in (
                    (expanded, "missing-marketplace:never-shipped"),
                    (failed_command, "failed with exit code 1"),
                    (hung_command, "timed out during child execution/output collection"),
                ):
                    with self.subTest(shell=shell, reason=expected_reason):
                        arguments = ([shell, "-NoProfile", "-Command", active_command]
                                     if shell != "cmd.exe" else active_command)
                        result = subprocess.run(
                            arguments,
                            shell=shell == "cmd.exe",
                            input=json.dumps(payload),
                            text=True,
                            capture_output=True,
                            cwd=repo,
                            env=environment,
                            timeout=20,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        decision = json.loads(result.stdout)["hookSpecificOutput"]
                        self.assertEqual(decision["hookEventName"], "PreToolUse")
                        self.assertEqual(decision["permissionDecision"], "deny")
                        self.assertIn(expected_reason, decision["permissionDecisionReason"])
                        self.assertFalse((repo / "src" / "probe.cpp").exists())


if __name__ == "__main__":
    unittest.main()
