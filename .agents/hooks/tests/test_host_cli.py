import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import host_cli
from tj_cli import process


class HostCliTests(unittest.TestCase):
    def test_windows_batch_inventory_uses_delayed_expansion_for_the_resolved_path(self):
        with tempfile.TemporaryDirectory(prefix="host cli & %PATH% ! ") as directory, mock.patch.object(
                host_cli.sys, "platform", "win32"), mock.patch.dict(host_cli.os.environ, {"COMSPEC": "cmd.exe"}):
            binary = Path(directory) / "host & %PATH% !" / "codex.cmd"
            command, environment = host_cli.plugin_inventory_command(binary)
        self.assertEqual(
            ["cmd.exe", "/d", "/v:on", "/s", "/c", '"!TJ_AGENTS_HOST_CLI!" plugin list --json'],
            command,
        )
        self.assertEqual(str(binary.resolve()), environment[host_cli.HOST_CLI_VARIABLE])

    def test_non_batch_command_remains_a_direct_process_invocation(self):
        command, environment = host_cli.plugin_inventory_command(Path("codex"))
        self.assertEqual([str(Path("codex").resolve()), "plugin", "list", "--json"], command)
        self.assertIsNone(environment)

    @unittest.skipUnless(sys.platform == "win32", "Windows command shims run only on Windows")
    def test_windows_batch_inventory_executes_through_the_installed_hidden_launcher(self):
        with tempfile.TemporaryDirectory(prefix="host cli ") as directory:
            binary = Path(directory) / "host & %PATH% !" / "codex.cmd"
            binary.parent.mkdir()
            binary.write_text('@echo {"installed": []}\r\n', encoding="ascii")
            command, environment = host_cli.plugin_inventory_command(binary)
            result = process.run(
                command,
                capture_output=True,
                text=True,
                env=environment,
                timeout=5,
                check=True,
            )
        self.assertEqual('{"installed": []}', result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
