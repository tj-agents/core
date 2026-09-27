import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "machine" / "bootstrap-capabilities" / "scripts" / "verify_machine.py"
spec = importlib.util.spec_from_file_location("verify_machine", SCRIPT)
verify_machine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_machine)


class VerifyMachineTests(unittest.TestCase):
    def test_reports_behavior_but_ignores_host_trust_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            claude = home / ".claude"
            codex = home / ".codex"
            claude.mkdir()
            codex.mkdir()
            (claude / "settings.json").write_text(
                '{"enabledPlugins":{"base@base-agents":true},"permissions":{"allow":["Read"]}}',
                encoding="utf-8",
            )
            (codex / "config.toml").write_text(
                'notify = ["python", "notify.py"]\n[plugins."base@base-agents"]\nenabled = true\n'
                '[hooks.state."trusted"]\ntrusted_hash = "sha256:x"\n'
                '[marketplaces.openai-bundled]\nsource_type = "local"\n'
                '[plugins."browser@openai-bundled"]\nenabled = true\n',
                encoding="utf-8",
            )
            agents = codex / "agents"
            agents.mkdir()
            (agents / "lane-l1.toml").write_text("", encoding="utf-8")
            findings = verify_machine.audit(home)
            self.assertEqual(4, len(findings))
            self.assertFalse(any("hooks.state" in finding for finding in findings))

    def test_clean_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual([], verify_machine.audit(Path(temp)))

    def test_reports_user_hooks_but_not_trust_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            codex = home / ".codex"
            codex.mkdir()
            (codex / "config.toml").write_text(
                '[hooks.state."trusted"]\ntrusted_hash = "sha256:x"\n'
                '[hooks.custom]\ncommand = "python hook.py"\n',
                encoding="utf-8",
            )
            hooks = codex / "hooks"
            hooks.mkdir()
            (hooks / "local.py").write_text("", encoding="utf-8")
            self.assertEqual(2, len(verify_machine.audit(home)))


if __name__ == "__main__":
    unittest.main()
