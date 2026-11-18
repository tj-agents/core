import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "repository_configuration", ROOT / ".agents/workflows/repository_configuration.py"
)
CONFIGURATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIGURATION)
POLICY_SPEC = importlib.util.spec_from_file_location(
    "delivery_policy", ROOT / ".agents/workflows/delivery_policy.py"
)
POLICY = importlib.util.module_from_spec(POLICY_SPEC)
POLICY_SPEC.loader.exec_module(POLICY)


class RepositoryConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="repository configuration Ünicode ")
        self.root = Path(self.temp.name)
        self.agents = self.root / ".agents"
        self.agents.mkdir()
        self.policy = {"standing_authorization": "auto", "instruction": "merge"}

    def tearDown(self):
        self.temp.cleanup()

    def write(self, value):
        (self.agents / "configuration.json").write_text(value, encoding="utf-8")

    def envelope(self, configuration):
        self.write(json.dumps({"schema_version": 1, "configuration": configuration}))

    def test_absent_configuration_uses_strict_legacy_preference(self):
        self.assertIsNone(CONFIGURATION.load(self.root))
        self.assertTrue(POLICY.auto_merge_preference(self.root, {**self.policy, "auto_merge": True}))
        self.assertFalse(POLICY.auto_merge_preference(self.root, self.policy))

    def test_invalid_authority_is_rejected_before_any_preference_is_resolved(self):
        self.envelope({"core": {"auto_merge": True}})
        for invalid in ({"standing_authorization": []}, {}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(POLICY.PolicyViolation):
                    POLICY.auto_merge_preference(self.root, invalid)

    def test_present_configuration_is_authoritative_and_future_namespaces_are_opaque(self):
        self.envelope({"marketplace-x": {"values": [1, {"nested": "preserved"}]}})
        self.assertEqual(
            {"marketplace-x": {"values": [1, {"nested": "preserved"}]}},
            CONFIGURATION.load(self.root),
        )
        self.assertFalse(POLICY.auto_merge_preference(self.root, {**self.policy, "auto_merge": True}))
        self.envelope({"core": {"auto_merge": False}})
        self.assertFalse(POLICY.auto_merge_preference(self.root, {**self.policy, "auto_merge": True}))
        self.envelope({"core": {"auto_merge": True}})
        self.assertTrue(POLICY.auto_merge_preference(self.root, self.policy))

    def test_core_namespace_is_strict(self):
        for core in (
            {"auto_merge": "true"},
            {"auto_merge": 1},
            {"unknown": True},
        ):
            with self.subTest(core=core):
                self.envelope({"core": core})
                with self.assertRaises(ValueError):
                    POLICY.auto_merge_preference(self.root, self.policy)

    def test_reader_rejects_invalid_envelopes_and_numbers(self):
        invalid = (
            "{",
            '{"schema_version": true, "configuration": {}}',
            '{"schema_version": 2, "configuration": {}}',
            '{"schema_version": 1, "configuration": [], "extra": true}',
            '{"schema_version": 1, "configuration": {"Bad": {}}}',
            '{"schema_version": 1, "configuration": {"core": []}}',
            '{"schema_version": 1, "configuration": {"core": {"a": 1, "a": 2}}}',
            '{"schema_version": 1, "configuration": {"future": {"value": 1e999}}}',
            '{"schema_version": 1, "configuration": {"future": {"value": NaN}}}',
        )
        for value in invalid:
            with self.subTest(value=value):
                self.write(value)
                with self.assertRaises(CONFIGURATION.ConfigurationViolation):
                    CONFIGURATION.load(self.root)

    def test_invalid_present_file_never_falls_back_to_legacy(self):
        path = self.agents / "configuration.json"
        path.mkdir()
        with self.assertRaises(ValueError):
            POLICY.auto_merge_preference(self.root, {**self.policy, "auto_merge": True})

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_dangling_link_is_invalid_present_configuration(self):
        path = self.agents / "configuration.json"
        try:
            os.symlink(self.agents / "missing.json", path)
        except OSError as error:
            self.skipTest(str(error))
        with self.assertRaises(CONFIGURATION.ConfigurationViolation):
            CONFIGURATION.load(self.root)


if __name__ == "__main__":
    unittest.main()
