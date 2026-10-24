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

    def write(self, value):
        path = self.agents / "settings.json"
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
        return path

    def test_absent_settings_disable_auto_merge_and_design_approval(self):
        self.assertFalse(delivery_policy.auto_merge_preference(self.root))
        self.assertFalse(CONFIGURATION.auto_approve_design(self.root))

    def test_design_approval_defaults_to_false_without_settings(self):
        enabled, provenance = CONFIGURATION.auto_approve_design_provenance(self.root)
        self.assertFalse(enabled)
        self.assertIn("no settings file", provenance)

    def test_design_approval_uses_nested_precedence(self):
        cases = (
            ({"auto_approve": {"all": True}}, True, "auto_approve.all"),
            ({"auto_approve": {"all": False, "design": True}}, True, "auto_approve.design"),
            ({"auto_approve": {"all": True, "design": False}}, False, "auto_approve.design"),
            ({"auto_approve": {}}, False, "auto_approve default"),
        )
        for core, expected, provenance_selector in cases:
            with self.subTest(core=core):
                self.write({"configuration": {"core": core}})
                self.assertEqual(expected, CONFIGURATION.auto_approve_design(self.root))
                enabled, provenance = CONFIGURATION.auto_approve_design_provenance(self.root)
                self.assertEqual(expected, enabled)
                self.assertIn(provenance_selector, provenance)

    def test_design_approval_is_independent_of_auto_merge(self):
        self.write({"configuration": {"core": {"auto_approve": {"design": True}}}})
        self.assertTrue(CONFIGURATION.auto_approve_design(self.root))
        self.assertFalse(delivery_policy.auto_merge_preference(self.root))

    def test_present_settings_are_authoritative_and_preserve_other_namespaces(self):
        path = self.write({
            "marketplaces": {"future": True},
            "configuration": {"future": {"feature": {"enabled": True}}},
        })
        before = path.read_text(encoding="utf-8")
        self.assertFalse(delivery_policy.auto_merge_preference(self.root))
        self.assertEqual(before, path.read_text(encoding="utf-8"))

        self.write({"configuration": {"core": {"auto_merge": False}}})
        self.assertFalse(delivery_policy.auto_merge_preference(self.root))

        self.write({"configuration": {"core": {"auto_merge": True}}})
        self.assertTrue(delivery_policy.auto_merge_preference(self.root))

    def test_empty_or_incomplete_present_settings_disable_auto_merge(self):
        for settings in ({}, {"configuration": {}}, {"configuration": {"core": {}}}):
            with self.subTest(settings=settings):
                self.write(settings)
                self.assertFalse(delivery_policy.auto_merge_preference(self.root))

    def test_configuration_json_is_not_a_second_public_interface(self):
        (self.agents / "configuration.json").write_text(
            json.dumps({"configuration": {"core": {"auto_merge": True}}}), encoding="utf-8"
        )
        self.assertFalse(delivery_policy.auto_merge_preference(self.root))

    def test_core_settings_are_strict(self):
        for core in (
            {"auto_merge": "true"},
            {"auto_merge": 1},
            {"auto_approve": True},
            {"auto_approve": {"all": "true"}},
            {"auto_approve": {"all": 1}},
            {"auto_approve": {"design": "true"}},
            {"auto_approve": {"unknown": True}},
            {"unknown": True},
        ):
            with self.subTest(core=core):
                self.write({"configuration": {"core": core}})
                with self.assertRaises(ValueError):
                    delivery_policy.auto_merge_preference(self.root)
                with self.assertRaises(ValueError):
                    CONFIGURATION.auto_approve_design(self.root)

    def test_core_capabilities_coexist_without_affecting_foreign_namespaces(self):
        self.write({
            "configuration": {
                "core": {"auto_merge": True, "auto_approve": {"design": False}},
                "foreign": {"enabled": "future"},
            }
        })
        self.assertTrue(delivery_policy.auto_merge_preference(self.root))
        self.assertFalse(CONFIGURATION.auto_approve_design(self.root))

        self.write({
            "configuration": {
                "core": {"auto_merge": False, "auto_approve": {"all": True}},
                "foreign": {"enabled": "future"},
            }
        })
        self.assertFalse(delivery_policy.auto_merge_preference(self.root))
        self.assertTrue(CONFIGURATION.auto_approve_design(self.root))

    def test_reader_rejects_malformed_duplicate_nonfinite_and_invalid_namespaces(self):
        invalid = (
            "{",
            '{"configuration": []}',
            '{"configuration": {"Bad": {}}}',
            '{"configuration": {"future": []}}',
            '{"configuration": {"future": {"item": 1, "item": 2}}}',
            '{"configuration": {"future": {"item": NaN}}}',
            '{"configuration": {"future": {"item": 1e999}}}',
            '{"configuration": {"core": {"auto_approve": {"design": true, "design": false}}}}',
        )
        for value in invalid:
            with self.subTest(value=value):
                self.write(value)
                with self.assertRaises(CONFIGURATION.ConfigurationViolation):
                    CONFIGURATION.load(self.root)

    def test_reader_normalizes_deep_json_recursion_to_a_configuration_violation(self):
        self.write(
            '{"configuration":{"future":{"value":'
            + "[" * 20_000
            + "0"
            + "]" * 20_000
            + "}}}"
        )
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

    def test_unreadable_settings_and_invalid_policy_are_refused(self):
        path = self.write({"configuration": {"core": {"auto_merge": True}}})
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            with self.assertRaises(CONFIGURATION.ConfigurationViolation):
                CONFIGURATION.load(self.root)

        path.unlink()
        policy = self.agents / "delivery-authorization.json"
        policy.write_text("{", encoding="utf-8")
        with self.assertRaises(delivery_policy.PolicyViolation):
            delivery_policy.load_policy(self.root)

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
        self.assertFalse(delivery_policy.auto_merge_preference(checkout))

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
        core = configuration["properties"]["core"]
        self.assertFalse(core["additionalProperties"])
        self.assertEqual({"type": "boolean"}, core["properties"]["auto_merge"])
        auto_approve = core["properties"]["auto_approve"]
        self.assertFalse(auto_approve["additionalProperties"])
        self.assertEqual(
            {"all": {"type": "boolean"}, "design": {"type": "boolean"}},
            auto_approve["properties"],
        )


if __name__ == "__main__":
    unittest.main()
