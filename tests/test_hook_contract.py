import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync_plugin_packages", ROOT / "scripts/sync_plugin_packages.py")
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class HookContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config, cls.output, skills, _ = SYNC.build(ROOT, validate_catalog_digests=False)
        cls.plugins = {skill["plugin"] for skill in skills.values()}

    def validate(self, output: dict[str, bytes]) -> None:
        SYNC.validate_hook_outputs(output, self.config, self.plugins)

    def test_all_declared_hooks_have_valid_pointers_commands_and_scripts(self) -> None:
        self.validate(self.output)

    def test_shipped_hook_without_manifest_pointer_is_rejected(self) -> None:
        output = copy.deepcopy(self.output)
        path = "plugins/base/.codex-plugin/plugin.json"
        manifest = json.loads(output[path])
        manifest.pop("hooks")
        output[path] = json.dumps(manifest).encode()
        with self.assertRaisesRegex(ValueError, "hook pointer"):
            self.validate(output)

    def test_missing_hook_pointer_target_is_rejected(self) -> None:
        output = copy.deepcopy(self.output)
        del output["plugins/base/hooks/codex.json"]
        with self.assertRaisesRegex(ValueError, "shipped hooks disagree|target is missing"):
            self.validate(output)

    def test_missing_hook_script_target_is_rejected(self) -> None:
        output = copy.deepcopy(self.output)
        del output["plugins/base/hooks/skill_router.py"]
        with self.assertRaisesRegex(ValueError, "script target is missing"):
            self.validate(output)

    def test_missing_second_windows_hook_script_target_is_rejected(self) -> None:
        output = copy.deepcopy(self.output)
        path = "plugins/base/hooks/codex.json"
        payload = json.loads(output[path])
        command = payload["hooks"]["PreToolUse"][0]["hooks"][0]["commandWindows"]
        payload["hooks"]["PreToolUse"][0]["hooks"][0]["commandWindows"] = command.replace(
            "hooks/skill_router.py", "hooks/does-not-exist.py"
        )
        output[path] = json.dumps(payload).encode()
        with self.assertRaisesRegex(ValueError, "script target is missing"):
            self.validate(output)

    def test_unknown_hook_type_is_rejected(self) -> None:
        output = copy.deepcopy(self.output)
        path = "plugins/base/hooks/codex.json"
        payload = json.loads(output[path])
        payload["hooks"]["SessionStart"][0]["hooks"][0]["type"] = "commnad"
        output[path] = json.dumps(payload).encode()
        with self.assertRaisesRegex(ValueError, "unsupported hook type"):
            self.validate(output)

    def test_codex_windows_host_root_expansion_is_enforced(self) -> None:
        output = copy.deepcopy(self.output)
        path = "plugins/base/hooks/codex.json"
        payload = json.loads(output[path])
        payload["hooks"]["PreToolUse"][0]["hooks"][0]["commandWindows"] = (
            'python -B "%PLUGIN_ROOT%/hooks/skill_router.py"'
        )
        output[path] = json.dumps(payload).encode()
        with self.assertRaisesRegex(ValueError, "wrong plugin root"):
            self.validate(output)

    def test_codex_windows_command_is_required(self) -> None:
        output = copy.deepcopy(self.output)
        path = "plugins/base/hooks/codex.json"
        payload = json.loads(output[path])
        payload["hooks"]["PreToolUse"][0]["hooks"][0].pop("commandWindows")
        output[path] = json.dumps(payload).encode()
        with self.assertRaisesRegex(ValueError, "missing commandWindows"):
            self.validate(output)


if __name__ == "__main__":
    unittest.main()
