"""Keep core's project permissions aligned with the commands CI prescribes."""

from fnmatch import fnmatchcase
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PREFIXES = ("python ", "pwsh ", "powershell.exe ", "./")


def verify_job_commands():
    lines = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8").splitlines()
    start = lines.index("  verify:")
    end = next(index for index in range(start + 1, len(lines)) if re.match(r"  \S", lines[index]))
    commands = []
    block_indent = None
    for line in lines[start:end]:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if block_indent is not None and stripped and indent < block_indent:
            block_indent = None
        if stripped == "run: |":
            block_indent = indent + 2
        elif stripped.startswith("run: "):
            commands.append(stripped.removeprefix("run: "))
        elif block_indent is not None and stripped:
            commands.append(stripped)
    return [command for command in commands if command.startswith(COMMAND_PREFIXES)]


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

    def test_every_ci_verify_command_is_allowed_for_powershell(self):
        commands = verify_job_commands()
        allowed = self.specifiers("allow", "PowerShell")

        self.assertGreater(len(commands), 10)
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(any(fnmatchcase(command, rule) for rule in allowed))

    def test_destructive_delivery_forms_are_denied_for_both_shells(self):
        for tool in ("Bash", "PowerShell"):
            denied = self.specifiers("deny", tool)
            for command in (
                "git push --force origin Fix/Example",
                "git push origin Fix/Example --force-with-lease",
                "git push -f origin Fix/Example",
                "git push origin +Fix/Example",
                "git push origin --delete Fix/Example",
                "git push --mirror origin",
                "git commit --no-verify -m message",
                "gh pr merge 12 --admin",
            ):
                with self.subTest(tool=tool, command=command):
                    self.assertTrue(any(fnmatchcase(command, rule) for rule in denied))

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
