"""The review family names each host's real native reviewer and runs in a repository with no `.agents/`."""

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
    return " ".join((text[start:] if following == -1 else text[start:following]).split())


class NativeLayerNamesTheHostReviewer(unittest.TestCase):
    def host_entry(self, host, packaged=False):
        if packaged:
            tree = "skills" if host == "claude" else "codex-skills"
            return " ".join((PACKAGE / tree / "review" / "SKILL.md").read_text(encoding="utf-8").split())
        return " ".join((ROOT / f".{host}" / "skills" / "review" / "SKILL.md").read_text(encoding="utf-8").split())

    def test_the_shared_stages_name_no_host_and_defer_to_the_host_entry_point(self):
        text = body("review")
        for host_reviewer in ("`code-review`", "`security-review`", "codex review", "Skill tool"):
            self.assertNotIn(host_reviewer, text)
        native = section(text, "## Stage 3")
        self.assertIn("`review`'s host entry point names that reviewer", native)
        self.assertIn("reading the diff yourself is not this layer", native)
        self.assertIn("`native-general`", native)
        self.assertIn("host security reviewer that `review`'s host entry point names", section(text, "## Stage 6"))

    def test_the_claude_entry_point_names_code_review_and_security_review(self):
        for packaged in (False, True):
            with self.subTest(packaged=packaged):
                entry = self.host_entry("claude", packaged)
                self.assertIn("built-in `code-review` skill, invoked through the Skill tool", entry)
                self.assertIn("`<effort> <frozen-base>..<frozen-head>`", entry)
                self.assertIn("built-in `security-review` skill", entry)
                self.assertIn("the checkout is clean at the frozen head, scope is `all`", entry)
                self.assertNotIn("codex review", entry)

    def test_the_codex_entry_point_names_codex_review(self):
        for packaged in (False, True):
            with self.subTest(packaged=packaged):
                entry = self.host_entry("codex", packaged)
                self.assertIn("`codex review --base <frozen-base>`", entry)
                self.assertIn("`security` lens", entry)
                self.assertNotIn("`code-review`", entry)

    def test_every_mode_with_a_native_layer_delegates_to_stage_three(self):
        for skill in DELEGATES_NATIVE_LAYER:
            with self.subTest(skill=skill):
                text = body(skill)
                self.assertIn("`review` Stage 3 native layer", text)

    def test_no_review_family_text_keeps_the_unnamed_native_general_layer(self):
        for skill in ("review", *DELEGATES_NATIVE_LAYER):
            with self.subTest(skill=skill):
                self.assertNotIn("native/general", body(skill))

    def test_the_packaged_procedure_is_the_authored_one(self):
        for skill in ("review", *DELEGATES_NATIVE_LAYER):
            with self.subTest(skill=skill):
                packaged = PACKAGE / ".agents" / "engineering" / "workflow" / skill / "SKILL.md"
                self.assertEqual(body(skill), packaged.read_text(encoding="utf-8"))


class ReviewRunsWithoutRepositoryHelpers(unittest.TestCase):
    def test_no_review_family_step_runs_a_helper_from_the_reviewed_repository(self):
        lifecycle = ROOT / ".agents" / "engineering" / "convention" / "review-lifecycle" / "SKILL.md"
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

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="consumer review ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.package = self.root / "installed engineering"
        shutil.copytree(PACKAGE, self.package)
        self.repository.mkdir()
        self.git("init", "-q", "-b", "main")
        (self.repository / "global.json").write_text("{}\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "base")
        self.git("checkout", "-q", "-b", "fix-prod-boot")
        source = self.repository / "src" / "Authorization"
        source.mkdir(parents=True)
        (source / "Startup.cs").write_text("class Startup {}\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "change")
        home = self.root / "home"
        home.mkdir()
        review_cache = self.root / "review-cache"
        review_cache.mkdir()
        self.environment = {key: value for key, value in os.environ.items() if key not in (
            "CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT", "CODEX_PLUGIN_ROOT", "CODEX_HOME", "CLAUDE_CONFIG_DIR",
        )}
        self.environment.update(
            HOME=str(home), USERPROFILE=str(home), PYTHONIOENCODING="utf-8",
            TMP=str(review_cache), TEMP=str(review_cache),
        )

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

    def external_skill_package(self, host):
        package = self.root / f"external {host}"
        if host == "codex":
            self.environment["CODEX_HOME"] = str(self.root / "codex home")
            package = Path(self.environment["CODEX_HOME"]) / "plugins" / "cache" / "example" / "external" / "1.0"
            tree = "codex-skills"
        else:
            tree = "skills"
        manifest = package / f".{host}-plugin"
        body = package / ".agents" / "external" / "workflow" / "review" / "SKILL.md"
        entry = package / tree / "review" / "SKILL.md"
        manifest.mkdir(parents=True)
        body.parent.mkdir(parents=True)
        entry.parent.mkdir(parents=True)
        (manifest / "plugin.json").write_text(
            json.dumps({"name": "external", "version": "1.0", "skills": f"./{tree}/"}),
            encoding="utf-8",
        )
        body.write_bytes(b"---\nname: review\n---\nexternal raw\r\nbody\n")
        entry.write_text(
            "Read [canonical shared definition](../../.agents/external/workflow/review/SKILL.md) in full.\n",
            encoding="utf-8",
        )
        return package, body

    def native_cli(self, host, package):
        directory = self.root / "native bin"
        directory.mkdir(exist_ok=True)
        inventory = {
            "claude": [{
                "enabled": True, "id": "external@example", "installPath": str(package),
                "scope": "project", "projectPath": str(self.repository), "revision": "advertised-r1",
            }],
            "codex": {"installed": [{
                "enabled": True, "installed": True, "name": "external", "marketplaceName": "example",
                "version": "1.0", "scope": "project", "projectPath": str(self.repository),
                "revision": "advertised-r1",
            }]},
        }[host]
        suffix = ".cmd" if os.name == "nt" else ""
        script = directory / f"{host}{suffix}"
        payload = json.dumps(inventory, separators=(",", ":"))
        if os.name == "nt":
            script.write_text("@echo off\necho " + payload + "\n", encoding="utf-8")
        else:
            script.write_text("#!/bin/sh\nprintf '%s\\n' '" + payload.replace("'", "'\\''") + "'\n", encoding="utf-8")
            script.chmod(0o755)
        self.environment["PATH"] = str(directory) + os.pathsep + self.environment["PATH"]

    def test_generated_helper_pins_installed_identity_for_both_native_hosts(self):
        inherited_python_path = self.environment.get("PYTHONPATH", "")
        self.environment["PYTHONPATH"] = str(self.package / "hooks") + (
            os.pathsep + inherited_python_path if inherited_python_path else ""
        )
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                package, body = self.external_skill_package(host)
                self.native_cli(host, package)
                routes = self.repository / ".agents" / "skill-routes.json"
                lifecycle = self.repository / ".agents" / "skills" / "review" / "SKILL.md"
                lifecycle.parent.mkdir(parents=True, exist_ok=True)
                lifecycle.write_text("---\nname: review\n---\n", encoding="utf-8")
                routes.write_text(
                    json.dumps({"routes": [{"path": "^src/", "skills": ["external:review"]}]}),
                    encoding="utf-8",
                )
                if host == "claude":
                    self.git("add", ".agents")
                    self.git("commit", "-q", "-m", "route installed external skill")

                prepared = self.run_packaged(
                    "workflows/workflow_ops.py", "--root", str(self.repository),
                    "--workflow-run-id", f"installed-{host}", "review-prepare",
                    "--base", "main", "--head", "HEAD", "--host", host,
                )
                self.assertEqual(0, prepared.returncode, prepared.stdout + prepared.stderr)
                descriptor = json.loads(prepared.stdout)
                rule = descriptor["installed_rules"][0]
                self.assertEqual("external:review", rule["requested_name"])
                self.assertEqual("advertised-r1", rule["native_revision"])
                self.assertEqual("1.0", rule["manifest_version"])

                listed = self.run_packaged(
                    "workflows/workflow_ops.py", "--root", str(self.repository),
                    "--workflow-run-id", f"installed-{host}", "skills",
                    "--lifecycle", "review", "--technical", "external:review",
                    "--host", host, "--descriptor", descriptor["artifact"],
                )
                self.assertEqual(0, listed.returncode, listed.stdout + listed.stderr)
                self.assertEqual("load", json.loads(listed.stdout)["skills"][1]["action"])

                shutil.rmtree(Path(descriptor["bundle"]["directory"]))
                restored = self.run_packaged(
                    "workflows/workflow_ops.py", "--root", str(self.repository),
                    "--workflow-run-id", f"installed-{host}", "review-reconcile",
                    "--descriptor", descriptor["artifact"], "--base", "main",
                )
                self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)

                body.write_bytes(b"---\nname: review\n---\ntampered\n")
                drifted = self.run_packaged(
                    "workflows/workflow_ops.py", "--root", str(self.repository),
                    "--workflow-run-id", f"installed-{host}", "review-reconcile",
                    "--descriptor", descriptor["artifact"], "--base", "main",
                )
                self.assertNotEqual(0, drifted.returncode)
                self.assertIn("installed rule identity changed", drifted.stdout + drifted.stderr)

    def external_skill_package(self, host):
        package = self.root / f"external {host}"
        if host == "codex":
            self.environment["CODEX_HOME"] = str(self.root / "codex home")
            package = Path(self.environment["CODEX_HOME"]) / "plugins" / "cache" / "example" / "external" / "1.0"
            tree = "codex-skills"
        else:
            tree = "skills"
        manifest = package / f".{host}-plugin"
        body = package / ".agents" / "external" / "workflow" / "review" / "SKILL.md"
        entry = package / tree / "review" / "SKILL.md"
        manifest.mkdir(parents=True)
        body.parent.mkdir(parents=True)
        entry.parent.mkdir(parents=True)
        (manifest / "plugin.json").write_text(
            json.dumps({"name": "external", "version": "1.0", "skills": f"./{tree}/"}),
            encoding="utf-8",
        )
        body.write_bytes(b"---\nname: review\n---\nexternal raw\r\nbody\n")
        entry.write_text(
            "Read [canonical shared definition](../../.agents/external/workflow/review/SKILL.md) in full.\n",
            encoding="utf-8",
        )
        return package, body

    def native_cli(self, host, package):
        directory = self.root / "native bin"
        directory.mkdir(exist_ok=True)
        inventory = {
            "claude": [{
                "enabled": True, "id": "external@example", "installPath": str(package),
                "scope": "project", "projectPath": str(self.repository), "revision": "advertised-r1",
            }],
            "codex": {"installed": [{
                "enabled": True, "installed": True, "name": "external", "marketplaceName": "example",
                "version": "1.0", "scope": "project", "projectPath": str(self.repository),
                "revision": "advertised-r1",
            }]},
        }[host]
        suffix = ".cmd" if os.name == "nt" else ""
        script = directory / f"{host}{suffix}"
        payload = json.dumps(inventory, separators=(",", ":"))
        if os.name == "nt":
            script.write_text("@echo off\necho " + payload + "\n", encoding="utf-8")
        else:
            script.write_text("#!/bin/sh\nprintf '%s\\n' '" + payload.replace("'", "'\\''") + "'\n", encoding="utf-8")
            script.chmod(0o755)
        self.environment["PATH"] = str(directory) + os.pathsep + self.environment["PATH"]

    def test_generated_helper_pins_installed_identity_for_both_native_hosts(self):
        inherited_python_path = self.environment.get("PYTHONPATH", "")
        self.environment["PYTHONPATH"] = str(self.package / "hooks") + (
            os.pathsep + inherited_python_path if inherited_python_path else ""
        )
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                package, body = self.external_skill_package(host)
                self.native_cli(host, package)
                routes = self.repository / ".agents" / "skill-routes.json"
                lifecycle = self.repository / ".agents" / "skills" / "review" / "SKILL.md"
                lifecycle.parent.mkdir(parents=True, exist_ok=True)
                lifecycle.write_text("---\nname: review\n---\n", encoding="utf-8")
                routes.write_text(
                    json.dumps({"routes": [{"path": "^src/", "skills": ["external:review"]}]}),
                    encoding="utf-8",
                )
                if host == "claude":
                    self.git("add", ".agents")
                    self.git("commit", "-q", "-m", "route installed external skill")

                prepared = self.run_packaged(
                    "workflows/workflow_ops.py", "--root", str(self.repository),
                    "--workflow-run-id", f"installed-{host}", "review-prepare",
                    "--base", "main", "--head", "HEAD", "--host", host,
                )
                self.assertEqual(0, prepared.returncode, prepared.stdout + prepared.stderr)
                descriptor = json.loads(prepared.stdout)
                rule = descriptor["installed_rules"][0]
                self.assertEqual("external:review", rule["requested_name"])
                self.assertEqual("advertised-r1", rule["native_revision"])
                self.assertEqual("1.0", rule["manifest_version"])

                listed = self.run_packaged(
                    "workflows/workflow_ops.py", "--root", str(self.repository),
                    "--workflow-run-id", f"installed-{host}", "skills",
                    "--lifecycle", "review", "--technical", "external:review",
                    "--host", host, "--descriptor", descriptor["artifact"],
                )
                self.assertEqual(0, listed.returncode, listed.stdout + listed.stderr)
                self.assertEqual("load", json.loads(listed.stdout)["skills"][1]["action"])

                shutil.rmtree(Path(descriptor["bundle"]["directory"]))
                restored = self.run_packaged(
                    "workflows/workflow_ops.py", "--root", str(self.repository),
                    "--workflow-run-id", f"installed-{host}", "review-reconcile",
                    "--descriptor", descriptor["artifact"], "--base", "main",
                )
                self.assertEqual(0, restored.returncode, restored.stdout + restored.stderr)

                body.write_bytes(b"---\nname: review\n---\ntampered\n")
                drifted = self.run_packaged(
                    "workflows/workflow_ops.py", "--root", str(self.repository),
                    "--workflow-run-id", f"installed-{host}", "review-reconcile",
                    "--descriptor", descriptor["artifact"], "--base", "main",
                )
                self.assertNotEqual(0, drifted.returncode)
                self.assertIn("installed rule identity changed", drifted.stdout + drifted.stderr)

    def test_stage_one_prepares_the_candidate_with_no_repository_runtime(self):
        self.assertFalse((self.repository / ".agents").exists())

        completed = self.run_packaged(
            "workflows/workflow_ops.py", "--root", str(self.repository),
            "--workflow-run-id", "consumer-review", "review-prepare", "--base", "main", "--head", "HEAD",
        )

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        descriptor = json.loads(completed.stdout)
        self.assertEqual(["src/Authorization/Startup.cs"], descriptor["paths"])
        self.assertEqual([], descriptor["rules"])
        self.assertEqual([], descriptor["routed_skills"])
        self.assertEqual("src/Authorization/Startup.cs", descriptor["security"]["first_path"])
        self.assertEqual("src/Authorization/Startup.cs", descriptor["security"]["trunk_first_path"])
        self.assertTrue(Path(descriptor["bundle"]["tree"]).is_dir())

    def test_stack_child_inherits_its_parent_layers_security_paths(self):
        self.git("checkout", "-q", "-b", "stack-child")
        (self.repository / "README.md").write_text("docs\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "child")

        completed = self.run_packaged(
            "workflows/workflow_ops.py", "--root", str(self.repository),
            "--workflow-run-id", "stack-child", "review-prepare", "--base", "fix-prod-boot", "--head", "HEAD",
        )

        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        descriptor = json.loads(completed.stdout)
        self.assertNotIn("src/Authorization/Startup.cs", descriptor["paths"])
        main = subprocess.run(["git", "rev-parse", "main"], cwd=self.repository, capture_output=True, text=True)
        self.assertEqual(
            {"first_path": None, "trunk_base": main.stdout.strip(), "trunk_first_path": "src/Authorization/Startup.cs"},
            descriptor["security"],
        )

    def test_stage_four_lists_the_installed_tier_conventions_from_the_plugin(self):
        config = self.root / "claude"
        cache = config / "plugins" / "cache"
        installed = cache / "dotagents" / "dotnet" / "installed"
        stale = cache / "dotagents" / "dotnet" / "stale"
        for payload in (installed, stale):
            skill = payload / "skills" / "persistence"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: persistence\nkind: contract\n---\n", encoding="utf-8")
            (payload / "tier.json").write_text(json.dumps({
                "schema_version": 1, "tier": "dotnet", "applies": "stack-present",
                "detect": {"files": ["global.json"]},
            }), encoding="utf-8")
        registry = {"plugins": {"dotnet@dotagents": [{"scope": "user", "installPath": str(installed)}]}}
        (config / "plugins" / "installed_plugins.json").write_text(json.dumps(registry), encoding="utf-8")
        self.environment["CLAUDE_CONFIG_DIR"] = str(config)

        completed = self.run_packaged(
            "hooks/tier_gate.py", "--conventions", "--project", str(self.repository),
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("dotnet (", completed.stdout)
        self.assertIn(str(installed / "skills" / "persistence" / "SKILL.md"), completed.stdout)
        self.assertNotIn(str(stale), completed.stdout)


if __name__ == "__main__":
    unittest.main()
