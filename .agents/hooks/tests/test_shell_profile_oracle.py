import copy
import importlib.util
import sys
import unittest
from pathlib import Path


HOOKS = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).with_name("fixtures")
sys.path.insert(0, str(HOOKS))


def load_oracle():
    spec = importlib.util.spec_from_file_location(
        "shell_profile_oracle", FIXTURES / "shell_profile_oracle.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load_oracle()


class OracleTests(unittest.TestCase):
    def setUp(self):
        self.profiles, self.sources = oracle.load_oracle()
        self.records = oracle.validate(self.profiles, self.sources)

    def test_complete_source_backed_unix_matrix(self):
        self.assertEqual(oracle.EXPECTED_COUNTS, oracle.count_records(self.records))
        self.assertEqual(394, len(self.records))
        self.assertTrue({record["source"] for record in self.records}.issubset(self.sources["sources"]))

    def test_bash_variants_keep_their_editions_and_conditions(self):
        by_id = {record["id"]: record for record in self.records}
        self.assertEqual("SYSLOG_HISTORY && SYSLOG_SHOPT", by_id["bash-O:syslog_history"]["condition"])
        self.assertEqual("__CYGWIN__", by_id["bash-o-cygwin:igncr"]["condition"])
        self.assertEqual("__CYGWIN__", by_id["bash-O-cygwin:completion_strip_exe"]["condition"])
        self.assertEqual("5.3.015", self.sources["sources"]["gfw-bash-5.3.015-cygwin"]["edition"])
        value_group = next(group for group in self.profiles["groups"] if group["id"] == "bash-long-value")
        self.assertEqual("value", value_group["arity"])

    def test_dash_union_is_exact_and_not_a_prefix_alias(self):
        names = {record["name"] for record in self.records if record["shell"] == "dash"}
        self.assertIn("privileged", names)
        self.assertNotIn("priv", names)

    def test_zsh_signs_and_maps_survive_expansion(self):
        signed = {record["id"]: record["signed_option"] for record in self.records if "signed_option" in record}
        self.assertEqual("-BADPATTERN", signed["zsh-native-letters:2"])
        self.assertEqual("-UNSET", signed["zsh-sh-ksh-letters:u"])

    def test_malformed_copies_are_rejected(self):
        malformed = copy.deepcopy(self.profiles)
        malformed["groups"][0]["source"] = "unknown"
        with self.assertRaises(ValueError):
            oracle.validate(malformed, self.sources)
        malformed = copy.deepcopy(self.profiles)
        malformed["groups"][0]["names"].append("debug")
        with self.assertRaises(ValueError):
            oracle.validate(malformed, self.sources)


class ExistingFacadeCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("git_auth_scope_gate", HOOKS / "git_auth_scope_gate.py")
        cls.gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.gate)

    def test_supported_raw_command_fields(self):
        for key in ("command", "cmd", "script", "input"):
            with self.subTest(key=key):
                self.assertEqual("echo ok", self.gate.extract_command("Bash", {key: "echo ok"}))
        self.assertEqual("echo ok", self.gate.extract_command("Bash", {"action": {"command": "echo ok"}}))

    def test_established_shell_and_non_shell_boundaries(self):
        for shell in ("bash", "sh", "zsh", "dash"):
            with self.subTest(shell=shell):
                self.assertEqual("echo ok", self.gate.extract_command("exec_command", {"command": [shell, "-c", "echo ok"]}))
        self.assertEqual("tool alpha", self.gate.extract_command("exec_command", {"command": ["tool", "alpha"]}))
        self.assertIsNone(self.gate.extract_command("Write", {"command": "echo ok"}))
        self.assertIsNone(self.gate.extract_command("Bash", {}))
        self.assertIsNone(self.gate.extract_command("Bash", None))


if __name__ == "__main__":
    unittest.main()
