import contextlib
import importlib.util
import io
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ci_selection", ROOT / "scripts/ci_selection.py")
CI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CI)


class ClassificationTests(unittest.TestCase):
    def test_prose_uses_docs_but_executable_guidance_keeps_full_coverage(self):
        for path in ("README.md", "docs/usage.md", "plans/work/GOAL.md", "reviews/topic.md"):
            with self.subTest(path=path):
                self.assertEqual(CI.classify([path])["mode"], "docs")
        for path in ("AGENTS.md", "CLAUDE.md", ".agents/workflow/contract/plan-artifacts/SKILL.md",
                     ".codex/agents/lane-l4.md", ".github/workflows/ci.yml", "scripts/ci_selection.py",
                     "tests/test_ci_selection.py", "scripts/new_tool.py", "CODE_CONVENTIONS.md"):
            with self.subTest(path=path):
                self.assertEqual(CI.classify([path])["mode"], "full")

    def test_known_runtime_families_union_their_regressions_on_both_platforms(self):
        value = CI.classify([
            ".agents/hooks/problem_records.py",
            ".agents/machine/utility/plugin-selection/scripts/adopt_plugins.py",
            "README.md",
        ])
        self.assertEqual(value["mode"], "focused")
        self.assertTrue({".agents/hooks/tests/test_problem_records.py",
                         ".agents/hooks/tests/test_adopt_plugins.py"}.issubset(value["tests"]))
        CI.required_results(value, self.results(), "pull_request")

    def test_relocated_handoff_helper_keeps_focused_transfer_coverage(self):
        value = CI.classify([".agents/workflow/workflow/handoff/scripts/transfer.py"])
        self.assertEqual("focused", value["mode"])
        self.assertEqual([".agents/hooks/tests/test_handoff_transfer.py"], value["tests"])
        CI.required_results(value, self.results(), "pull_request")

    @staticmethod
    def results():
        return {name: {"result": "success"} for name in
                ("select", "guard", "guidance-examples", "verify-windows", "verify-linux")}

    def test_unknown_shared_infrastructure_and_mixed_changes_use_full_coverage(self):
        for path in (".agents/hooks/hook_runtime.py", ".agents/hooks/hook_dispatch.py",
                     ".agents/machine/utility/plugin-selection/scripts/plugin_selection.py",
                     ".agents/machine/utility/plugin-selection/scripts/repo_config.py",
                     ".agents/machine/utility/plugin-selection/scripts/lock_io.py",
                     ".agents/plugins/sources.json", "tests/launcher_test_support.py"):
            with self.subTest(path=path):
                self.assertEqual(CI.classify(["README.md", path])["mode"], "full")

    def test_scope_risk_and_non_pr_events_cannot_narrow_coverage(self):
        for options in ({"binary": True}, {"lines": 1001}, {"labels": ["ci:full"]},
                        {"event": "push"}, {"event": "merge_group"}, {"event": "unknown"}):
            with self.subTest(options=options):
                self.assertEqual(CI.classify(["README.md"], **options)["mode"], "full")
        self.assertEqual(CI.classify([f"docs/{i}.md" for i in range(41)])["mode"], "full")
        self.assertEqual(CI.classify([])["mode"], "full")

    def test_missing_regression_falls_back_to_full(self):
        with tempfile.TemporaryDirectory() as raw:
            self.assertEqual(CI.classify([".agents/hooks/problem_records.py"], root=Path(raw))["mode"], "full")

    def test_test_changes_include_transitive_consumers_and_new_tests(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "tests").mkdir()
            for name, body in {"test_base.py": "", "test_consumer.py": "from test_base import Fixture",
                               "test_outer.py": "from test_consumer import Helpers"}.items():
                (root / "tests" / name).write_text(body, encoding="utf-8")
            selected = CI.classify(["tests/test_base.py"], root=root)
            self.assertEqual(selected["tests"], ["tests/test_base.py", "tests/test_consumer.py", "tests/test_outer.py"])
            self.assertEqual(CI.classify(["tests/test_outer.py"], root=root)["tests"], ["tests/test_outer.py"])
            self.assertEqual(CI.classify(["tests/test_removed.py"], root=root)["mode"], "full")


class AggregateTests(unittest.TestCase):
    def test_docs_require_guard_and_successful_classification(self):
        results = ClassificationTests.results()
        results["verify-windows"]["result"] = results["verify-linux"]["result"] = "skipped"
        CI.required_results(CI.plan("docs", "prose"), results, "pull_request")
        for job in ("select", "guard", "guidance-examples"):
            with self.subTest(job=job):
                broken = {**results, job: {"result": "skipped"}}
                with self.assertRaises(ValueError):
                    CI.required_results(CI.plan("docs", "prose"), broken, "pull_request")

    def test_selected_jobs_must_succeed_not_skip_cancel_or_disappear(self):
        for mode in ("full", "focused"):
            value = CI.plan(mode, "runtime", ["tests/test_example.py"] if mode == "focused" else [])
            for job in ClassificationTests.results():
                for outcome in ("failure", "cancelled", "skipped", "neutral", None):
                    with self.subTest(mode=mode, job=job, outcome=outcome):
                        broken = {**ClassificationTests.results(), job: {"result": outcome}}
                        with self.assertRaises(ValueError):
                            CI.required_results(value, broken, "pull_request")
                broken = ClassificationTests.results()
                broken.pop(job)
                with self.assertRaises(ValueError):
                    CI.required_results(value, broken, "pull_request")

    def test_main_requires_both_platforms_with_no_pr_guard(self):
        results = ClassificationTests.results()
        results["guard"]["result"] = "skipped"
        CI.required_results(CI.plan("full", "main"), results, "push")

    def test_non_pr_event_cannot_accept_a_narrowed_plan(self):
        results = ClassificationTests.results()
        results["guard"]["result"] = "skipped"
        for mode in ("docs", "focused"):
            value = CI.plan(mode, "narrow", ["tests/test_example.py"] if mode == "focused" else [])
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                CI.required_results(value, results, "push")
        with self.assertRaises(ValueError):
            CI.required_results(CI.plan("full", "main"), [], "push")

    def test_invalid_plan_cannot_establish_green(self):
        for value in ({}, {"mode": "docs", "reason": "prose", "tests": ["tests/test_x.py"]},
                      {"mode": "focused", "reason": "runtime", "tests": []},
                      {"mode": "focused", "reason": "runtime", "tests": ["../../test_x.py"]},
                      {"mode": "full", "reason": "", "tests": []}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CI.required_results(value, ClassificationTests.results(), "pull_request")


class GitSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="CI selection ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "CI tests")
        self.git("config", "user.email", "ci@example.invalid")
        self.git("config", "gc.auto", "0")
        self.git("config", "maintenance.auto", "false")
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        self.commit()
        self.base = self.git("rev-parse", "HEAD").strip()
        self.payload = {"pull_request": {"base": {"sha": self.base}, "labels": []}}

    def git(self, *arguments):
        return subprocess.run(["git", *arguments], cwd=self.root, check=True,
                              capture_output=True, text=True, timeout=30).stdout

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture")

    def test_doc_range_and_explicit_risk_label(self):
        (self.root / "README.md").write_text("changed\n", encoding="utf-8")
        self.commit()
        self.assertEqual(CI.select(self.root, "pull_request", self.payload)["mode"], "docs")
        self.payload["pull_request"]["labels"] = [{"name": "ci:full"}]
        self.assertEqual(CI.select(self.root, "pull_request", self.payload)["mode"], "full")

    def test_rename_keeps_the_old_executable_path_in_scope(self):
        self.git("mv", "README.md", "script.py")
        self.commit()
        self.assertEqual(CI.select(self.root, "pull_request", self.payload)["mode"], "full")

    def test_deleted_unknown_runtime_is_not_invisible(self):
        (self.root / "runtime.py").write_text("pass\n", encoding="utf-8")
        self.commit()
        self.payload["pull_request"]["base"]["sha"] = self.git("rev-parse", "HEAD").strip()
        (self.root / "runtime.py").unlink()
        self.commit()
        self.assertEqual(CI.select(self.root, "pull_request", self.payload)["mode"], "full")

    def test_binary_change_cannot_look_like_prose(self):
        (self.root / "README.md").write_bytes(b"\0binary\0")
        self.commit()
        self.assertEqual(CI.select(self.root, "pull_request", self.payload)["mode"], "full")

    def test_unresolvable_range_and_missing_event_data_fall_back_to_full(self):
        for payload in ({}, {"pull_request": {"base": {"sha": "--help"}}},
                        {"pull_request": {"base": {"sha": "f" * 40}}}):
            with self.subTest(payload=payload):
                self.assertEqual(CI.select(self.root, "pull_request", payload)["mode"], "full")


class ExecutionTests(unittest.TestCase):
    def test_selected_modules_execute_and_propagate_failures(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "tests").mkdir()
            target = root / "tests/test_ci_fixture_selected.py"
            target.write_text("import unittest\nclass Selected(unittest.TestCase):\n def test_selected(self): self.fail('observed regression')\n",
                              encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(CI.run_tests(root, CI.plan("focused", "test", [target.relative_to(root).as_posix()]), "source"), 1)

    def test_zero_discovery_or_missing_selected_module_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "tests").mkdir()
            target = root / "tests/test_ci_fixture_empty.py"
            target.write_text("", encoding="utf-8")
            value = CI.plan("focused", "test", [target.relative_to(root).as_posix()])
            with self.assertRaises(ValueError):
                CI.run_tests(root, value, "source")
            target.unlink()
            with self.assertRaises(ValueError):
                CI.run_tests(root, value, "source")

    def test_missing_selection_output_fails_the_aggregate_entry_point(self):
        with mock.patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(CI.main(["required"]), 1)

    def test_plan_output_is_single_line_and_docs_check_failure_is_red(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            event = root / "event.json"
            event.write_text("{}", encoding="utf-8")
            output = root / "outputs"
            with mock.patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": str(event),
                                              "GITHUB_OUTPUT": str(output)}), \
                    mock.patch.object(CI, "select", return_value=CI.plan("docs", "prose\ntext")), \
                    mock.patch.object(CI.subprocess, "run", side_effect=subprocess.CalledProcessError(1, ["docs"])), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(CI.main(["select", "--root", str(root)]), 1)
            lines = output.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0].removeprefix("plan="))["reason"], "prose\ntext")


class WorkflowWiringTests(unittest.TestCase):
    def test_aggregate_runs_after_all_selection_outcomes_without_path_filters(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        jobs = dict(re.findall(r"^  ([a-z-]+):\n(.*?)(?=^  [a-z-]+:|\Z)",
                               workflow.split("jobs:\n", 1)[1], re.MULTILINE | re.DOTALL))
        self.assertIn("    if: always()\n", jobs["ci-required"])
        required = re.search(r"^    needs: \[(.*?)\]$", jobs["ci-required"], re.MULTILINE)
        self.assertEqual(set(required[1].split(", ")),
                         {"select", "guard", "guidance-examples", "verify-windows", "verify-linux"})
        self.assertIn("CI_NEEDS: ${{ toJSON(needs) }}", jobs["ci-required"])
        self.assertIn("scripts/ci_selection.py required", jobs["ci-required"])
        self.assertNotRegex(workflow.split("jobs:\n", 1)[0], r"paths(?:-ignore)?:")
        self.assertNotIn("cancel-in-progress: true", workflow)
        for platform in ("windows", "linux"):
            job = jobs[f"verify-{platform}"]
            self.assertIn("    needs: select\n", job)
            self.assertIn("mode != 'docs'", job)
            for group in ("source", "runtime"):
                step = re.search(r"      - name: selected[^\n]*\n(.*?)(?=\n      -|\Z)",
                                 job[job.index(f"      - name: selected {'source' if group == 'source' else 'shared'}"):],
                                 re.DOTALL)[1]
                self.assertIn("mode == 'focused'", step)
                self.assertIn(f"scripts/ci_selection.py run --group {group}", step)
                if platform == "linux":
                    self.assertIn("< /dev/null", step)
            for name in ("source layout and package tests", "shared runtime tests"):
                step = job.split(f"      - name: {name}\n", 1)[1].split("\n      -", 1)[0]
                self.assertIn("mode == 'full'", step)
            self.assertIn("sync-generated.ps1 -Check", job)
            self.assertIn("sync_harness_manifests.py --check", job)

    def test_changed_guidance_examples_run_on_pull_requests_and_default_pushes(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        jobs = dict(re.findall(r"^  ([a-z-]+):\n(.*?)(?=^  [a-z-]+:|\Z)",
                               workflow.split("jobs:\n", 1)[1], re.MULTILINE | re.DOTALL))
        job = jobs["guidance-examples"]
        self.assertIn("fetch-depth: 0", job)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", job)
        self.assertIn("repository: tj-agents/template", job)
        self.assertIn("path: .template", job)
        self.assertIn("github.event.pull_request.base.sha", job)
        self.assertIn("github.event.pull_request.head.sha }}\"", job)
        self.assertIn("github.event.before", job)
        self.assertIn("github.sha }}\"", job)
        self.assertIn("github.ref == 'refs/heads/main'", job)
        self.assertEqual(2, job.count(".template/.agents/template/utility/check/scripts/check_examples.py --root . --base"))
        pull_request_run = next(line for line in job.splitlines()
                                if "github.event.pull_request.base.sha" in line)
        push_run = next(line for line in job.splitlines() if "github.event.before" in line)
        self.assertIn("--merge-base", pull_request_run)
        self.assertNotIn("--merge-base", push_run)


if __name__ == "__main__":
    unittest.main()
