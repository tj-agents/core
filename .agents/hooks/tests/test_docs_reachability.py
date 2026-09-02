import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docs_reachability import repository_report


class DocsReachabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_clean_chain_has_no_errors(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "Conventions: @./agents/CODE_CONVENTIONS.md\n")
        self.write("agents/CODE_CONVENTIONS.md", "# Conventions\n")

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])

    def test_plain_link_reference_counts_as_reachable(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "See [rules](./agents/RULES.md).\n")
        self.write("agents/RULES.md", "# Rules\n")

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])

    def test_skill_reference_counts_as_reachable(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write(".agents/skills/thing/SKILL.md", "See [rules](../../../agents/RULES.md).\n")
        self.write("agents/RULES.md", "# Rules\n")

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])

    def test_agents_md_without_claude_sibling_is_an_error(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write("app/AGENTS.md", "@./agents/CODE_CONVENTIONS.md\n")
        self.write("app/agents/CODE_CONVENTIONS.md", "# Conventions\n")

        report = repository_report(self.root)

        self.assertTrue(any("app/AGENTS.md" in error and "sibling CLAUDE.md" in error for error in report["errors"]))

    def test_claude_md_with_wrong_body_is_an_error(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write("app/AGENTS.md", "# App\n")
        self.write("app/CLAUDE.md", "Some other content\n")

        report = repository_report(self.root)

        self.assertTrue(any("app/CLAUDE.md" in error and "must contain exactly" in error for error in report["errors"]))

    def test_unreferenced_agents_doc_is_an_orphan(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root, no mention of the doc below\n")
        self.write("agents/ORPHAN.md", "# Nobody points at me\n")

        report = repository_report(self.root)

        self.assertTrue(any("agents/ORPHAN.md" in error and "not reachable" in error for error in report["errors"]))

    def test_plugin_agent_registered_by_host_manifest_is_reachable(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write("plugins/example/agents/workflow-reader.md", "# Reader\n")
        manifest = {
            "delivery": {"plugin_directory": "agents"},
            "roles": {"reader": {"filename": "workflow-reader.md"}},
        }
        self.write(
            "plugins/example/workflows/hosts/claude.json",
            json.dumps(manifest),
        )

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])

    def test_plugin_agent_manifest_cannot_register_a_doc_outside_its_plugin(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write("agents/ORPHAN.md", "# Orphan\n")
        manifest = {
            "delivery": {"plugin_directory": "agents"},
            "roles": {"reader": {"filename": "../../../agents/ORPHAN.md"}},
        }
        self.write(
            "plugins/example/workflows/hosts/claude.json",
            json.dumps(manifest),
        )

        report = repository_report(self.root)

        self.assertTrue(
            any("agents/ORPHAN.md" in error and "not reachable" in error for error in report["errors"])
        )

    def test_reachability_follows_links_transitively_through_a_loaded_doc(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "@./agents/CODE_PATTERNS.md\n")
        self.write("agents/CODE_PATTERNS.md", "See [companion](./MICROSERVICE_COMMUNICATION.md).\n")
        self.write("agents/MICROSERVICE_COMMUNICATION.md", "# Communication\n")

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])

    def test_dot_agents_directory_is_excluded_from_the_orphan_scan(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write(".agents/hooks/some_module.md", "# Not a doc-chain target\n")

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])

    def test_guidance_doc_linking_a_missing_file_is_an_error(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "See [the audit](./plans/DELETED_AUDIT.md).\n")

        report = repository_report(self.root)

        self.assertTrue(
            any("DELETED_AUDIT.md" in error and "does not exist" in error for error in report["errors"])
        )

    def test_a_reachable_doc_can_still_carry_a_dead_link(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "@./agents/CODE_CONVENTIONS.md\n")
        self.write("agents/CODE_CONVENTIONS.md", "Rationale: [why](./GONE.md).\n")

        report = repository_report(self.root)

        self.assertTrue(any("GONE.md" in error for error in report["errors"]))

    def test_root_absolute_reference_is_an_error_even_though_it_resolves(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "See [north star](/api/docs/NORTH_STAR.md).\n")

        report = repository_report(self.root)

        self.assertTrue(any("root-absolute" in error for error in report["errors"]))

    def test_working_docs_dead_links_warn_rather_than_fail_the_gate(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write("plans/epic/A_PLAN.md", "Ledger: [progress](./A_PROGRESS.md).\n")
        self.write("reviews/Feature-X.md", "See [finding](./gone.md).\n")

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])
        self.assertEqual(2, len(report["warnings"]))

    def test_test_project_without_an_agents_md_is_an_error(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write(
            "api/Svc/tests/Svc.UnitTests/Svc.UnitTests.csproj",
            "<Project><PropertyGroup><IsTestProject>true</IsTestProject></PropertyGroup></Project>\n",
        )

        report = repository_report(self.root)

        self.assertEqual(1, len(report["errors"]))
        self.assertIn("Svc.UnitTests.csproj", report["errors"][0])

    def test_test_project_with_the_stub_pair_is_clean(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write(
            "api/Svc/tests/Svc.UnitTests/Svc.UnitTests.csproj",
            "<Project><PropertyGroup><IsTestProject>true</IsTestProject></PropertyGroup></Project>\n",
        )
        self.write("api/Svc/tests/Svc.UnitTests/AGENTS.md", "# Svc.UnitTests\n")
        self.write("api/Svc/tests/Svc.UnitTests/CLAUDE.md", "@AGENTS.md\n")

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])

    def test_a_support_library_is_not_held_to_the_test_project_rule(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("AGENTS.md", "# Root\n")
        self.write(
            "api/Svc/tests/Svc.Fixtures/Svc.Fixtures.csproj",
            "<Project><PropertyGroup><IsTestProject>false</IsTestProject></PropertyGroup></Project>\n",
        )

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])

    def test_link_like_text_inside_a_fenced_block_is_not_a_reference(self):
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write(
            "AGENTS.md",
            "# Root\n\n```bash\ngrep -viE \"[/\\\\](bin|obj)[/\\\\]\"\n```\n",
        )

        report = repository_report(self.root)

        self.assertEqual([], report["errors"])


if __name__ == "__main__":
    unittest.main()
