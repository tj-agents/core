"""Keep core's project permissions aligned with the commands CI prescribes."""

from fnmatch import fnmatchcase
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
BLOCK_START = re.compile(r"run:\s*[|>](?:[-+]?\d?|\d[-+])\s*(?:\s#.*)?")
POWERSHELL_CONTROL = re.compile(r"(\$|if\s*\()")
CI_BOOTSTRAP_STEPS = {
    "build the pinned tj_hook candidate",
    "install the locked Python environment",
}


def verify_job_block(name):
    lines = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8").splitlines()
    start = lines.index(f"  {name}:")
    end = next((index for index in range(start + 1, len(lines)) if re.match(r"  \S", lines[index])), len(lines))
    return lines[start:end]


def verify_job_commands():
    commands = []
    block_indent = None
    step_name = ""
    for line in verify_job_block("verify-windows"):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped.startswith("- ") and not stripped.startswith("- name: "):
            step_name = ""
        if stripped.startswith("- name: "):
            step_name = stripped.removeprefix("- name: ")
        if stripped.startswith("- run:"):
            stripped = stripped.removeprefix("- ")
            indent += 2
        if block_indent is not None and stripped and indent < block_indent:
            block_indent = None
        if BLOCK_START.fullmatch(stripped):
            block_indent = indent + 2
        elif stripped.startswith("run: ") and step_name not in CI_BOOTSTRAP_STEPS:
            commands.append(stripped.removeprefix("run: "))
        elif block_indent is not None and stripped and step_name not in CI_BOOTSTRAP_STEPS:
            commands.append(stripped)
    return [command for command in commands if not POWERSHELL_CONTROL.match(command)]


def bash_form(command):
    return "pwsh " + command if command.startswith("./") else command


class RepositoryPermissionTests(unittest.TestCase):
    def setUp(self):
        self.permissions = json.loads(
            (ROOT / ".claude/settings.json").read_text(encoding="utf-8")
        )["permissions"]

    def specifiers(self, key, tool):
        prefix = tool + "("
        return [
            rule[len(prefix):-1]
            for rule in self.permissions[key]
            if rule.startswith(prefix) and rule.endswith(")")
        ]

    def auto_approved(self, tool, command):
        allowed = any(fnmatchcase(command, rule) for rule in self.specifiers("allow", tool))
        denied = any(fnmatchcase(command, rule) for rule in self.specifiers("deny", tool))
        return allowed and not denied

    def test_every_ci_verify_command_is_allowed_for_both_shells(self):
        commands = verify_job_commands()

        self.assertEqual(17, len(commands))
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(self.auto_approved("PowerShell", command))
                self.assertTrue(self.auto_approved("Bash", bash_form(command)))

    def test_verify_jobs_provision_hidden_hook_runtime(self):
        for name in ("verify-windows", "verify-linux"):
            with self.subTest(job=name):
                block = "\n".join(verify_job_block(name))
                self.assertIn(
                    "astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884 # v10.3.0",
                    block,
                )
                self.assertIn("python-version: '3.12'", block)
                self.assertIn("repository: tj-agents/cli", block)
                self.assertIn("ref: cd8c726e2aadc321251de599b75c4e72e21cecb9", block)
                self.assertIn("cargo build --locked --release --bin tj_hook", block)
                self.assertIn("uv sync --locked", block)
                self.assertIn("$binaryDirectory >> $env:GITHUB_PATH", block)
                self.assertIn(
                    'uv run --locked python -c "import sys; print(sys.executable)"',
                    block,
                )
                self.assertIn("$pythonDirectory >> $env:GITHUB_PATH", block)
                self.assertLess(
                    block.index("$pythonDirectory >> $env:GITHUB_PATH"),
                    block.index("- name: regenerate the workspace from authored sources"),
                )

    def test_regeneration_validates_with_locked_hook_dependencies(self):
        block = "\n".join(verify_job_block("regenerate"))
        self.assertIn("astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884", block)
        validator = "uv run --locked python -B .agents/hooks/check_tier_payload.py --root ."
        self.assertIn(validator, block)
        self.assertLess(block.index("astral-sh/setup-uv@"), block.index(validator))

    def test_project_settings_never_auto_approve_destructive_delivery(self):
        for tool in ("Bash", "PowerShell"):
            for command in (
                "git push --force origin Fix/Example",
                "git push origin Fix/Example --force-with-lease",
                "git push -f origin Fix/Example",
                "git push -uf origin Fix/Example",
                "git push -ud origin Fix/Example",
                "git push origin +Fix/Example",
                "git push origin :Fix/Example",
                "git push origin --delete Fix/Example",
                "git push --prune origin refs/heads/*:refs/heads/*",
                "git push --mirror origin",
                "gh pr merge 12 --admin",
            ):
                with self.subTest(tool=tool, command=command):
                    self.assertFalse(self.auto_approved(tool, command))

    def test_generated_output_is_not_editable(self):
        sources = json.loads(
            (ROOT / ".agents/plugins/sources.json").read_text(encoding="utf-8")
        )
        allowed = self.specifiers("allow", "Edit")
        denied = self.specifiers("deny", "Edit")
        for generated in sources["generated_roots"]:
            path = "/" + generated
            with self.subTest(path=path):
                editable = any(fnmatchcase(path, rule) or fnmatchcase(path + "/x", rule) for rule in allowed)
                self.assertTrue(not editable or path in denied)


if __name__ == "__main__":
    unittest.main()
