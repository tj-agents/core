"""Synthetic Claude and Codex profiles only; native removals go to a command double."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/machine/scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("legacy_marketplaces", SCRIPTS / "legacy_marketplaces.py")
LEGACY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LEGACY)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")


class Profiles:
    def __init__(self, test):
        temporary = tempfile.TemporaryDirectory(prefix="legacy marketplaces ")
        test.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.claude, self.codex, self.project = self.root / "claude", self.root / "codex", self.root / "project"
        self.project.mkdir()
        for patcher in (mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.claude),
                                                     "CODEX_HOME": str(self.codex)}),
                        mock.patch.object(LEGACY.plugin_autoupdate.tempfile, "gettempdir",
                                          return_value=str(self.root / "tmp"))):
            patcher.start()
            test.addCleanup(patcher.stop)
        self.known = {}

    def claude_marketplace(self, name, repository, plugins):
        location = self.root / "markets" / name
        write(location / ".claude-plugin/marketplace.json", {"plugins": [{"name": plugin} for plugin in plugins]})
        self.known[name] = {"source": {"source": "github", "repo": repository}, "installLocation": str(location)}
        write(self.claude / "plugins/known_marketplaces.json", self.known)

    def codex_catalog(self, name, plugins):
        write(self.codex / ".tmp/marketplaces" / name / ".agents/plugins/marketplace.json",
              {"plugins": [{"name": plugin} for plugin in plugins]})


class ClaudeTests(unittest.TestCase):
    def test_overlapping_plugin_names_do_not_make_other_publishers_superseded(self):
        profiles = Profiles(self)
        profiles.claude_marketplace("tj-agents", "tj-agents/marketplace", ["python"])
        profiles.claude_marketplace("agents", "Concertable/agents", ["python"])
        profiles.claude_marketplace("other-agents", "tomjseery/other-agents", ["python"])
        run = mock.Mock()
        self.assertEqual(([], []), LEGACY.review("claude", profiles.project, lambda: "claude", run))
        run.assert_not_called()

    def test_unused_superseded_registrations_are_removed_and_used_ones_reported(self):
        profiles = Profiles(self)
        profiles.claude_marketplace("tj-agents", "tj-agents/marketplace", ["base", "python", "infonetica", "azure"])
        profiles.claude_marketplace("python-agents", "tj-agents/python-agents", ["python"])
        profiles.claude_marketplace("infonetica", "tj-agents/infonetica", ["infonetica"])
        profiles.claude_marketplace("claude-plugins-official", "anthropics/claude-plugins-official", ["azure"])
        profiles.claude_marketplace("agents", "Concertable/agents", ["concertable"])
        write(profiles.project / ".claude/settings.local.json", {"enabledPlugins": {"infonetica@infonetica": True}})
        run = mock.Mock(return_value="")

        removed, problems = LEGACY.review("claude", profiles.project, lambda: "claude", run)

        self.assertEqual(["claude:python-agents"], removed)
        run.assert_called_once_with(["claude", "plugin", "marketplace", "remove", "python-agents"], profiles.project)
        self.assertEqual(1, len(problems))
        self.assertIn("legacy marketplace infonetica (claude) is still used by infonetica@infonetica", problems[0])
        self.assertIn("infonetica@infonetica -> infonetica@tj-agents", problems[0])

    def test_an_installed_superseded_plugin_keeps_its_registration_and_is_reported(self):
        profiles = Profiles(self)
        profiles.claude_marketplace("tj-agents", "tj-agents/marketplace", ["work"])
        profiles.claude_marketplace("work-agents", "tj-agents/work", ["work"])
        write(profiles.claude / "plugins/installed_plugins.json",
              {"plugins": {"work@work-agents": [{"scope": "local", "projectPath": "C:/elsewhere"}]}})
        run = mock.Mock()

        removed, problems = LEGACY.review("claude", profiles.project, lambda: "claude", run)

        self.assertEqual([], removed)
        run.assert_not_called()
        self.assertIn("work-agents (claude) is still used by work@work-agents", problems[0])

    def test_a_project_declaration_of_a_superseded_marketplace_names_its_file(self):
        profiles = Profiles(self)
        profiles.claude_marketplace("tj-agents", "tj-agents/marketplace", ["python"])
        write(profiles.project / ".claude/settings.json", {
            "extraKnownMarketplaces": {"python-agents": {"source": {"source": "github", "repo": "tj-agents/python"}}},
            "enabledPlugins": {"python@python-agents": True}})

        removed, problems = LEGACY.review("claude", profiles.project, lambda: "claude", mock.Mock())

        self.assertEqual([], removed)
        self.assertEqual([f"legacy marketplace python-agents is declared in {profiles.project / '.claude/settings.json'}; "
                          "remove it and switch python@python-agents -> python@tj-agents"], problems)

    def test_nothing_is_judged_without_the_canonical_catalog(self):
        profiles = Profiles(self)
        profiles.claude_marketplace("python-agents", "tj-agents/python-agents", ["python"])
        run = mock.Mock()

        self.assertEqual(([], []), LEGACY.review("claude", profiles.project, lambda: "claude", run))
        run.assert_not_called()


class CodexTests(unittest.TestCase):
    def test_user_registrations_are_removed_only_when_unused_and_project_declarations_are_reported(self):
        profiles = Profiles(self)
        profiles.codex_catalog("tj-agents", ["base", "python", "work", "infonetica"])
        profiles.codex_catalog("agents", ["concertable"])
        project = profiles.root / "infonetica-app"
        write(project / ".codex/config.toml", '[marketplaces.python-agents]\nsource_type = "git"\n'
                                               'source = "https://github.com/tj-agents/python.git"\n'
                                               '[plugins."python@python-agents"]\nenabled = true\n')
        write(profiles.codex / "config.toml",
              '[marketplaces.agents]\nsource_type = "git"\nsource = "https://github.com/Concertable/agents.git"\n'
              '[marketplaces.work-agents]\nsource_type = "git"\nsource = "https://github.com/tj-agents/work.git"\n'
              '[marketplaces.infonetica]\nsource_type = "git"\nsource = "https://github.com/tj-agents/infonetica.git"\n'
              '[plugins."concertable@agents"]\nenabled = true\n'
              '[plugins."infonetica@infonetica"]\nenabled = true\n'
              f'[projects.{json.dumps(str(project.resolve()))}]\ntrust_level = "trusted"\n')
        profiles.codex_catalog("work-agents", ["work"])
        run = mock.Mock(return_value="")

        removed, problems = LEGACY.review("codex", profiles.project, lambda: "codex", run)

        self.assertEqual(["codex:work-agents"], removed)
        run.assert_called_once_with(["codex", "plugin", "marketplace", "remove", "work-agents"], profiles.project)
        self.assertEqual(2, len(problems))
        self.assertIn(f"python-agents is declared in {project.resolve() / '.codex/config.toml'}", problems[0])
        self.assertIn("python@python-agents -> python@tj-agents", problems[0])
        self.assertIn("infonetica (codex) is still used by infonetica@infonetica", problems[1])


if __name__ == "__main__":
    unittest.main()
