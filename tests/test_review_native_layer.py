"""The review family names each host's real native reviewer and runs in a repository with no `.agents/`.

A simulated `native-general` event passes whatever the procedure says, so it cannot catch a Stage 3 that
names no reviewer. These checks read the shipped procedure itself and run its helpers from the packaged
plugin against a consumer-shaped repository.
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".agents" / "engineering" / "workflow"
PACKAGE = ROOT / "plugins" / "engineering"
REVIEW_FAMILY = ("review", "incremental-review", "big-review", "big-review-all", "docs-review", "address-review")
DELEGATES_NATIVE_LAYER = ("incremental-review", "big-review", "docs-review")


def body(skill):
    return (WORKFLOW / skill / "SKILL.md").read_text(encoding="utf-8")


def section(text, heading):
    start = text.index(heading)
    following = text.find("\n## ", start + len(heading))
    return text[start:] if following == -1 else text[start:following]


class NativeLayerNamesTheHostReviewer(unittest.TestCase):
    def test_stage_three_names_claude_code_review_and_codex_review(self):
        stage = section(body("review"), "## Stage 3")

        self.assertIn("built-in `code-review` skill", stage)
        self.assertIn("Skill tool", stage)
        self.assertIn("`codex review --base <frozen-base>`", stage)
        self.assertIn("reading the diff yourself is not this layer", stage)
        self.assertIn("`native-general`", stage)

    def test_stage_six_names_claude_security_review(self):
        self.assertIn("built-in `security-review` skill", section(body("review"), "## Stage 6"))

    def test_every_mode_with_a_native_layer_delegates_to_stage_three(self):
        for skill in DELEGATES_NATIVE_LAYER:
            with self.subTest(skill=skill):
                text = body(skill)
                self.assertIn("`review` Stage 3 native layer", text)
                self.assertNotIn("native/general layer over", text)
                self.assertNotIn("native/general review receives", text)

    def test_the_packaged_procedure_is_the_authored_one(self):
        for skill in ("review", *DELEGATES_NATIVE_LAYER):
            with self.subTest(skill=skill):
                packaged = PACKAGE / ".agents" / "engineering" / "workflow" / skill / "SKILL.md"
                self.assertEqual(body(skill), packaged.read_text(encoding="utf-8"))


class ReviewRunsWithoutRepositoryHelpers(unittest.TestCase):
    def test_no_review_family_step_runs_a_helper_from_the_reviewed_repository(self):
        lifecycle = ROOT / ".agents" / "engineering" / "contract" / "review-lifecycle" / "SKILL.md"
        texts = {skill: body(skill) for skill in REVIEW_FAMILY}
        texts["review-lifecycle"] = lifecycle.read_text(encoding="utf-8")
        for skill, text in texts.items():
            with self.subTest(skill=skill):
                self.assertIsNone(re.search(r"python(?: -B)? (?!<engineering>/)\S+\.py", text))
                self.assertIsNone(re.search(r"(?<!<engineering>/workflows/)workflow_ops\.py", text))

    def test_every_engineering_helper_the_review_names_is_shipped(self):
        named = set()
        for skill in (*REVIEW_FAMILY, "review-lifecycle"):
            path = next((ROOT / ".agents" / "engineering").rglob(f"{skill}/SKILL.md"))
            named.update(re.findall(r"<engineering>/([\w./-]+\.py)", path.read_text(encoding="utf-8")))

        self.assertIn("workflows/workflow_ops.py", named)
        self.assertIn("hooks/tier_gate.py", named)
        for relative in named:
            with self.subTest(helper=relative):
                self.assertTrue((PACKAGE / relative).is_file())


class ConsumerRepositoryAcceptance(unittest.TestCase):
    """Stages 1 and 4 from a relocated package, in a repository shaped like cris-authz."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="consumer review ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.package = self.root / "installed engineering"
        shutil.copytree(PACKAGE, self.package)
        self.repository = self.root / "cris-authz"
        self.repository.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("remote", "add", "origin", "https://github.com/Infonetica/cris-authz.git")
        (self.repository / "global.json").write_text("{}\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "base")
        self.git("checkout", "-q", "-b", "fix-prod-boot")
        source = self.repository / "src" / "Authorization"
        source.mkdir(parents=True)
        (source / "Startup.cs").write_text("class Startup {}\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "change")
        self.environment = {key: value for key, value in os.environ.items()
                            if key not in ("CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT", "CODEX_PLUGIN_ROOT")}
        self.environment["PYTHONIOENCODING"] = "utf-8"

    def git(self, *arguments):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *arguments],
            cwd=self.repository, check=True, capture_output=True,
        )

    def run_packaged(self, relative, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(self.package / relative), *arguments],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8",
            env=self.environment, timeout=60,
        )

    def test_stage_one_prepares_the_candidate_with_no_repository_runtime(self):
        self.assertFalse((self.repository / ".agents").exists())

        completed = self.run_packaged(
            "workflows/workflow_ops.py", "--root", str(self.repository),
            "--workflow-run-id", "consumer-review", "review-prepare", "--base", "main", "--head", "HEAD",
        )

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        descriptor = json.loads(completed.stdout)
        self.assertEqual("Infonetica/cris-authz", descriptor["repository"])
        self.assertEqual(["src/Authorization/Startup.cs"], descriptor["paths"])
        self.assertEqual([], descriptor["rules"])
        self.assertEqual(
            {"required": True, "first_path": "src/Authorization/Startup.cs"}, descriptor["security"]
        )
        self.assertTrue(Path(descriptor["bundle"]["tree"]).is_dir())

    def test_stage_four_resolves_tier_conventions_from_the_plugin(self):
        completed = self.run_packaged(
            "hooks/tier_gate.py", "--conventions", "--project", str(self.repository),
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(completed.stdout.startswith("Tier gate - "), completed.stdout)


if __name__ == "__main__":
    unittest.main()
