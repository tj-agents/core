import importlib.util
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ".agents" / "hooks" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("tier_gate")
checker = load("check_tier_payload")


class Predicates(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)
        (self.root / "project.csproj").write_text("<Project />", encoding="utf-8")

    def test_nested_positive_composition_requires_every_conjunct(self):
        node = {"all": [{"glob": "*.csproj"}, {"any": [{"file": "adopted.json"}, {"file": "other.json"}]}]}
        self.assertFalse(gate.evaluate_predicate(self.root, node).matched)
        (self.root / "adopted.json").write_text("{}", encoding="utf-8")
        result = gate.evaluate_predicate(self.root, node)
        self.assertTrue(result.matched)
        self.assertEqual(result.scope, str(self.root))
        self.assertEqual(result.evidence, ("project.csproj", "adopted.json"))

    def test_unknown_branch_cannot_be_hidden_by_a_matching_alternative(self):
        node = {"any": [{"file": "project.csproj"}, {"fact": "technology.unknown"}]}
        result = gate.evaluate_predicate(self.root, node)
        self.assertFalse(result.matched)
        self.assertEqual(result.diagnostics[0]["code"], "unknown-fact")
        self.assertEqual(result.diagnostics[0]["path"], "detect.any[1]")

    def test_invalid_member_is_diagnosed_even_when_another_member_matches(self):
        for invalid in ({"all": []}, {"not": {"file": "x"}}, {"file": "x", "glob": "*"},
                        {"remote": "["}, {"content": {"glob": "*", "pattern": "["}},
                        {"context": {"key": "house", "equals": "tommy", "contains": "tommy"}}):
            with self.subTest(invalid=invalid):
                result = gate.evaluate_predicate(self.root, {"any": [{"file": "project.csproj"}, invalid]})
                self.assertFalse(result.matched)
                self.assertTrue(result.diagnostics)

    def test_fact_results_preserve_evidence_and_require_the_same_scope(self):
        fact = gate.PredicateResult(self.root, True, ["project.csproj"])
        result = gate.evaluate_predicate(self.root, {"fact": "language.dotnet"}, {"language.dotnet": fact})
        self.assertTrue(result.matched)
        self.assertEqual(result.prerequisites, ("language.dotnet",))
        self.assertEqual(result.evidence, ("project.csproj",))
        unrelated = gate.PredicateResult(self.root / "other", True, ["other.csproj"])
        result = gate.evaluate_predicate(self.root, {"fact": "language.dotnet"}, {"language.dotnet": unrelated})
        self.assertFalse(result.matched)
        self.assertEqual(result.diagnostics[0]["code"], "invalid-fact")

    def test_context_equality_membership_and_unknowns(self):
        contexts = {"house.dotnet": "tommy", "architecture": ["capability-repositories"]}
        for value in ({"key": "house.dotnet", "equals": "tommy"},
                      {"key": "architecture", "contains": "capability-repositories"}):
            self.assertTrue(gate.evaluate_predicate(self.root, {"context": value}, contexts=contexts).matched)
        result = gate.evaluate_predicate(self.root, {"context": {"key": "unknown", "equals": "tommy"}}, contexts=contexts)
        self.assertEqual(result.diagnostics[0]["code"], "unknown-context")
        result = gate.evaluate_predicate(self.root, {"context": {"key": "house.dotnet", "contains": "tommy"}}, contexts=contexts)
        self.assertEqual(result.diagnostics[0]["code"], "invalid-context")

    def test_content_and_remote_primitives(self):
        result = gate.evaluate_predicate(self.root, {"content": {"glob": "*.csproj", "pattern": "Project"}})
        self.assertTrue(result.matched)
        self.assertFalse(gate.evaluate_predicate(self.root, {"remote": "^infonetica/"}).matched)

    def test_v3_selection_exposes_shared_results(self):
        data = {"schema_version": 3, "tier": "example", "applies": "stack-present",
                "detect": {"all": [{"glob": "*.csproj"}, {"file": "project.csproj"}]}}
        declaration = gate.Declaration("example", "test", data)
        result = gate.assess(self.root, [declaration])
        self.assertEqual([item.id for item, _ in result.applicable], ["example@test"])
        self.assertEqual(result.selections[0]["scope"], str(self.root))
        self.assertEqual(result.selections[0]["evidence"], ("project.csproj",))
        self.assertEqual(result.diagnostics, ())

    def test_v3_force_and_owner_identity_do_not_establish_governing_selection(self):
        data = {"schema_version": 3, "tier": "example", "applies": "stack-present",
                "owner_repository": "tj-agents/example", "detect": {"file": "missing"}}
        declaration = gate.Declaration("example", "test", data)
        with patch.dict(gate.os.environ, {gate.OVERRIDE_VARIABLE: "example"}), \
                patch.object(gate, "repository_identity", return_value="tj-agents/example"):
            result = gate.assess(self.root, [declaration])
        self.assertEqual(result.applicable, [])
        self.assertEqual(result.blocked, [declaration])
        self.assertNotIn(gate.OVERRIDE_VARIABLE, gate.refusal(declaration, "example", self.root))

    def test_review_and_session_report_unknown_configuration(self):
        declaration = gate.Declaration("example", "test", {
            "schema_version": 3, "tier": "example", "applies": "stack-present", "detect": {"fact": "unknown"}})
        for output in (gate.statement(self.root, [declaration]), gate.conventions(self.root, [declaration])):
            self.assertIn("Configuration diagnostic", output)
            self.assertIn("Provide scoped evidence for fact: unknown", output)

    def test_discovery_reports_version_and_parse_failures(self):
        for name, body in (("future", json.dumps({"schema_version": 99})), ("broken", "{")):
            payload = self.root / name / name / "1"
            payload.mkdir(parents=True)
            (payload / "tier.json").write_text(body, encoding="utf-8")
        diagnostics = []
        found = gate.declarations([self.root], diagnostics=diagnostics)
        self.assertEqual([item.id for item in found], ["broken@broken", "future@future"])
        self.assertTrue(all(item.diagnostics for item in found))
        self.assertEqual([item["code"] for item in diagnostics], ["unreadable-declaration", "unsupported-version"])


    def install(self, plugin, body):
        cache = self.root / "config" / "plugins" / "cache"
        payload = cache / "test-market" / plugin / "1"
        skill = payload / "skills" / "rule"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: rule\nkind: convention\n---\n", encoding="utf-8")
        if body is not None:
            (payload / "tier.json").write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
        registry_path = cache.parent / "installed_plugins.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {"plugins": {}}
        registry["plugins"][plugin + "@test-market"] = [{"installPath": str(payload)}]
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        return cache, payload

    def hook_payloads(self, plugin, payload):
        return ({"cwd": str(self.root), "tool_name": "Skill", "tool_input": {"skill": plugin + ":rule"}},
                {"cwd": str(self.root), "tool_name": "PowerShell",
                 "tool_input": {"command": "Get-Content '" + str(payload / "skills" / "rule" / "SKILL.md") + "'"}})

    def test_invalid_installed_declarations_block_both_hook_paths(self):
        valid = {"schema_version": 3, "tier": "invalid", "applies": "stack-present", "detect": {"all": []}}
        for body in (valid, dict(valid, detect={"not": {"file": "project.csproj"}}),
                     dict(valid, owner_repository=17), dict(valid, schema_version=99), "{", []):
            with self.subTest(body=body):
                plugin = "invalid" + str(len(list((self.root / "config").glob("**/tier.json"))))
                cache, payload = self.install(plugin, body)
                with patch.object(gate, "cache_roots", return_value=[cache]):
                    result = gate.assess(self.root)
                    selection = next(item for item in result.selections if item["plugin_id"] == plugin + "@test-market")
                    self.assertFalse(selection["matched"])
                    self.assertTrue(selection["diagnostics"])
                    for hook in self.hook_payloads(plugin, payload):
                        stderr = io.StringIO()
                        with contextlib.redirect_stderr(stderr):
                            self.assertEqual(gate.gate(hook), 2)
                        self.assertIn(str(payload / "tier.json"), stderr.getvalue())
                        self.assertIn(selection["diagnostics"][0]["message"], stderr.getvalue())

    def test_hook_diagnostics_identify_only_the_requested_plugin(self):
        for plugin, predicate, message in (("unknown-fact", {"fact": "technology.unknown"}, "Provide scoped evidence for fact"),
                                           ("unknown-context", {"context": {"key": "missing", "equals": "tommy"}}, "Provide scoped context")):
            cache, payload = self.install(plugin, {"schema_version": 3, "tier": plugin,
                                                  "applies": "stack-present", "detect": predicate})
            with patch.object(gate, "cache_roots", return_value=[cache]):
                for hook in self.hook_payloads(plugin, payload):
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        self.assertEqual(gate.gate(hook), 2)
                    self.assertIn("Configuration diagnostic for " + plugin + "@test-market: detect:", stderr.getvalue())
                    self.assertIn(message, stderr.getvalue())
                    other_message = "Provide scoped context" if plugin == "unknown-fact" else "Provide scoped evidence for fact"
                    self.assertNotIn(other_message, stderr.getvalue())

    def test_mixed_validity_keeps_every_valid_convention_and_ordinary_plugins(self):
        for version in (1, 2, 3):
            detect = {"globs": ["*.csproj"]} if version < 3 else {"glob": "*.csproj"}
            cache, _ = self.install("valid" + str(version), {"schema_version": version, "tier": "valid" + str(version),
                                                            "applies": "stack-present", "detect": detect})
        self.install("invalid", {"schema_version": 3, "tier": "invalid", "applies": "stack-present", "detect": {"all": []}})
        self.install("unknown", {"schema_version": 3, "tier": "unknown", "applies": "stack-present", "detect": {"fact": "missing"}})
        _, ordinary = self.install("ordinary", None)
        with patch.object(gate, "cache_roots", return_value=[cache]):
            result = gate.assess(self.root)
            self.assertEqual([item.plugin for item, _ in result.applicable], ["valid1", "valid2", "valid3"])
            self.assertNotIn("ordinary", [item.plugin for item in result.blocked])
            listing = gate.conventions(self.root)
            self.assertIn("Configuration diagnostic", listing)
            self.assertIn("Provide scoped evidence for fact: missing", listing)
            for version in (1, 2, 3):
                self.assertIn("valid" + str(version) + " (", listing)
            self.assertEqual(listing.count("  rule - "), 3)
            for hook in self.hook_payloads("ordinary", ordinary):
                self.assertEqual(gate.gate(hook), 0)
            diagnostics = []
            gate.declarations([cache], diagnostics=diagnostics)
            self.assertFalse(any("ordinary" in item["path"] for item in diagnostics))

    def test_payload_checker_accepts_v3_and_rejects_invalid_composition(self):
        data = {"schema_version": 3, "tier": "example", "applies": "stack-present",
                "detect": {"all": [{"fact": "language.dotnet"}, {"context": {"key": "house", "equals": "tommy"}}]}}
        path = self.root / "tier.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        problems = []
        checker.check_tier_declaration(self.root, problems)
        self.assertEqual(problems, [])
        data["detect"] = {"all": []}
        path.write_text(json.dumps(data), encoding="utf-8")
        checker.check_tier_declaration(self.root, problems)
        self.assertIn("non-empty array", problems[0])


if __name__ == "__main__":
    unittest.main()
