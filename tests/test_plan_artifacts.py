"""Package-level checks; model behavior requires the separate host probes."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


class PlanArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="plan artifacts ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plugin = self.root / "installed package with spaces"
        shutil.copytree(ROOT / "plugins/base", self.plugin)
        self.cwd = self.root / "unrelated directory"
        self.cwd.mkdir()
        (self.cwd / "PLAN.md").write_text("User-owned plan", encoding="utf-8")

    def manifest(self, host):
        return json.loads((self.plugin / f".{host}-plugin/plugin.json").read_text())

    def invoke(self, host, source="startup", extra=()):
        script = self.plugin / ".agents/base/plan-artifacts/scripts/session-context.py"
        return subprocess.run([sys.executable, "-B", str(script), *extra],
                              input=json.dumps({"hook_event_name": "SessionStart", "source": source}),
                              text=True, encoding="utf-8", capture_output=True, cwd=self.cwd)

    def test_packaged_hook_commands_and_context_for_each_session_source(self):
        before = snapshot(self.root)
        bodies = []
        for host in ("claude", "codex"):
            manifest = self.manifest(host)
            hooks = json.loads((self.plugin / manifest["hooks"]).read_text())
            handler = hooks["hooks"]["SessionStart"][0]["hooks"][0]
            script = ".agents/base/plan-artifacts/scripts/session-context.py"
            expected = (
                f'python -B "${{CLAUDE_PLUGIN_ROOT}}/{script}"'
                if host == "claude"
                else f'python3 -B "${{PLUGIN_ROOT}}/{script}"'
            )
            self.assertEqual(handler["command"], expected)
            if host == "codex":
                self.assertEqual(
                    handler["commandWindows"],
                    f'python -B "${{PLUGIN_ROOT}}/{script}"',
                )
            self.assertTrue((self.plugin / script).is_file())
            self.assertTrue((self.plugin / '.agents/base/plan-artifacts/templates/PLAN.md').is_file())
            for source in ("startup", "resume", "compact", "clear"):
                with self.subTest(host=host, source=source):
                    result = self.invoke(host, source)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(output["hookEventName"], "SessionStart")
                    self.assertEqual(result.stderr, "")
                    body = output["additionalContext"].split("\n\n", 1)[1]
                    contract = (self.plugin / '.agents/base/plan-artifacts/SKILL.md').read_text(encoding='utf-8')
                    self.assertEqual(body, contract.split("\n---\n", 1)[1].strip())
                    bodies.append(body)
        self.assertEqual(len(set(bodies)), 1)
        self.assertEqual(before, snapshot(self.root))

    def test_shell_command_runs_from_unrelated_path_with_spaces(self):
        shell = shutil.which("sh")
        if os.name == "nt" and shutil.which("git"):
            git_bash = Path(shutil.which("git")).resolve().parents[1] / "bin/bash.exe"
            shell = str(git_bash) if git_bash.is_file() else None
        if not shell:
            self.skipTest("No Bash/sh installed; native host probe must cover shell execution")
        for host in ("claude", "codex"):
            hooks = json.loads((self.plugin / self.manifest(host)["hooks"]).read_text())
            hook = hooks['hooks']['SessionStart'][0]['hooks'][0]
            command = hook.get('commandWindows', hook['command']) if os.name == 'nt' else hook['command']
            if host == "codex":
                command = command.replace("${PLUGIN_ROOT}", self.plugin.as_posix())
            env = dict(os.environ, CLAUDE_PLUGIN_ROOT=self.plugin.as_posix(),
                       PLUGIN_ROOT=self.plugin.as_posix())
            native_codex = os.name == "nt" and host == "codex"
            argv = command if native_codex else [shell, "-c", command]
            result = subprocess.run(argv, shell=native_codex, cwd=self.cwd, env=env,
                                    input='{}', text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('additionalContext', json.loads(result.stdout)['hookSpecificOutput'])

    def test_missing_or_invalid_contract_reports_failure_without_mutation(self):
        contract = self.plugin / ".agents/base/plan-artifacts/SKILL.md"
        original = contract.read_bytes()
        for host in ("claude", "codex"):
            for content in (b"invalid contract", b"\xff"):
                contract.write_bytes(content)
                before = snapshot(self.root)
                result = self.invoke(host)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("cannot read contract", result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(before, snapshot(self.root))
            contract.unlink()
            result = self.invoke(host)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(str(contract.resolve()), result.stderr)
            contract.write_bytes(original)

    def test_fallback_is_digest_marked_and_tracks_contract_changes(self):
        result = self.invoke('codex', extra=('--instruction-fragment',))
        self.assertEqual(result.returncode, 0, result.stderr)
        fragment = result.stdout
        contract = self.plugin / '.agents/base/plan-artifacts/SKILL.md'
        digest = hashlib.sha256(contract.read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()
        self.assertIn(f'sha256:{digest}', fragment)
        self.assertIn(contract.read_text().split('\n---\n', 1)[1].strip(), fragment)
        contract.write_text(contract.read_text() + '\nNew revision.\n', encoding='utf-8')
        changed = self.invoke('codex', extra=('--instruction-fragment',)).stdout
        self.assertNotIn(f'sha256:{digest}', changed)
        self.assertIn('New revision.', changed)


if __name__ == '__main__':
    unittest.main()
