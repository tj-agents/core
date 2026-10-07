import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tier_gate_remote_host", ROOT / ".agents/hooks/tier_gate.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class RemoteHost(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True, capture_output=True)

    def origin(self, url):
        subprocess.run(["git", "-C", str(self.root), "config", "remote.origin.url", url], check=True, capture_output=True)

    def matches(self, host="github.com"):
        return gate.evaluate_predicate(self.root, {"remote_host": host})

    def test_real_git_network_origins_match_exact_normalized_hostname(self):
        for url in ("https://github.com/owner/repo.git", "https://GITHUB.COM./owner/repo.git",
                    "ssh://git@github.com/owner/repo.git", "ssh://git@GITHUB.COM:2222/owner/repo.git",
                    "git@github.com:owner/repo.git", "git@github.com:/owner/repo.git", "git@GITHUB.COM.:owner/repo.git"):
            with self.subTest(url=url):
                self.origin(url)
                self.assertEqual(gate.repository_host(self.root), "github.com")
                result = self.matches("GitHub.COM.")
                self.assertTrue(result.matched)
                self.assertEqual(result.evidence, ("origin host github.com",))
                self.assertEqual(result.diagnostics, ())

    def test_lookalike_hosts_and_wrong_host_never_match(self):
        for host in ("github.com.evil", "evilgithub.com", "github-com.test", "other.example"):
            for url in (f"https://{host}/owner/repo.git", f"git@{host}:owner/repo.git"):
                with self.subTest(url=url):
                    self.origin(url)
                    self.assertFalse(self.matches().matched)
                    self.assertEqual(self.matches().evidence, ())
        self.origin("https://github.com@evil.test/owner/repo.git")
        self.assertFalse(self.matches().matched)

    def test_local_file_and_malformed_origin_shapes_do_not_supply_hostname(self):
        for url in ("", "../owner/repo.git", "/owner/repo.git", "C:/owner/repo.git",
                    "C:\\owner\\repo.git", "file:///github.com/owner/repo.git", "file://github.com/owner/repo.git",
                    "github.com/owner/repo.git", "github.com:owner/repo.git", "https:///owner/repo.git",
                    "https://github.com", " https://github.com/owner/repo.git", "https://github.com/owner/repo.git ",
                    "ssh://git@github.com/", "https://github.com:/owner/repo.git", "https://github.com:bad/owner/repo.git",
                    "https://github.com:70000/owner/repo.git", "https://github.com:0/owner/repo.git",
                    "https://github.com/owner/repo.git?host=evil", "https://github.com/owner/repo.git#fragment",
                    "https://github.com/owner/repo.git?", "https://github.com/owner/repo.git#",
                    "https://github.com/owner/../repo.git", "https://github.com/owner//repo.git",
                    "https://github.com./owner/ repo.git", "https://github..com/owner/repo.git",
                    "https://%67ithub.com/owner/repo.git", "https://[github.com/owner/repo.git",
                    "ftp://github.com/owner/repo.git", "git@@github.com:owner/repo.git"):
            with self.subTest(url=url):
                self.origin(url)
                self.assertIsNone(gate.repository_host(self.root))
                self.assertFalse(self.matches().matched)
        for url in ("https://github.com/owner/repo.git\nsecond", "https://github.com/owner/repo.git\x00"):
            with patch.object(gate, "_git", return_value=url):
                self.assertIsNone(gate.repository_host(self.root))

    def test_no_origin_git_failure_and_timeout_are_nonmatches(self):
        self.assertIsNone(gate.repository_host(self.root))
        self.assertFalse(self.matches().matched)
        for error in (OSError("no git"), subprocess.TimeoutExpired("git", gate.GIT_TIMEOUT)):
            with patch.object(gate.subprocess, "run", side_effect=error):
                self.assertFalse(self.matches().matched)
        with patch.object(gate, "_git", return_value=None):
            self.assertFalse(self.matches().matched)

    def test_exact_host_predicate_parser_and_schema_reject_patterns_and_urls(self):
        schema = json.loads((ROOT / ".agents/schemas/tier.schema.json").read_text(encoding="utf-8"))
        shape = next(item for item in schema["$defs"]["predicate"]["oneOf"] if "remote_host" in item["properties"])
        pattern = shape["properties"]["remote_host"]["pattern"]
        self.assertFalse(shape["additionalProperties"])
        self.assertEqual(shape["required"], ["remote_host"])
        for value in ("github.com", "GITHUB.COM.", "git.internal", "localhost", "127.0.0.1"):
            self.assertEqual(gate.predicate_diagnostics({"remote_host": value}), [])
            self.assertIsNotNone(re.search(pattern, value))
        for value in ("", " ", "*.github.com", "^github.com$", "github.com:22", "https://github.com",
                      "github.com/path", "github..com", "-github.com", "github-.com", "github.com\n", "x" * 64 + ".test"):
            with self.subTest(value=value):
                self.assertTrue(gate.predicate_diagnostics({"remote_host": value}))
                self.assertIsNone(re.search(pattern, value))
        for value in (None, [], {}):
            self.assertTrue(gate.predicate_diagnostics({"remote_host": value}))
        self.assertTrue(gate.predicate_diagnostics({"remote_host": "github.com", "remote": "^owner/"}))

    def test_legacy_remote_still_matches_owner_repository_without_host_restriction(self):
        self.origin("git@other.example:owner/repo.git")
        self.assertEqual(gate.repository_identity(self.root), "owner/repo")
        self.assertTrue(gate.evaluate_predicate(self.root, {"remote": "^owner/"}).matched)
        self.assertFalse(self.matches().matched)
        matched, evidence = gate.stack_present(self.root, {"remote": ["^owner/"]})
        self.assertTrue(matched)
        self.assertEqual(evidence, "origin owner/repo")


if __name__ == "__main__":
    unittest.main()
