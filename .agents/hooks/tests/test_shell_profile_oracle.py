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
        self.assertEqual(436, len(self.records))
        self.assertTrue({record["source"] for record in self.records}.issubset(self.sources["sources"]))

    def test_powershell_descriptor_prefixes_aliases_and_windows_projection(self):
        group = next(group for group in self.profiles["groups"] if group["id"] == "powershell-descriptors")
        descriptors = group["descriptors"]
        records = {record["id"]: record for record in self.records if record["shell"] == "powershell"}
        self.assertEqual(42, len(records))
        self.assertEqual({f"pwsh:{descriptor['name']}" for descriptor in descriptors}, set(records))
        self.assertEqual(["!UNIX"], records["pwsh:v2socketservermode"]["condition"])
        self.assertEqual(["DEBUG"], records["pwsh:isswait"]["condition"])
        self.assertEqual("outputformat", records["pwsh:of"]["canonical_name"])
        self.assertEqual("outputformat", records["pwsh:of"]["enum"])
        self.assertEqual("encodedcommand", records["pwsh:ec"]["canonical_name"])
        self.assertEqual("opaque", records["pwsh:ec"]["action"])
        for descriptor in descriptors:
            for length in range(len(descriptor["minimum_prefix"]), len(descriptor["name"]) + 1):
                supplied = descriptor["name"][:length]
                expected = next(
                    candidate
                    for candidate in descriptors
                    if len(supplied) >= len(candidate["minimum_prefix"])
                    and candidate["name"].casefold().startswith(supplied.casefold())
                )
                with self.subTest(supplied=supplied):
                    self.assertEqual(expected["name"], oracle.resolve_powershell_prefix(self.profiles, supplied)["name"])
        self.assertIsNone(oracle.resolve_powershell_prefix(self.profiles, "n"))
        self.assertIsNone(oracle.resolve_powershell_prefix(self.profiles, "configurationfil"))
        self.assertEqual("interactive", oracle.resolve_powershell_prefix(self.profiles, "i")["name"])
        windows = list(oracle.iter_powershell_descriptors(self.profiles, "windows"))
        windows_by_name = {descriptor["name"]: descriptor for descriptor in windows}
        self.assertEqual(901, records["pwsh:version"]["source_line"])
        self.assertEqual("windows-powershell-5.1-cli-doc", windows_by_name["version"]["source"])
        self.assertEqual(1, windows_by_name["version"]["arity"])
        self.assertNotIn("source_line", windows_by_name["version"])
        self.assertEqual("psconsolefile", windows[-1]["name"])
        self.assertNotIn("cwa", windows_by_name)
        self.assertNotIn("socketservermode", windows_by_name)

    def test_bash_variants_keep_their_editions_and_conditions(self):
        by_id = {record["id"]: record for record in self.records}
        expected = {
            "bash-long:debugger": "DEBUGGER",
            "bash-long:dump-po-strings": "TRANSLATABLE_STRINGS",
            "bash-long:dump-strings": "TRANSLATABLE_STRINGS",
            "bash-long:protected": "WORDEXP_OPTION",
            "bash-long:restricted": "RESTRICTED_SHELL",
            "bash-long:wordexp": "WORDEXP_OPTION",
            "bash-o:braceexpand": "BRACE_EXPANSION",
            "bash-o:emacs": "READLINE",
            "bash-o:histexpand": "BANG_HISTORY",
            "bash-o:history": "HISTORY",
            "bash-o:monitor": "JOB_CONTROL",
            "bash-o:nolog": "HISTORY",
            "bash-o:notify": "JOB_CONTROL",
            "bash-o:vi": "READLINE",
            "bash-O:assoc_expand_once": "ARRAY_VARS",
            "bash-O:checkjobs": "JOB_CONTROL",
            "bash-O:cmdhist": "HISTORY",
            "bash-O:complete_fullquote": "READLINE",
            "bash-O:direxpand": "READLINE",
            "bash-O:dirspell": "READLINE",
            "bash-O:extdebug": "DEBUGGER",
            "bash-O:extglob": "EXTENDED_GLOB",
            "bash-O:force_fignore": "READLINE",
            "bash-O:histappend": "HISTORY",
            "bash-O:histreedit": "READLINE",
            "bash-O:histverify": "READLINE",
            "bash-O:hostcomplete": "READLINE",
            "bash-O:lithist": "HISTORY",
            "bash-O:no_empty_cmd_completion": "READLINE",
            "bash-O:progcomp": "PROGRAMMABLE_COMPLETION",
            "bash-O:progcomp_alias": "PROGRAMMABLE_COMPLETION && ALIAS",
            "bash-O:restricted_shell": "RESTRICTED_SHELL",
            "bash-O:syslog_history": "SYSLOG_HISTORY && SYSLOG_SHOPT",
            "bash-o-cygwin:igncr": "__CYGWIN__",
            "bash-O-cygwin:completion_strip_exe": "__CYGWIN__",
        }
        actual = {
            record_id: record["condition"]
            for record_id, record in by_id.items()
            if record["shell"] != "powershell" and record.get("condition")
        }
        self.assertEqual(expected, actual)
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
        malformed = copy.deepcopy(self.profiles)
        malformed["groups"][8]["id"] = "zsh-renamed"
        with self.assertRaises(ValueError):
            oracle.validate(malformed, self.sources)
        malformed = copy.deepcopy(self.profiles)
        split = copy.deepcopy(malformed["groups"][1])
        malformed["groups"][1]["names"] = ["init-file"]
        split["names"] = ["rcfile"]
        malformed["groups"].append(split)
        with self.assertRaises(ValueError):
            oracle.validate(malformed, self.sources)
        malformed = copy.deepcopy(self.profiles)
        malformed["groups"][7]["source"] = "dash-0.5.13.5-options"
        with self.assertRaises(ValueError):
            oracle.validate(malformed, self.sources)
        malformed_sources = copy.deepcopy(self.sources)
        malformed_sources["sources"]["gnu-bash-5.2.37-shell"].pop("sha256")
        with self.assertRaises(ValueError):
            oracle.validate(self.profiles, malformed_sources)
        for label, source_id, mutate in (
            ("missing Git-for-Windows condition", "gfw-bash-5.3.015-cygwin", lambda source: source.pop("condition")),
            ("missing Git-for-Windows derivation", "gfw-bash-5.3.015-cygwin", lambda source: source.pop("derivation")),
            ("missing Debian derivation", "debian-dash-0.5.12-2", lambda source: source.pop("derivation")),
            ("changed Git-for-Windows derivation", "gfw-bash-5.3.015-cygwin", lambda source: source.__setitem__("derivation", "other")),
            ("malformed Debian derivation", "debian-dash-0.5.12-2", lambda source: source.__setitem__("derivation", [])),
            ("unexpected GNU condition", "gnu-bash-5.2.37-shell", lambda source: source.__setitem__("condition", "__CYGWIN__")),
        ):
            with self.subTest(label=label):
                malformed_sources = copy.deepcopy(self.sources)
                mutate(malformed_sources["sources"][source_id])
                with self.assertRaises(ValueError):
                    oracle.validate(self.profiles, malformed_sources)
        for label, index, mutate in (
            ("array id", 0, lambda group: group.__setitem__("id", [])),
            ("nested names", 0, lambda group: group.__setitem__("names", [["debug"]])),
            ("non-object map", 0, lambda group: group.__setitem__("map", [])),
            ("invalid condition", 0, lambda group: group.__setitem__("condition", [])),
            ("invalid variants", 0, lambda group: group.__setitem__("variants", [])),
            ("letter group names", 9, lambda group: group.update(names=["wrong"], map={})),
        ):
            with self.subTest(label=label):
                malformed = copy.deepcopy(self.profiles)
                mutate(malformed["groups"][index])
                with self.assertRaises(ValueError):
                    oracle.validate(malformed, self.sources)
        malformed = copy.deepcopy(self.profiles)
        malformed["groups"][9]["map"]["0"] = 1
        with self.assertRaises(ValueError):
            oracle.validate(malformed, self.sources)
        powershell_index = next(index for index, group in enumerate(self.profiles["groups"]) if group["id"] == "powershell-descriptors")
        for label, mutate in (
            ("missing descriptor", lambda group: group["descriptors"].pop()),
            ("reordered descriptor", lambda group: group["descriptors"].reverse()),
            ("lost condition", lambda group: group["conditions"].pop("isswait")),
            ("incorrect condition", lambda group: group["conditions"].__setitem__("token", ["UNIX"])),
            ("incorrect alias", lambda group: group["aliases"].__setitem__("ec", "command")),
            ("bad arity", lambda group: group["descriptors"][20].__setitem__("arity", 1)),
            ("bad action", lambda group: group["descriptors"][22].__setitem__("action", "continue")),
            ("wrong source location", lambda group: group["source_lines"].__setitem__("command", 1055)),
            ("missing immutable documentation metadata", lambda group: group["windows_extra"][0].pop("source")),
        ):
            with self.subTest(label=label):
                malformed = copy.deepcopy(self.profiles)
                mutate(malformed["groups"][powershell_index])
                with self.assertRaises(ValueError):
                    oracle.validate(malformed, self.sources)
        for label, source_id, mutate in (
            ("wrong parser provenance", "pwsh-7.6.0-parser", lambda source: source.__setitem__("provenance", "verified")),
            ("lost normalized hash", "pwsh-7.6.0-parser", lambda source: source.pop("normalized_lf_sha256")),
            ("collapsed raw and normalized hashes", "pwsh-7.6.0-parser", lambda source: source.__setitem__("normalized_lf_sha256", source["sha256"])),
            ("falsely asserted parser revision", "pwsh-7.6.0-parser", lambda source: source.__setitem__("revision", "f" * 40)),
            ("missing immutable documentation metadata", "pwsh-7.5-cli-doc", lambda source: source.pop("revision")),
            ("wrong documentation locations", "windows-powershell-5.1-cli-doc", lambda source: source["locations"][0].__setitem__(0, 26)),
        ):
            with self.subTest(label=label):
                malformed_sources = copy.deepcopy(self.sources)
                mutate(malformed_sources["sources"][source_id])
                with self.assertRaises(ValueError):
                    oracle.validate(self.profiles, malformed_sources)


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
