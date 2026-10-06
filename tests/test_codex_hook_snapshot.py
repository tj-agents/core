import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "codex_hook_snapshot", ROOT / ".agents" / "hooks" / "codex_hook_snapshot.py"
)
SNAPSHOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SNAPSHOT)


class CodexHookSnapshotTests(unittest.TestCase):
    def test_concurrent_delayed_reads_keep_digest_order_and_reject_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in [('a.txt', b'first\r\n'), ('b.bin', b'\xff\r\n'),
                                  ('c.txt', b'last\r')]:
                (root / name).write_bytes(content)
            expected = SNAPSHOT.digest_tree(root, 'base')
            read_bytes = Path.read_bytes
            started = threading.Barrier(3)
            last_finished = threading.Event()
            lock = threading.Lock()
            completions = []
            active = peak = 0

            def delayed_read(path):
                nonlocal active, peak
                with lock:
                    active += 1
                    peak = max(peak, active)
                try:
                    started.wait(timeout=10)
                    content = read_bytes(path)
                    if path.name != 'c.txt' and not last_finished.wait(timeout=10):
                        raise TimeoutError('Concurrent final read did not complete')
                    with lock:
                        completions.append(path.name)
                    if path.name == 'c.txt':
                        last_finished.set()
                    return content
                finally:
                    with lock:
                        active -= 1

            with patch.object(Path, 'read_bytes', delayed_read):
                self.assertEqual(expected, SNAPSHOT.digest_tree(root, 'base'))
                self.assertEqual(3, peak)
                self.assertEqual('c.txt', completions[0])
                (root / 'b.bin').write_bytes(b'tampered')
                with self.assertRaises(SystemExit) as raised:
                    SNAPSHOT.verified(root, expected, 'base')
                self.assertEqual(2, raised.exception.code)

    def test_nested_text_binary_and_exclusions_keep_known_integrity_digests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                'nested/deeper/readme': b'end\r',
                'nested/a.txt': 'café\r\n'.encode('utf-8'),
                'nested/Z.bin': b'\xff\x00\r\n',
                'A.txt': b'first\r\nsecond\rthird\n',
                'catalog/catalog.json': b'catalog\r\n',
                'hooks/codex.json': b'excluded bytes',
            }
            for relative, content in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            (root / 'empty directory').mkdir()
            self.assertEqual('sha256:4cae22b1da621db254dd6f8cae7c0e630f64de733ba21a92b739f5173f54cb5d',
                             SNAPSHOT.digest_tree(root, 'base'))
            self.assertEqual('sha256:31d98d8abb3e0ea352cb87114db6c920bea86ade05e9ac72c6be9b1177789254',
                             SNAPSHOT.digest_tree(root, 'machine'))

    def test_file_directory_and_excluded_symbolic_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            root = temporary / 'package'
            root.mkdir()
            target_file = temporary / 'target.txt'
            target_file.write_text('target', encoding='utf-8')
            target_directory = temporary / 'target directory'
            target_directory.mkdir()
            for relative, target in [('file-link', target_file),
                                     ('directory-link', target_directory),
                                     ('hooks/codex.json', target_file),
                                     ('catalog/catalog.json', target_file)]:
                with self.subTest(relative=relative):
                    link = root / relative
                    link.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        link.symlink_to(target, target_is_directory=target.is_dir())
                    except OSError as error:
                        self.skipTest(f'Symbolic links unavailable: {error}')
                    try:
                        with self.assertRaises(SystemExit) as raised:
                            SNAPSHOT.digest_tree(root, 'machine')
                        self.assertEqual(2, raised.exception.code)
                    finally:
                        link.unlink()

    def test_each_generated_command_binds_to_its_package_bytes(self):
        for plugin in ("base", "engineering", "machine"):
            with self.subTest(plugin=plugin):
                root = ROOT / "plugins" / plugin
                expected = SNAPSHOT.digest_tree(root, plugin)
                manifest = json.loads((root / "hooks" / "codex.json").read_text(encoding="utf-8"))
                for groups in manifest["hooks"].values():
                    for group in groups:
                        for hook in group["hooks"]:
                            for field in ("command", "commandWindows"):
                                command = hook[field]
                                self.assertEqual(
                                    re.search(r"sha256:[0-9a-f]{64}", command).group(), expected
                                )

    def test_hook_survives_deleted_cache_path_and_rejects_modified_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            payload = temporary / "cache" / "base-agents" / "base" / "2.1.16"
            shutil.copytree(ROOT / "plugins" / "base", payload)
            data = temporary / "data"
            manifest = json.loads((payload / "hooks" / "codex.json").read_text(encoding="utf-8"))
            command = manifest["hooks"]["SessionStart"][0]["hooks"][0]["commandWindows"]
            command = command.replace("${PLUGIN_ROOT}", str(payload))
            environment = dict(os.environ, PLUGIN_DATA=str(data))

            first = subprocess.run(
                command, shell=True, cwd=ROOT, env=environment,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            expected = SNAPSHOT.digest_tree(payload, "base")
            key = hashlib.sha256((str(payload) + "\0" + expected).encode("utf-8")).hexdigest()
            snapshot = data / "hook-snapshots" / key
            self.assertTrue((snapshot / "hooks" / "codex_hook_snapshot.py").is_file())

            shutil.rmtree(payload)
            recovered = subprocess.run(
                command, shell=True, cwd=ROOT, env=environment,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            first_context = json.loads(first.stdout)["hookSpecificOutput"]["additionalContext"]
            recovered_context = json.loads(recovered.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Maintained plan artifacts", first_context)
            self.assertIn("Maintained plan artifacts", recovered_context)

            pre_tool = manifest["hooks"]["PreToolUse"][0]["hooks"][0]["commandWindows"]
            pre_tool = pre_tool.replace("${PLUGIN_ROOT}", str(payload))
            routed = subprocess.run(
                pre_tool, shell=True, cwd=ROOT, env=environment,
                input=json.dumps({
                    "tool_name": "exec_command", "cwd": str(ROOT),
                    "tool_input": {"cmd": "echo read only"},
                }),
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(routed.returncode, 0, routed.stderr)

            (snapshot / "hooks" / "hook_runtime.py").write_text("changed", encoding="utf-8")
            rejected = subprocess.run(
                command, shell=True, cwd=ROOT, env=environment,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(rejected.returncode, 2, rejected.stderr)
            self.assertIn("integrity check failed", rejected.stderr)

    def test_same_version_refresh_keeps_each_trusted_package_callable(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            payload = temporary / "cache" / "base-agents" / "base" / "2.1.16"
            shutil.copytree(ROOT / "plugins" / "base", payload)
            data = temporary / "data"
            manifest = json.loads((payload / "hooks" / "codex.json").read_text(encoding="utf-8"))
            template = manifest["hooks"]["SessionStart"][0]["hooks"][0]["commandWindows"]
            template = template.replace("${PLUGIN_ROOT}", str(payload))
            original = re.search(r"sha256:[0-9a-f]{64}", template).group()
            environment = dict(os.environ, PLUGIN_DATA=str(data))
            commands = []

            for revision in ("first", "second"):
                (payload / "revision.txt").write_text(revision, encoding="utf-8")
                expected = SNAPSHOT.digest_tree(payload, "base")
                command = template.replace(original, expected)
                commands.append(command)
                result = subprocess.run(
                    command, shell=True, cwd=ROOT, env=environment,
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            snapshots = list((data / "hook-snapshots").iterdir())
            self.assertEqual(2, len(snapshots))
            self.assertEqual(
                {"first", "second"},
                {(path / "revision.txt").read_text(encoding="utf-8") for path in snapshots},
            )
            shutil.rmtree(payload)
            for command in commands:
                recovered = subprocess.run(
                    command, shell=True, cwd=ROOT, env=environment,
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(recovered.returncode, 0, recovered.stderr)

if __name__ == "__main__":
    unittest.main()
