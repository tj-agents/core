import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".agents" / "workflows"))
import delivery_policy


SPEC = importlib.util.spec_from_file_location(
    "repository_configuration", ROOT / ".agents" / "workflows" / "repository_configuration.py"
)
CONFIGURATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIGURATION)


class RepositoryConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="répository settings ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.agents = self.root / ".agents"
        self.agents.mkdir()
        self.policy = {"standing_authorization": "auto", "instruction": "Merge green reviewed PRs", "auto_merge": True}

    def write(self, value):
        path = self.agents / "settings.json"
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
        return path

    def test_absent_settings_fall_back_to_a_valid_legacy_preference(self):
        self.assertTrue(delivery_policy.auto_merge_preference(self.root, self.policy))

    def test_present_settings_are_authoritative_and_preserve_other_namespaces(self):
        path = self.write({
            "marketplaces": {"future": True},
            "configuration": {"future": {"feature": {"enabled": True}}},
        })
        before = path.read_text(encoding="utf-8")
        self.assertFalse(delivery_policy.auto_merge_preference(self.root, self.policy))
        self.assertEqual(before, path.read_text(encoding="utf-8"))

        self.write({"configuration": {"core": {"auto_merge": False}}})
        self.assertFalse(delivery_policy.auto_merge_preference(self.root, self.policy))

        self.write({"configuration": {"core": {"auto_merge": True}}})
        self.assertTrue(delivery_policy.auto_merge_preference(self.root, self.policy))

    def test_empty_or_incomplete_present_settings_disable_the_legacy_preference(self):
        for settings in ({}, {"configuration": {}}, {"configuration": {"core": {}}}):
            with self.subTest(settings=settings):
                self.write(settings)
                self.assertFalse(delivery_policy.auto_merge_preference(self.root, self.policy))

    def test_configuration_json_is_not_a_second_public_interface(self):
        (self.agents / "configuration.json").write_text(
            json.dumps({"configuration": {"core": {"auto_merge": True}}}), encoding="utf-8"
        )
        policy = {"standing_authorization": "auto", "instruction": "Merge green reviewed PRs"}
        self.assertFalse(delivery_policy.auto_merge_preference(self.root, policy))

    def test_core_settings_are_strict(self):
        for core in ({"auto_merge": "true"}, {"auto_merge": 1}, {"unknown": True}):
            with self.subTest(core=core):
                self.write({"configuration": {"core": core}})
                with self.assertRaises(ValueError):
                    delivery_policy.auto_merge_preference(self.root, self.policy)

    def test_reader_rejects_malformed_duplicate_nonfinite_and_invalid_namespaces(self):
        invalid = (
            "{",
            '{"configuration": []}',
            '{"configuration": {"Bad": {}}}',
            '{"configuration": {"future": []}}',
            '{"configuration": {"future": {"item": 1, "item": 2}}}',
            '{"configuration": {"future": {"item": NaN}}}',
            '{"configuration": {"future": {"item": 1e999}}}',
        )
        for value in invalid:
            with self.subTest(value=value):
                self.write(value)
                with self.assertRaises(CONFIGURATION.ConfigurationViolation):
                    CONFIGURATION.load(self.root)

    def test_directory_and_redirected_paths_are_invalid(self):
        path = self.agents / "settings.json"
        path.mkdir()
        with self.assertRaises(CONFIGURATION.ConfigurationViolation):
            CONFIGURATION.load(self.root)
        path.rmdir()

        redirected = self.root / "redirected"
        redirected.mkdir()
        self.agents.rmdir()
        try:
            os.symlink(redirected, self.agents, target_is_directory=True)
        except OSError as error:
            self.skipTest(str(error))
        with self.assertRaises(CONFIGURATION.ConfigurationViolation):
            CONFIGURATION.load(self.root)

    def test_final_symlink_is_invalid(self):
        path = self.agents / "settings.json"
        try:
            os.symlink(self.root / "missing.json", path)
        except OSError as error:
            self.skipTest(str(error))
        with self.assertRaises(CONFIGURATION.ConfigurationViolation):
            CONFIGURATION.load(self.root)

    def test_unreadable_present_settings_and_invalid_legacy_are_not_fallbacks(self):
        path = self.write({"configuration": {"core": {"auto_merge": True}}})
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            with self.assertRaises(CONFIGURATION.ConfigurationViolation):
                CONFIGURATION.load(self.root)

        path.unlink()
        legacy = self.agents / "delivery-authorization.json"
        legacy.write_text("{", encoding="utf-8")
        with self.assertRaises(delivery_policy.PolicyViolation):
            delivery_policy.load_legacy_policy(self.root)

    def test_reader_ignores_ancestor_and_host_settings(self):
        checkout = self.root / "checkout"
        checkout_agents = checkout / ".agents"
        checkout_agents.mkdir(parents=True)
        (self.agents / "settings.json").write_text(
            json.dumps({"configuration": {"core": {"auto_merge": True}}}), encoding="utf-8"
        )
        (checkout / ".claude").mkdir()
        (checkout / ".claude" / "settings.json").write_text(
            json.dumps({"configuration": {"core": {"auto_merge": True}}}), encoding="utf-8"
        )
        policy = {"standing_authorization": "auto", "instruction": "Merge green reviewed PRs"}
        self.assertFalse(delivery_policy.auto_merge_preference(checkout, policy))

    def test_schema_keeps_root_settings_open_and_matches_namespace_rules(self):
        schema = json.loads(
            (ROOT / ".agents" / "schemas" / "repository-configuration.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("required", schema)
        self.assertNotIn("additionalProperties", schema)
        configuration = schema["properties"]["configuration"]
        self.assertEqual("^[a-z][a-z0-9-]*$", configuration["propertyNames"]["pattern"])
        self.assertEqual({"type": "object"}, configuration["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
