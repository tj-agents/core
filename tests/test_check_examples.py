import subprocess
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / ".agents/engineering/convention/docs/scripts/check_examples.py"


class ExampleCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="example checker ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Example Checker")
        self.git("config", "user.email", "examples@example.invalid")
        self.write("README.md", "base\n")
        self.commit()
        self.base = self.git("rev-parse", "HEAD").stdout.strip()

    def git(self, *arguments):
        return subprocess.run(["git", *arguments], cwd=self.root, check=True, text=True,
                              capture_output=True)

    def write(self, relative, text):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture")

    def check(self, *arguments):
        return subprocess.run(["python", "-B", str(CHECKER), "--root", str(self.root), *arguments],
                              text=True, capture_output=True)

    @staticmethod
    def skill(body):
        return "---\nname: example\n---\n" + body

    def test_added_modified_and_renamed_authored_guidance_need_real_examples(self):
        relative = ".agents/example/convention/example/SKILL.md"
        self.write(relative, self.skill("# Rule\n\n```text\nInput: source\nOutput: result\n```\n"))
        self.commit()
        self.assertEqual(0, self.check("--base", self.base).returncode)
        first = self.git("rev-parse", "HEAD").stdout.strip()

        self.write(relative, self.skill("# Rule\n\nNo demonstration.\n"))
        self.commit()
        failed = self.check("--base", first)
        self.assertEqual(1, failed.returncode)
        self.assertIn(relative, failed.stderr)
        second = self.git("rev-parse", "HEAD").stdout.strip()

        renamed = ".agents/example/convention/renamed/SKILL.md"
        (self.root / renamed).parent.mkdir(parents=True, exist_ok=True)
        self.git("mv", relative, renamed)
        self.commit()
        self.assertEqual(1, self.check("--base", second).returncode)

    def test_deleted_and_unchanged_guidance_do_not_require_retrofit(self):
        relative = ".agents/example/convention/old/SKILL.md"
        self.write(relative, self.skill("# Old\n"))
        self.commit()
        unchanged = self.git("rev-parse", "HEAD").stdout.strip()
        self.write("README.md", "changed\n")
        self.commit()
        self.assertEqual(0, self.check("--base", unchanged).returncode)
        before_delete = self.git("rev-parse", "HEAD").stdout.strip()
        (self.root / relative).unlink()
        self.commit()
        self.assertEqual(0, self.check("--base", before_delete).returncode)

    def test_fences_ignore_front_matter_and_reject_empty_placeholders_and_structural_json(self):
        cases = {
            "frontmatter": "---\nexample: ```text\nInput: not a body\n```\n---\n# Rule\n",
            "empty": self.skill("# Rule\n\n```text\n\n```\n"),
            "placeholder": self.skill("# Rule\n\n```bash\n# TODO\n...\n```\n"),
            "structural": self.skill("# Rule\n\n```json\n{\"schema_version\": 1, \"shared_source\": \"x\", \"hosts\": []}\n```\n"),
            "coverage": self.skill("# Rule\n\n```json agent-host-coverage\n{\"schema_version\": 1, \"shared_source\": \"x\", \"hosts\": []}\n```\n"),
            "completion": self.skill("# Rule\n\n```json\n{\"schema_version\": 1, \"candidate_head\": \"abc\", \"completion\": true}\n```\n"),
            "comments": self.skill("# Rule\n\n```text\n/* TODO */\n<!-- TBD -->\n```\n"),
        }
        for name, body in cases.items():
            with self.subTest(name=name):
                self.write(f".agents/example/convention/{name}/SKILL.md", body)
                result = self.check("--path", f".agents/example/convention/{name}/SKILL.md")
                self.assertEqual(1, result.returncode)

    def test_nonempty_backtick_and_tilde_fences_are_examples(self):
        for name, fence in (("ticks", "```"), ("tildes", "~~~~")):
            with self.subTest(name=name):
                relative = f".agents/example/convention/{name}/SKILL.md"
                self.write(relative, self.skill(f"# Rule\n\n{fence}text\nInput: source\nOutput: result\n{fence}\n"))
                self.assertEqual(0, self.check("--path", relative).returncode)

    def test_template_plugin_namespace_and_real_json_configuration_are_examples(self):
        template = ".agents/template/utility/check/SKILL.md"
        self.write(template, self.skill("# Check\n\n```json\n{\"host\": \"localhost\"}\n```\n"))
        self.assertEqual(0, self.check("--path", template).returncode)

    def test_nested_skill_assets_are_excluded_without_excluding_a_template_plugin(self):
        self.write(".agents/example/convention/real/templates/SKILL.md", self.skill("# Generated template\n"))
        self.write(".agents/example/convention/real/resources/SKILL.md", self.skill("# Resource\n"))
        self.commit()
        self.assertEqual(0, self.check("--base", self.base).returncode)

    def test_example_fenced_inside_an_html_comment_does_not_count(self):
        relative = ".agents/example/convention/commented/SKILL.md"
        self.write(relative, self.skill("# Rule\n\n<!--\n```text\nInput: hidden\n```\n-->\n"))
        self.assertEqual(1, self.check("--path", relative).returncode)

    def test_explicit_paths_check_working_tree_and_support_root_standards(self):
        self.write("SOURCE_LAYOUT.md", "# Layout\n\n```text\nInput: source\nOutput: package\n```\n")
        self.assertEqual(0, self.check("--path", "SOURCE_LAYOUT.md").returncode)
        self.write("RULES.md", "# Rules\n\n```text\nInput: change\nOutput: verified behavior\n```\n")
        self.assertEqual(0, self.check("--path", "RULES.md").returncode)
        for path in ("missing.md", "../outside.md", "fixtures/RULES.md"):
            with self.subTest(path=path):
                self.assertEqual(1, self.check("--path", path).returncode)

    def test_invalid_base_fails_closed_and_zero_base_checks_initial_guidance(self):
        self.write("AGENTS.md", "# Guidance\n\n```text\nInput: change\nOutput: action\n```\n")
        self.commit()
        self.assertEqual(1, self.check("--base", "not-a-commit").returncode)
        self.assertEqual(0, self.check("--base", "0" * 40).returncode)


if __name__ == "__main__":
    unittest.main()
