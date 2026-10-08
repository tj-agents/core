import importlib.util
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


OPERATIONS = Path(__file__).resolve().parents[2] / "workflows" / "workflow_ops.py"
SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "workflow_efficiency_scenarios.json"


def load_operations():
    spec = importlib.util.spec_from_file_location("workflow_ops", OPERATIONS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ops = load_operations()


class RepositoryFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        self.git("config", "user.email", "workflow@example.test")
        self.git("config", "user.name", "Workflow Fixture")
        self.git("remote", "add", "origin", "https://github.com/example/workflow-fixture.git")
        (self.root / ".agents" / "skills" / "feature").mkdir(parents=True)
        (self.root / ".agents" / "skills" / "feature" / "SKILL.md").write_text(
            "---\nname: feature\n---\n\n# Feature\n",
            encoding="utf-8",
        )
        (self.root / "src").mkdir()
        (self.root / "src" / "mapping.txt").write_text("baseline\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "baseline")
        self.base = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", self.base)
        self.git("switch", "-q", "-c", "Feature/Workflow-ops")

    def git(self, *arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def commit(self, path, text, message):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        self.git("add", str(path))
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")


class PrReadinessTests(RepositoryFixture):
    def pr(self, checks):
        return {
            "number": 42,
            "url": "https://github.com/example/workflow-fixture/pull/42",
            "headRefOid": "abc123",
            "statusCheckRollup": checks,
        }

    def test_pending_reports_observed_checks_and_a_recheck_interval(self):
        value = self.pr([{"name": "verify", "status": "IN_PROGRESS", "conclusion": ""}])
        with mock.patch.object(ops, "pull_request_state", return_value=value):
            result = ops.pr_readiness_observation(self.root, 42, "example/private", 45)

        self.assertEqual("waiting", result["state"])
        self.assertFalse(result["terminal"])
        self.assertEqual(["verify"], result["observed_pending_checks"])
        self.assertEqual(45, result["recheck_seconds"])
        self.assertEqual("example/private", result["identity"]["repository"])

    def test_green_checks_are_ready_for_the_next_delivery_gate(self):
        value = self.pr([{"name": "verify", "status": "COMPLETED", "conclusion": "SUCCESS"}])
        with mock.patch.object(ops, "pull_request_state", return_value=value):
            result = ops.pr_readiness_observation(self.root, 42, "example/private")

        self.assertEqual("ready", result["state"])
        self.assertTrue(result["terminal"])
        self.assertIn("next delivery gate", result["message"])

    def test_closed_pr_is_terminal_not_ready(self):
        value = self.pr([])
        value["state"] = "CLOSED"
        with mock.patch.object(ops, "pull_request_state", return_value=value):
            result = ops.pr_readiness_observation(self.root, 42, "example/private")

        self.assertEqual("closed", result["state"])
        self.assertTrue(result["terminal"])
        self.assertIn("not ready", result["message"])

    def test_ordinary_failed_check_names_the_job_and_url(self):
        value = self.pr([{
            "name": "verify", "status": "COMPLETED", "conclusion": "FAILURE",
            "databaseId": 90, "targetUrl": "https://github.com/example/private/actions/runs/3/job/90",
        }])
        unavailable = subprocess.CompletedProcess([], 1, "", "not available")
        with mock.patch.object(ops, "pull_request_state", return_value=value), \
                mock.patch.object(ops, "run_process", return_value=unavailable):
            result = ops.pr_readiness_observation(self.root, 42, "example/private")

        self.assertEqual("failed", result["state"])
        self.assertTrue(result["terminal"])
        self.assertEqual("verify", result["failed_check"]["name"])
        self.assertEqual("https://github.com/example/private/actions/runs/3/job/90", result["failed_check"]["url"])

    def test_external_block_in_any_failed_check_is_preferred(self):
        value = self.pr([
            {"name": "unit", "status": "COMPLETED", "conclusion": "FAILURE"},
            {"name": "billing", "status": "COMPLETED", "conclusion": "FAILURE", "targetUrl": "https://example.test/billing"},
        ])
        block = {"kind": "github-billing", "resolver": "GitHub organization/account billing administrator"}
        with mock.patch.object(ops, "pull_request_state", return_value=value), \
                mock.patch.object(ops, "external_check_block", side_effect=[None, block]):
            result = ops.pr_readiness_observation(self.root, 42, "example/private")

        self.assertEqual("blocked", result["state"])
        self.assertEqual("billing", result["failed_check"]["name"])
        self.assertEqual("https://example.test/billing", result["failed_check"]["url"])

    def test_failed_payment_or_spending_limit_is_an_external_billing_block(self):
        value = self.pr([{
            "name": "verify", "status": "COMPLETED", "conclusion": "FAILURE",
            "detailsUrl": "https://github.com/example/private/actions/runs/3/job/90",
        }])
        output = {"check_runs": [{"name": "verify", "output": {"summary": "GitHub Actions failed payment: spending limit reached."}}]}
        completed = subprocess.CompletedProcess([], 0, json.dumps(output), "")
        with mock.patch.object(ops, "pull_request_state", return_value=value), \
                mock.patch.object(ops, "run_process", return_value=completed) as run:
            result = ops.pr_readiness_observation(self.root, 42, "example/private")

        self.assertEqual("blocked", result["state"])
        self.assertTrue(result["terminal"])
        self.assertEqual("no ETA available", result["eta"])
        self.assertEqual("GitHub organization/account billing administrator", result["external_block"]["resolver"])
        self.assertIn("restores billing or raises the spending limit", result["external_block"]["resume_condition"])
        run.assert_called_once_with(
            ["gh", "api", "repos/example/private/commits/abc123/check-runs"], self.root, check=False
        )

    def test_watch_stops_immediately_for_a_terminal_external_block(self):
        blocked = {"state": "blocked", "terminal": True}
        with mock.patch.object(ops, "pr_readiness_observation", return_value=blocked) as observe, \
                mock.patch.object(ops.time, "sleep") as sleep:
            result = ops.pr_readiness(self.root, 42, "example/private", watch=True)

        self.assertEqual(blocked, result)
        observe.assert_called_once_with(self.root, 42, "example/private", ops.DEFAULT_POLL_SECONDS)
        sleep.assert_not_called()

    def test_watch_emits_each_pending_observation_before_rechecking(self):
        pending = {"state": "waiting", "terminal": False}
        ready = {"state": "ready", "terminal": True}
        emitted = []
        with mock.patch.object(ops, "pr_readiness_observation", side_effect=[pending, ready]), \
                mock.patch.object(ops.time, "sleep") as sleep:
            result = ops.pr_readiness(self.root, 42, "example/private", 15, watch=True, on_wait=emitted.append)

        self.assertEqual(ready, result)
        self.assertEqual([pending], emitted)
        sleep.assert_called_once_with(15)

    def test_poll_interval_is_bounded(self):
        with self.assertRaisesRegex(ops.WorkflowOperationError, "between 15 and 300"):
            ops.pr_readiness(self.root, 42, "example/private", 0)
        with self.assertRaisesRegex(ops.WorkflowOperationError, "between 15 and 300"):
            ops.pr_readiness(self.root, 42, "example/private", 301)


class CompactRunTests(RepositoryFixture):
    def test_process_output_decodes_utf8_even_with_non_ascii_text(self):
        result = ops.run_process(
            [sys.executable, "-c", "import sys; sys.stdout.buffer.write('café'.encode('utf-8'))"],
            self.root,
        )
        self.assertEqual("café", result.stdout)

    def test_success_returns_no_log_content_and_keeps_the_artifact(self):
        result = ops.compact_run(
            self.root,
            "run-1",
            "successful validation",
            [sys.executable, "-c", "print('large successful failure-path test detail\\n' * 100)"],
            8,
            20,
            4096,
        )
        self.assertEqual("succeeded", result["exit_state"])
        self.assertEqual([], result["summary"])
        self.assertEqual([], result["failing_items"])
        self.assertGreater(result["captured_lines"], 90)
        self.assertIn("large successful failure-path test detail", Path(result["artifact"]).read_text(encoding="utf-8"))
        scenario = json.loads(SCENARIOS.read_text(encoding="utf-8"))["bounded_log_output"]
        self.assertEqual(scenario["success_summary_bytes"], len(json.dumps(result["summary"]).encode("utf-8")) - 2)

    def test_failure_items_and_summary_are_bounded(self):
        result = ops.compact_run(
            self.root,
            "run-1",
            "failed validation",
            [sys.executable, "-c", "import sys; print('ERROR item-' + 'x' * 5000); sys.exit(3)"],
            2,
            1,
            128,
        )
        self.assertEqual("failed", result["exit_state"])
        self.assertEqual(3, result["exit_code"])
        self.assertEqual(1, len(result["failing_items"]))
        self.assertLessEqual(len(result["failing_items"][0].encode("utf-8")), 128)
        self.assertLessEqual(sum(len(line.encode("utf-8")) for line in result["summary"]), 128)

    def test_caller_cannot_raise_the_repository_output_caps(self):
        result = ops.compact_run(
            self.root,
            "run-1",
            "failed validation",
            [sys.executable, "-c", "import sys; print(('ERROR item ' + 'x' * 500 + '\\n') * 100); sys.exit(1)"],
            1000,
            1000,
            1000000,
        )
        self.assertLessEqual(len(result["failing_items"]), 20)
        self.assertLessEqual(sum(len(line.encode("utf-8")) for line in result["summary"]), 4096)

    def test_failure_summary_redacts_credentials(self):
        result = ops.compact_run(
            self.root,
            "run-1",
            "failed secret validation",
            [sys.executable, "-c", "import sys; print('ERROR token=abc123 password:open'); print('ERROR Authorization: Bearer bearer-value'); print('ERROR Authorization=Basic basic-value'); sys.exit(1)"],
            2,
            2,
            256,
        )
        returned = json.dumps({"summary": result["summary"], "failing_items": result["failing_items"]})
        self.assertNotIn("abc123", returned)
        self.assertNotIn("password:open", returned)
        self.assertNotIn("bearer-value", returned)
        self.assertNotIn("basic-value", returned)
        self.assertIn("[REDACTED]", returned)
        artifact = Path(result["artifact"]).read_text(encoding="utf-8")
        self.assertNotIn("abc123", artifact)
        self.assertNotIn("password:open", artifact)
        self.assertNotIn("bearer-value", artifact)
        self.assertNotIn("basic-value", artifact)

    def test_nested_run_ids_are_contained_and_parent_traversal_is_rejected(self):
        nested = ops.inspect_repository(self.root, "agent-workflows/runtime-001")
        self.assertEqual("inspect", nested["operation"])
        with self.assertRaisesRegex(ops.WorkflowOperationError, "escapes"):
            ops.inspect_repository(self.root, "../outside")

    def test_run_id_rejects_an_alias_to_another_run_inside_the_state_root(self):
        runs = ops.state_root(self.root) / "runs"
        target = runs / "target"
        target.mkdir(parents=True)
        alias = runs / "alias"
        if sys.platform == "win32":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(alias), str(target)],
                capture_output=True, check=True,
            )
            self.addCleanup(alias.rmdir)
        else:
            alias.symlink_to(target, target_is_directory=True)
            self.addCleanup(alias.unlink)

        with self.assertRaisesRegex(ops.WorkflowOperationError, "redirected"):
            ops.run_root(self.root, "alias/nested")

    def test_run_id_rejects_a_redirected_workflow_state_root(self):
        state = ops.state_root(self.root)
        original_redirect = ops.is_redirect
        with mock.patch.object(
            ops, "is_redirect",
            side_effect=lambda path: Path(path) == state or original_redirect(path),
        ):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "redirected"):
                ops.run_root(self.root, "run-1")


class InspectionAndSkillTests(RepositoryFixture):
    def test_inspection_consolidates_repository_identity(self):
        result = ops.inspect_repository(self.root, "run-1")
        self.assertEqual("example/workflow-fixture", result["repository"])
        self.assertEqual("Feature/Workflow-ops", result["branch"])
        self.assertEqual(self.git("rev-parse", "HEAD"), result["head"])
        self.assertEqual([], result["dirty_paths"])

    def test_inspection_preserves_modified_and_renamed_paths_with_spaces(self):
        path = self.root / ".agents" / "skills" / "feature" / "SKILL.md"
        path.write_text("# Changed guidance\n", encoding="utf-8")
        self.git("mv", "src/mapping.txt", "src/renamed mapping.txt")
        result = ops.inspect_repository(self.root, "paths")
        self.assertCountEqual(
            [".agents/skills/feature/SKILL.md", "src/renamed mapping.txt", "src/mapping.txt"],
            result["dirty_paths"],
        )

    def test_skill_identity_loads_once_and_survives_context_recovery(self):
        lifecycle = "feature"
        first = ops.skill_identities(self.root, "run-1", lifecycle, [])
        second = ops.skill_identities(self.root, "run-1", lifecycle, [])
        self.assertEqual("load", first["skills"][0]["action"])
        self.assertEqual("cached", second["skills"][0]["action"])
        self.assertEqual(first["skills"][0]["sha256"], second["skills"][0]["sha256"])

    def test_changed_skill_identity_requires_a_new_load(self):
        lifecycle = "feature"
        ops.skill_identities(self.root, "run-1", lifecycle, [])
        path = self.root / ".agents" / "skills" / "feature" / "SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
        changed = ops.skill_identities(self.root, "run-1", lifecycle, [])
        self.assertEqual("load", changed["skills"][0]["action"])


class ReviewTests(RepositoryFixture):
    def setUp(self):
        super().setUp()
        cache = Path(self.temp.name) / "review-cache"
        cache.mkdir()
        patcher = mock.patch.object(ops.tempfile, "gettempdir", return_value=str(cache))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.head = self.commit("src/mapping.txt", "candidate\n", "candidate")

    def test_failed_initial_routing_removes_the_unpublished_bundle_and_allows_retry(self):
        with mock.patch.object(ops, "route_findings", side_effect=OSError("routing failed")):
            with self.assertRaisesRegex(OSError, "routing failed"):
                ops.review_prepare(self.root, "retry", "origin/main", "HEAD", False)

        result = ops.review_prepare(self.root, "retry", "origin/main", "HEAD", False)

        self.assertTrue(Path(result["artifact"]).is_file())

    def test_failed_descriptor_publication_removes_the_unpublished_bundle_and_allows_retry(self):
        original_atomic_json = ops.atomic_json

        def fail_publication(path, value):
            if Path(path).name == "descriptor.json":
                raise OSError("publication failed")
            original_atomic_json(path, value)

        with mock.patch.object(ops, "atomic_json", side_effect=fail_publication):
            with self.assertRaisesRegex(OSError, "publication failed"):
                ops.review_prepare(self.root, "retry", "origin/main", "HEAD", False)

        result = ops.review_prepare(self.root, "retry", "origin/main", "HEAD", False)

        self.assertTrue(Path(result["artifact"]).is_file())

    def test_rejected_preexisting_unpublished_bundle_is_preserved(self):
        result = ops.review_prepare(self.root, "existing", "origin/main", "HEAD", False)
        Path(result["artifact"]).unlink()
        directory = Path(result["bundle"]["directory"])
        original_patch = Path(result["bundle"]["patch"]).read_bytes()

        with self.assertRaisesRegex(ops.WorkflowOperationError, "already exists"):
            ops.review_prepare(self.root, "existing", "origin/main", "HEAD", False)

        self.assertTrue(directory.is_dir())
        self.assertEqual(original_patch, Path(result["bundle"]["patch"]).read_bytes())

    def test_cleanup_locked_expired_bundle_does_not_block_unrelated_preparation(self):
        expired = ops.review_prepare(self.root, "expired", "origin/main", "HEAD", False)
        descriptor_path = Path(expired["artifact"])
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        descriptor["bundle"]["last_validated_at"] = "2000-01-01T00:00:00+00:00"
        ops.atomic_json(descriptor_path, descriptor)
        original_rmtree = ops.shutil.rmtree

        def remove_unlocked(path, *args, **kwargs):
            if Path(path) == Path(expired["bundle"]["directory"]):
                raise PermissionError("bundle locked")
            return original_rmtree(path, *args, **kwargs)

        with mock.patch.object(ops.shutil, "rmtree", side_effect=remove_unlocked):
            result = ops.review_prepare(self.root, "unrelated", "origin/main", "HEAD", False)

        self.assertTrue(Path(result["artifact"]).is_file())
        self.assertTrue(Path(expired["bundle"]["directory"]).is_dir())

    def test_cleanup_malformed_descriptor_does_not_block_unrelated_preparation(self):
        for name, value in (("list", []), ("bundle-list", {"bundle": []})):
            path = ops.run_root(self.root, name) / "review" / "candidate" / "descriptor.json"
            ops.atomic_json(path, value)

        result = ops.review_prepare(self.root, "unrelated", "origin/main", "HEAD", False)

        self.assertTrue(Path(result["artifact"]).is_file())

    def test_small_candidate_gets_one_minimal_isolated_wave(self):
        result = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        self.assertEqual(1, result["waves"])
        self.assertEqual(["native-general"], result["lenses"])
        self.assertEqual(["src/mapping.txt"], result["paths"])
        self.assertNotIn("transcript", result["context"])
        self.assertLess(len(json.dumps(result["context"])), 4096)
        tree = Path(result["bundle"]["tree"])
        self.assertEqual("candidate\n", (tree / "src" / "mapping.txt").read_text(encoding="utf-8"))
        self.assertEqual(result["bundle"]["identity_sha256"], ops.sha256_file(Path(result["bundle"]["identity"])))
        path_bytes = Path(result["bundle"]["paths"]).read_bytes()
        self.assertFalse(path_bytes.endswith(b"\0"))
        self.assertEqual(hashlib.sha256(path_bytes).hexdigest(), result["path_digest"])

    def test_materialized_review_tree_is_outside_the_checkout_and_common_git_directory(self):
        result = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        tree = Path(result["bundle"]["tree"]).resolve()
        common = Path(self.git("rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
        with self.assertRaises(ValueError):
            tree.relative_to(self.root.resolve())
        with self.assertRaises(ValueError):
            tree.relative_to(common)

    def test_temp_cache_under_another_registered_worktree_is_rejected(self):
        linked = self.root.parent / "linked"
        self.git("worktree", "add", "-q", "-b", "Fix/Linked", str(linked))
        self.addCleanup(lambda: subprocess.run(
            ["git", "worktree", "remove", "--force", str(linked)], cwd=self.root,
            capture_output=True, text=True,
        ))
        with mock.patch.object(ops.tempfile, "gettempdir", return_value=str(self.root / "temporary")):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "inside the checkout"):
                ops.review_bundle_locations(linked, "nested/run", "a" * 64)

    def test_wholly_missing_bundle_restores_the_frozen_identity_after_head_moves(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        original = json.loads(Path(descriptor["artifact"]).read_text(encoding="utf-8"))
        identity = Path(descriptor["bundle"]["identity"]).read_bytes()
        shutil.rmtree(descriptor["bundle"]["directory"])
        self.commit("src/later.txt", "later\n", "later candidate")

        reconciled = ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

        restored = json.loads(Path(descriptor["artifact"]).read_text(encoding="utf-8"))
        self.assertEqual(original["descriptor_id"], restored["descriptor_id"])
        self.assertEqual(original["created_at"], restored["created_at"])
        self.assertEqual(original["synchronization"], restored["synchronization"])
        self.assertEqual(identity, Path(descriptor["bundle"]["identity"]).read_bytes())
        self.assertTrue(reconciled["review_required"])

    def test_interrupted_restore_removes_owned_cache_and_retries_exact_identity(self):
        for failure in ("materialize_tree", "atomic_json"):
            with self.subTest(failure=failure):
                descriptor = ops.review_prepare(self.root, failure, "origin/main", "HEAD", False)
                artifact = Path(descriptor["artifact"])
                stored = artifact.read_bytes()
                identity = Path(descriptor["bundle"]["identity"]).read_bytes()
                directory = Path(descriptor["bundle"]["directory"])
                shutil.rmtree(directory)
                with mock.patch.object(ops, failure, side_effect=OSError("interrupted restore")):
                    with self.assertRaisesRegex(OSError, "interrupted restore"):
                        ops.load_descriptor(self.root, failure, artifact)
                self.assertFalse(directory.exists())
                self.assertEqual(stored, artifact.read_bytes())
                restored = ops.load_descriptor(self.root, failure, artifact)
                self.assertEqual(descriptor["descriptor_id"], restored["descriptor_id"])
                self.assertEqual(identity, Path(restored["bundle"]["identity"]).read_bytes())
                original = json.loads(stored)
                original["bundle"].pop("last_validated_at")
                restored["bundle"].pop("last_validated_at")
                self.assertEqual(original, restored)

    def test_final_cache_inside_registered_worktree_is_rejected(self):
        temporary = Path(ops.tempfile.gettempdir())
        for depth in (0, 1):
            with self.subTest(depth=depth):
                locations = ops.review_bundle_locations(self.root, "nested/run", "a" * 64)
                linked = temporary / "review"
                if depth:
                    linked = locations["directory"].parent.parent
                self.git("worktree", "add", "-q", "-b", f"Fix/Cache-{depth}", str(linked))
                try:
                    with self.assertRaisesRegex(ops.WorkflowOperationError, "inside the checkout"):
                        ops.review_bundle_locations(self.root, "nested/run", "a" * 64)
                finally:
                    self.git("worktree", "remove", "--force", str(linked))

    def test_partial_bundle_is_rejected_without_restoration(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        Path(descriptor["bundle"]["tree_archive"]).unlink()
        identity = Path(descriptor["bundle"]["identity"]).read_bytes()

        with self.assertRaisesRegex(ops.WorkflowOperationError, "incomplete"):
            ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")
        self.assertTrue(Path(descriptor["bundle"]["directory"]).is_dir())
        self.assertEqual(identity, Path(descriptor["bundle"]["identity"]).read_bytes())

    def test_cleanup_skips_recent_bundle_without_resolving_locations(self):
        recent = ops.review_prepare(self.root, "recent", "origin/main", "HEAD", False)

        with mock.patch.object(ops, "review_bundle_locations") as locations:
            ops.cleanup_review_bundles(self.root)

        locations.assert_not_called()
        self.assertTrue(Path(recent["bundle"]["directory"]).is_dir())

    def test_cleanup_never_scans_legacy_payload_trees(self):
        payloads = []
        for name, with_descriptor in (("stored", True), ("unpublished", False)):
            candidate = ops.run_root(self.root, name) / "review" / ("a" * 64)
            payload = candidate / "tree"
            payload.mkdir(parents=True)
            payloads.append(payload)
            if with_descriptor:
                ops.atomic_json(candidate / "descriptor.json", {"bundle": {}})
        original_scandir = ops.os.scandir

        def scan_namespace(path):
            self.assertNotIn(Path(path), payloads)
            return original_scandir(path)

        with mock.patch.object(ops.os, "scandir", side_effect=scan_namespace), mock.patch.object(
            getattr(Path, "_globber", ops.os), "scandir", side_effect=scan_namespace
        ):
            ops.cleanup_review_bundles(self.root)

    def test_descriptor_scan_preserves_nested_review_and_candidate_named_runs(self):
        runs = ops.state_root(self.root) / "runs"
        paths = []
        for run_id in ("nested/run", "review/" + "b" * 64 + "/nested", "namespace/tree/run"):
            descriptor = ops.run_root(self.root, run_id) / "review" / ("c" * 64) / "descriptor.json"
            ops.atomic_json(descriptor, {"bundle": {}})
            paths.append(descriptor)

        self.assertCountEqual(paths, ops.review_descriptor_paths(runs))

    def test_descriptor_scan_does_not_traverse_directory_junctions(self):
        runs = ops.state_root(self.root) / "runs"
        runs.mkdir(parents=True)
        target = Path(self.temp.name) / "foreign-run"
        descriptor = target / "review" / ("d" * 64) / "descriptor.json"
        ops.atomic_json(descriptor, {"bundle": {}})
        alias = runs / "alias"
        if sys.platform == "win32":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(alias), str(target)],
                capture_output=True, check=True,
            )
            self.addCleanup(alias.rmdir)
        else:
            alias.symlink_to(target, target_is_directory=True)
            self.addCleanup(alias.unlink)
        original_scandir = ops.os.scandir

        def scan_namespace(path):
            self.assertNotEqual(alias, Path(path))
            return original_scandir(path)

        with mock.patch.object(ops.os, "scandir", side_effect=scan_namespace):
            self.assertEqual([], list(ops.review_descriptor_paths(runs)))

    def test_descriptor_scan_rejects_redirected_roots_and_descriptors(self):
        runs = ops.state_root(self.root) / "runs"
        descriptor = ops.run_root(self.root, "stored") / "review" / ("e" * 64) / "descriptor.json"
        ops.atomic_json(descriptor, {"bundle": {}})
        original_redirect = ops.is_redirect
        for redirected in (runs.parent, runs, descriptor):
            with self.subTest(redirected=redirected), mock.patch.object(
                ops, "is_redirect", side_effect=lambda path: Path(path) == redirected or original_redirect(path)
            ):
                self.assertEqual([], list(ops.review_descriptor_paths(runs)))

    def test_cleanup_removes_only_expired_repository_owned_bundles(self):
        expired = ops.review_prepare(self.root, "expired", "origin/main", "HEAD", False)
        recent = ops.review_prepare(self.root, "recent", "origin/main", "HEAD", False)
        descriptor_path = Path(expired["artifact"])
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        descriptor["bundle"]["last_validated_at"] = "2000-01-01T00:00:00+00:00"
        ops.atomic_json(descriptor_path, descriptor)
        foreign = Path(expired["bundle"]["directory"]).parent / "foreign"
        foreign.mkdir()

        ops.cleanup_review_bundles(self.root)

        self.assertFalse(Path(expired["bundle"]["directory"]).exists())
        self.assertTrue(Path(recent["bundle"]["directory"]).is_dir())
        self.assertTrue(foreign.is_dir())

    def test_complete_legacy_bundle_migrates_without_changing_frozen_identity(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        descriptor_path = Path(descriptor["artifact"])
        stored = json.loads(descriptor_path.read_text(encoding="utf-8"))
        locations = ops.review_bundle_locations(self.root, "run-1", descriptor_path.parent.name)
        legacy = ops.legacy_review_bundle_locations(locations)
        for name in ("patch", "paths", "tree", "tree_archive", "identity"):
            shutil.move(str(Path(stored["bundle"][name])), str(legacy[name]))
        Path(stored["bundle"]["directory"]).rmdir()
        identity_sha = stored["bundle"]["identity_sha256"]
        stored["bundle"].update({name: str(legacy[name]) for name in (
            "directory", "patch", "paths", "tree", "tree_archive", "identity"
        )})
        ops.atomic_json(descriptor_path, stored)

        with mock.patch.object(ops, "remove_legacy_review_payload"):
            loaded = ops.load_descriptor(self.root, "run-1", descriptor_path)

        self.assertEqual(descriptor["descriptor_id"], loaded["descriptor_id"])
        self.assertEqual(identity_sha, loaded["bundle"]["identity_sha256"])
        self.assertTrue(Path(loaded["bundle"]["tree"]).is_dir())
        self.assertTrue(legacy["tree"].is_dir())
        ops.load_descriptor(self.root, "run-1", descriptor_path)
        self.assertFalse(legacy["tree"].exists())

    def test_absent_legacy_bundle_restores_the_stored_frozen_identity(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        descriptor_path = Path(descriptor["artifact"])
        stored = json.loads(descriptor_path.read_text(encoding="utf-8"))
        locations = ops.review_bundle_locations(self.root, "run-1", descriptor_path.parent.name)
        legacy = ops.legacy_review_bundle_locations(locations)
        identity = Path(stored["bundle"]["identity"]).read_bytes()
        shutil.rmtree(stored["bundle"]["directory"])
        stored["bundle"].update({name: str(legacy[name]) for name in (
            "directory", "patch", "paths", "tree", "tree_archive", "identity"
        )})
        ops.atomic_json(descriptor_path, stored)

        loaded = ops.load_descriptor(self.root, "run-1", descriptor_path)

        self.assertEqual(descriptor["descriptor_id"], loaded["descriptor_id"])
        self.assertEqual(identity, Path(loaded["bundle"]["identity"]).read_bytes())

    def test_interrupted_legacy_descriptor_publication_reuses_the_complete_external_bundle(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        descriptor_path = Path(descriptor["artifact"])
        stored = json.loads(descriptor_path.read_text(encoding="utf-8"))
        locations = ops.review_bundle_locations(self.root, "run-1", descriptor_path.parent.name)
        legacy = ops.legacy_review_bundle_locations(locations)
        for name in ("patch", "paths", "tree", "tree_archive", "identity"):
            shutil.move(str(Path(stored["bundle"][name])), str(legacy[name]))
        Path(stored["bundle"]["directory"]).rmdir()
        identity = legacy["identity"].read_bytes()
        stored["bundle"].update({name: str(legacy[name]) for name in (
            "directory", "patch", "paths", "tree", "tree_archive", "identity"
        )})
        ops.atomic_json(descriptor_path, stored)
        original_atomic_json = ops.atomic_json

        def interrupt_descriptor_publication(path, value):
            if Path(path) == descriptor_path and value["bundle"]["directory"] == str(locations["directory"]):
                raise OSError("interrupted publication")
            original_atomic_json(path, value)

        with mock.patch.object(ops, "atomic_json", side_effect=interrupt_descriptor_publication):
            with self.assertRaisesRegex(OSError, "interrupted publication"):
                ops.load_descriptor(self.root, "run-1", descriptor_path)

        loaded = ops.load_descriptor(self.root, "run-1", descriptor_path)

        self.assertEqual(descriptor["descriptor_id"], loaded["descriptor_id"])
        self.assertEqual(identity, Path(loaded["bundle"]["identity"]).read_bytes())
        self.assertFalse(legacy["tree"].exists())

    def test_tampered_legacy_bundle_is_not_rewritten(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        descriptor_path = Path(descriptor["artifact"])
        stored = json.loads(descriptor_path.read_text(encoding="utf-8"))
        locations = ops.review_bundle_locations(self.root, "run-1", descriptor_path.parent.name)
        legacy = ops.legacy_review_bundle_locations(locations)
        for name in ("patch", "paths", "tree", "tree_archive", "identity"):
            shutil.move(str(Path(stored["bundle"][name])), str(legacy[name]))
        Path(stored["bundle"]["directory"]).rmdir()
        stored["bundle"].update({name: str(legacy[name]) for name in (
            "directory", "patch", "paths", "tree", "tree_archive", "identity"
        )})
        ops.atomic_json(descriptor_path, stored)
        legacy["patch"].write_bytes(b"forged")

        with self.assertRaisesRegex(ops.WorkflowOperationError, "legacy review patch hash"):
            ops.load_descriptor(self.root, "run-1", descriptor_path)

        self.assertEqual(str(legacy["directory"]), json.loads(descriptor_path.read_text(encoding="utf-8"))["bundle"]["directory"])
        self.assertFalse(Path(descriptor["bundle"]["directory"]).exists())

    def test_redirected_legacy_candidate_directory_is_not_migrated(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        descriptor_path = Path(descriptor["artifact"])
        stored = json.loads(descriptor_path.read_text(encoding="utf-8"))
        locations = ops.review_bundle_locations(self.root, "run-1", descriptor_path.parent.name)
        legacy = ops.legacy_review_bundle_locations(locations)
        stored["bundle"].update({name: str(legacy[name]) for name in (
            "directory", "patch", "paths", "tree", "tree_archive", "identity"
        )})
        ops.atomic_json(descriptor_path, stored)
        original_redirect = ops.is_redirect

        with mock.patch.object(
            ops,
            "is_redirect",
            side_effect=lambda path: Path(path) == legacy["directory"] or original_redirect(path),
        ):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "descriptor namespace"):
                ops.load_descriptor(self.root, "run-1", descriptor_path)

        self.assertEqual(str(legacy["directory"]), json.loads(descriptor_path.read_text(encoding="utf-8"))["bundle"]["directory"])

    def test_review_run_cannot_be_reused_on_another_branch(self):
        ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        self.git("switch", "-q", "-c", "Feature/Another-review")

        with self.assertRaisesRegex(ops.WorkflowOperationError, "another branch"):
            ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)

        self.assertEqual(
            1,
            ops.review_prepare(self.root, "run-2", "origin/main", "HEAD", False)["waves"],
        )

    def test_review_prepare_resolves_rules_with_the_packaged_router(self):
        route_table = self.root / ".agents" / "skill-routes.json"
        route_table.write_text(
            json.dumps({"routes": [{"path": "^src/", "skills": ["feature"]}]}),
            encoding="utf-8",
        )
        candidate_router = self.root / ".agents" / "hooks" / "skill_router.py"
        candidate_router.parent.mkdir(parents=True)
        candidate_router.write_text(
            'import json\nprint(json.dumps({"skills": {"shadowed": []}}))\n',
            encoding="utf-8",
        )
        self.git("add", ".agents/skill-routes.json", ".agents/hooks/skill_router.py")
        self.git("commit", "-q", "-m", "add routing")

        result = ops.review_prepare(self.root, "routed-review", "origin/main", "HEAD", False)

        self.assertEqual(["feature"], [rule["name"] for rule in result["rules"]])
        self.assertEqual(".agents/skills/feature/SKILL.md", result["rules"][0]["path"])

    def test_review_prepare_keeps_plugin_owned_routes_and_deny_hits(self):
        (self.root / ".agents" / "skill-routes.json").write_text(json.dumps({"routes": [{
            "path": "^src/", "skills": ["dotnet:persistence"],
            "deny": [{"pattern": "candidate", "reason": "no candidate text"}],
        }]}), encoding="utf-8")
        self.git("add", ".agents/skill-routes.json")
        self.git("commit", "-q", "-m", "add plugin routing")

        result = ops.review_prepare(self.root, "plugin-routed", "origin/main", "HEAD", False)

        self.assertEqual([], result["rules"])
        self.assertEqual(["dotnet:persistence"], result["routed_skills"])
        self.assertEqual([["src/mapping.txt", "no candidate text"]], result["route_violations"])

    def test_opted_in_review_fails_visibly_when_router_runtime_is_missing(self):
        (self.root / ".agents" / "skill-routes.json").write_text(
            json.dumps({"routes": [{"path": "^src/", "skills": ["feature"]}]}),
            encoding="utf-8",
        )
        original = ops.__file__
        ops.__file__ = str(self.root / "absent-package" / "workflows" / "workflow_ops.py")
        try:
            with self.assertRaisesRegex(ops.WorkflowOperationError, "has no skill_router.py"):
                ops.routed_skills(self.root, ["src/mapping.txt"])
        finally:
            ops.__file__ = original
    def test_tampered_review_artifact_is_rejected(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        Path(descriptor["bundle"]["patch"]).write_bytes(b"forged")
        with self.assertRaisesRegex(ops.WorkflowOperationError, "patch hash"):
            ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

    def test_tampered_materialized_tree_is_rejected(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        tree_file = Path(descriptor["bundle"]["tree"]) / "src" / "mapping.txt"
        tree_file.write_text("forged\n", encoding="utf-8")
        with self.assertRaisesRegex(ops.WorkflowOperationError, "materialized review tree"):
            ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

    def test_tampered_tree_archive_is_rejected(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        Path(descriptor["bundle"]["tree_archive"]).write_bytes(b"forged")
        with self.assertRaisesRegex(ops.WorkflowOperationError, "tree archive hash"):
            ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

    def test_descriptor_outside_the_bound_run_is_rejected(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        copied = self.root / "descriptor.json"
        copied.write_text(Path(descriptor["artifact"]).read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaisesRegex(ops.WorkflowOperationError, "outside"):
            ops.review_reconcile(self.root, "run-1", copied, "origin/main")

    def test_unrelated_base_movement_does_not_restart_source_review(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        descriptor_path = descriptor["artifact"]
        tree = self.git("rev-parse", f"{self.base}^{{tree}}")
        moved = self.git("commit-tree", tree, "-p", self.base, "-m", "unrelated empty base move")
        self.git("update-ref", "refs/remotes/origin/main", moved)
        result = ops.review_reconcile(self.root, "run-1", descriptor_path, "origin/main")
        self.assertTrue(result["base_moved"])
        self.assertTrue(result["exact_head"])
        self.assertFalse(result["review_required"])

    def test_base_already_merged_into_frozen_head_does_not_restart_review(self):
        self.git("switch", "-q", "main")
        moved = self.commit("src/main.txt", "base advance\n", "base advance")
        self.git("switch", "-q", "Feature/Workflow-ops")
        self.git("merge", "-q", "--no-edit", moved)
        descriptor = ops.review_prepare(self.root, "run-1", self.base, "HEAD", False)
        self.git("update-ref", "refs/remotes/origin/main", moved)

        result = ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

        self.assertFalse(result["base_moved"])
        self.assertTrue(result["exact_head"])
        self.assertFalse(result["review_required"])

    def test_relevant_base_movement_requires_incremental_review(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        self.git("switch", "-q", "main")
        moved = self.commit("src/mapping.txt", "base change\n", "relevant base change")
        self.git("switch", "-q", "Feature/Workflow-ops")
        self.git("update-ref", "refs/remotes/origin/main", moved)

        result = ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")

        self.assertTrue(result["base_moved"])
        self.assertTrue(result["review_required"])
        self.assertIn("base-changed-relevant-evidence", result["reasons"])

    def test_head_movement_requires_incremental_review(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        self.commit("src/second.txt", "later\n", "later candidate")
        result = ops.review_reconcile(self.root, "run-1", descriptor["artifact"], "origin/main")
        self.assertTrue(result["review_required"])
        self.assertIn("candidate-head-changed", result["reasons"])

    def test_delivery_preflight_preserves_review_after_unrelated_base_movement(self):
        descriptor = ops.review_prepare(self.root, "run-1", "origin/main", "HEAD", False)
        tree = self.git("rev-parse", f"{self.base}^{{tree}}")
        moved = self.git("commit-tree", tree, "-p", self.base, "-m", "unrelated empty base move")
        self.git("update-ref", "refs/remotes/origin/main", moved)
        with mock.patch.object(ops, "delivery_owner", return_value={"action": "create"}):
            result = ops.delivery_preflight(self.root, "run-1", descriptor["artifact"], "origin/main")
        self.assertTrue(result["ready"])
        self.assertEqual([], result["blockers"])

    def test_delivery_preflight_blocks_base_movement_before_review(self):
        tree = self.git("rev-parse", f"{self.base}^{{tree}}")
        moved = self.git("commit-tree", tree, "-p", self.base, "-m", "base move")
        self.git("update-ref", "refs/remotes/origin/main", moved)
        with mock.patch.object(ops, "delivery_owner", return_value={"action": "create"}):
            result = ops.delivery_preflight(self.root, "run-1", None, "origin/main")
        self.assertFalse(result["ready"])
        self.assertIn("base-ahead-before-final-review", result["blockers"])


class DeliveryOwnershipTests(RepositoryFixture):
    def setUp(self):
        super().setUp()
        self.url = "https://github.com/example/workflow-fixture/pull/12"
        self.pr = {"number": 12, "url": self.url, "headRefName": "Feature/Delivery",
                   "headRefOid": self.base, "baseRefName": "main", "state": "OPEN",
                   "isCrossRepository": False}
        self.branch_prs = []
        self.forge_commands = []
        original = ops.run_process

        def run(arguments, root, **kwargs):
            if arguments[0] != "gh":
                return original(arguments, root, **kwargs)
            self.forge_commands.append(arguments)
            payload = self.pr if arguments[2] == "view" else self.branch_prs
            return subprocess.CompletedProcess(arguments, 0, json.dumps(payload), "")

        patcher = mock.patch.object(ops, "run_process", side_effect=run)
        patcher.start()
        self.addCleanup(patcher.stop)

    def ledger(self, pr):
        path = "plans/work/WORK_PROGRESS.md"
        self.commit("plans/work/WORK_PLAN.md", "# Work\n", "plan")
        self.commit("plans/work/WORK_ROADMAP.md", "# Roadmap\n", "roadmap")
        self.commit(path, "\n".join([
            "# Work progress", "- Plan: `plans/work/WORK_PLAN.md`",
            "- Roadmap: `plans/work/WORK_ROADMAP.md`", "- Roadmap item: `work/slice`",
            f"- Worktree: `{self.root}`", f"- Branch: `{self.git('branch', '--show-current')}`",
            f"- PR: `{pr}`", "", "## Next Steps", "", "Publish the verified correction.",
            "Scope: whole plan", "Current slice: repair the existing delivery",
            "Remaining scope: publish and review", "Done when: the owning review contains the repair",
        ]) + "\n", "checkpoint")
        return path

    def test_correction_on_another_branch_routes_to_the_recorded_review(self):
        ledger = self.ledger(self.url)
        result = ops.delivery_preflight(self.root, "repair", None, None, ledger)
        self.assertEqual("integrate", result["ownership"]["action"])
        self.assertEqual(self.url, result["ownership"]["pr_url"])
        self.assertEqual("Feature/Delivery", result["ownership"]["branch"])
        self.assertFalse(result["ready"])
        self.assertIn("delivery-integrate", result["blockers"])
        self.assertEqual("view", self.forge_commands[0][2])
        self.assertEqual(1, len(self.forge_commands))

    def test_handoff_keeps_review_identity_when_execution_moves(self):
        ledger = self.ledger(self.url)
        successor = self.root.parent / "successor"
        self.git("worktree", "add", "-q", "-b", "Fix/Successor", str(successor))
        path = successor / ledger
        text = path.read_text(encoding="utf-8").replace("Feature/Workflow-ops", "Fix/Successor")
        path.write_text(text.replace(str(self.root), str(successor)), encoding="utf-8")
        result = ops.delivery_preflight(successor, "successor-run", None, None, ledger)
        self.assertEqual("Fix/Successor", result["identity"]["branch"])
        self.assertEqual(self.url, result["ownership"]["pr_url"])
        self.assertEqual("integrate", result["ownership"]["action"])

    def test_separately_assessed_slice_can_create_its_own_review(self):
        ledger = self.ledger("not opened")
        result = ops.delivery_preflight(self.root, "new-slice", None, "origin/main", ledger)
        self.assertEqual("create", result["ownership"]["action"])
        self.assertTrue(result["ready"])
        self.assertEqual("list", self.forge_commands[0][2])

    def test_branch_without_a_review_leaves_scope_to_assess(self):
        result = ops.delivery_preflight(self.root, "unknown", None, "origin/main")
        self.assertEqual("assess-scope", result["ownership"]["action"])
        self.assertFalse(result["ready"])

    def test_untracked_document_directory_does_not_obscure_the_ownership_route(self):
        path = self.root / "plans" / "notes"
        path.mkdir(parents=True)
        (path / "WORK PLAN.md").write_text("# Separate notes\n", encoding="utf-8")
        result = ops.delivery_preflight(self.root, "notes", None, "origin/main")
        self.assertEqual(["delivery-assess-scope"], result["blockers"])
        self.assertEqual(["plans/notes/WORK PLAN.md"], result["documentation_dirty_paths"])
        (path / "script.py").write_text("print('unfinished')\n", encoding="utf-8")
        result = ops.delivery_preflight(self.root, "mixed", None, "origin/main")
        self.assertIn("uncommitted-code", result["blockers"])
        self.assertEqual(["plans/notes/script.py"], result["code_dirty_paths"])

    def test_current_review_is_reused_when_the_ledger_has_not_caught_up(self):
        ledger = self.ledger("not opened")
        self.pr["headRefName"] = self.git("branch", "--show-current")
        self.branch_prs = [self.pr]
        result = ops.delivery_preflight(self.root, "existing", None, None, ledger)
        self.assertEqual("update", result["ownership"]["action"])
        self.assertEqual(self.url, result["ownership"]["pr_url"])
        self.assertTrue(result["ready"])

    def test_closed_review_is_reconciled_instead_of_replaced(self):
        self.pr["state"] = "MERGED"
        result = ops.delivery_preflight(self.root, "closed", None, None, pr_url=self.url)
        self.assertEqual("reconcile-review", result["ownership"]["action"])
        self.assertFalse(result["ready"])

    def test_fork_review_requires_reconciliation_even_with_the_same_branch_name(self):
        self.pr["isCrossRepository"] = True
        self.pr["headRefName"] = self.git("branch", "--show-current")
        result = ops.delivery_preflight(self.root, "fork", None, None, pr_url=self.url)
        self.assertEqual("reconcile-review", result["ownership"]["action"])
        self.assertFalse(result["ready"])

    def test_conflicting_recorded_owners_require_reconciliation(self):
        ledger = self.ledger(self.url)
        with self.assertRaisesRegex(ops.WorkflowOperationError, "owners disagree"):
            ops.delivery_preflight(self.root, "conflict", None, None, ledger, self.url + "3")
        self.assertEqual([], self.forge_commands)

    def test_foreign_repository_owner_is_rejected_before_forge_access(self):
        with self.assertRaisesRegex(ops.WorkflowOperationError, "this repository"):
            ops.delivery_preflight(self.root, "foreign", None, None,
                                   pr_url="https://github.com/another/repo/pull/12")
        self.assertEqual([], self.forge_commands)

    def test_forge_failure_is_not_an_empty_branch_lookup(self):
        original = ops.run_process

        def unavailable(arguments, root, **kwargs):
            if arguments[0] == "gh":
                raise ops.WorkflowOperationError("forge unavailable")
            return original(arguments, root, **kwargs)

        with mock.patch.object(ops, "run_process", side_effect=unavailable):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "forge unavailable"):
                ops.delivery_owner(self.root, "offline")

    def test_existing_delivery_binding_resolves_the_review_before_branch_lookup(self):
        binding = {
            "repository": "example/workflow-fixture", "pr_url": self.url, "pr_number": 12,
            "worktree": str(self.root), "branch": "Feature/Delivery", "remote_head_sha": self.base,
            "pending_evidence": [],
            "review": {"work_order": "reviews/Feature-Delivery.md",
                       "work_order_order": ["native-general"], "reviewed_sha": None},
            "merge_authorization": {"mode": "absent", "instruction": None},
            "completion_condition": "review completes",
        }
        artifact = ops.delivery_runtime.artifact_from_binding(binding)
        (self.root / ops.delivery_runtime.BINDING_FILE).write_text(json.dumps(artifact), encoding="utf-8")
        result = ops.delivery_owner(self.root, "bound-correction")
        self.assertEqual("binding", result["source"])
        self.assertEqual("integrate", result["action"])
        self.assertEqual(self.url, result["pr_url"])
        with self.assertRaisesRegex(ops.WorkflowOperationError, "owners disagree"):
            ops.delivery_owner(self.root, "conflict", pr_url=self.url + "3")

    def test_recorded_stack_base_is_used_for_preflight(self):
        self.pr["headRefName"] = self.git("branch", "--show-current")
        self.pr["baseRefName"] = "Feature/Parent"
        self.git("update-ref", "refs/remotes/origin/Feature/Parent", self.base)
        result = ops.delivery_preflight(self.root, "stack", None, None, pr_url=self.url)
        self.assertTrue(result["ready"])
        self.assertEqual("Feature/Parent", result["ownership"]["base"])

    def test_cli_returns_a_blocked_exit_for_a_correction_branch(self):
        ledger = self.ledger(self.url)
        with mock.patch.object(ops, "emit") as emit:
            code = ops.main(["--root", str(self.root), "--workflow-run-id", "cli", "delivery-preflight",
                             "--ledger", ledger])
        self.assertEqual(1, code)
        self.assertEqual("integrate", emit.call_args.args[0]["ownership"]["action"])


class ChangedPathsTests(RepositoryFixture):
    def test_large_pull_uses_the_paginated_files_endpoint(self):
        paths = [f"src/file-{index:03}.txt" for index in range(658)]
        completed = subprocess.CompletedProcess([], 0, "\n".join(reversed(paths)) + "\n", "")
        with mock.patch.object(ops, "repository_slug", return_value="example/workflow-fixture"), \
                mock.patch.object(ops, "run_process", return_value=completed) as run:
            actual = ops.changed_paths(self.root, 12, paths[:100], 658)

        self.assertEqual(sorted(paths), actual)
        run.assert_called_once_with(
            [
                "gh",
                "api",
                "--paginate",
                "repos/example/workflow-fixture/pulls/12/files?per_page=100",
                "--jq",
                ".[].filename",
            ],
            self.root,
            check=False,
        )

    def test_paginated_files_must_match_the_authoritative_changed_file_count(self):
        completed = subprocess.CompletedProcess([], 0, "src/one.txt\n", "")
        with mock.patch.object(ops, "repository_slug", return_value="example/workflow-fixture"), \
                mock.patch.object(ops, "run_process", return_value=completed):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "returned 1 of 2"):
                ops.changed_paths(self.root, 12, ["src/one.txt"], 2)
    def test_paginated_files_must_include_every_reported_path(self):
        completed = subprocess.CompletedProcess([], 0, "src/one.txt\n", "")
        with mock.patch.object(ops, "repository_slug", return_value="example/workflow-fixture"), \
                mock.patch.object(ops, "run_process", return_value=completed):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "missing reported paths"):
                ops.changed_paths(self.root, 12, ["src/one.txt", "src/two.txt"])

class MonitorTests(RepositoryFixture):
    def observer(self, values):
        remaining = iter(values)
        last = values[-1]

        def observe(_root, _identity):
            nonlocal last
            last = next(remaining, last)
            return last

        return observe

    def test_monitor_persists_exact_identity_and_emits_only_after_transition(self):
        observer = self.observer(
            [
                {"state": "in_progress", "conclusion": None},
                {"state": "in_progress", "conclusion": None},
                {"state": "completed", "conclusion": "success"},
            ]
        )
        result = ops.monitor_remote(
            self.root,
            "run-1",
            "run",
            "42",
            "HEAD",
            "ci",
            1,
            0.001,
            2,
            observer,
        )
        self.assertEqual("terminal", result["transition"])
        self.assertEqual(3, result["queries"])
        self.assertEqual(self.head_or_base(), result["identity"]["head"])
        state = json.loads(Path(result["state_artifact"]).read_text(encoding="utf-8"))
        self.assertEqual("example/workflow-fixture", state["identity"]["repository"])
        self.assertEqual("42", state["identity"]["target_id"])

    def test_monitor_reconnects_to_the_same_identity(self):
        observer = self.observer(
            [
                {"state": "in_progress", "conclusion": None},
                {"state": "queued", "conclusion": None},
            ]
        )
        first = ops.monitor_remote(self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2, observer)
        second = ops.monitor_remote(self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2, observer)
        self.assertFalse(first["reconnected"])
        self.assertTrue(second["reconnected"])
        self.assertEqual(first["monitor_id"], second["monitor_id"])

    def test_a_second_live_monitor_for_the_same_identity_is_refused(self):
        identity = ops.remote_identity(self.root, "run", "42", "HEAD", "ci", 1)
        monitor_id = ops.digest(identity)
        lock = ops.state_root(self.root) / "monitors" / f"{monitor_id}.lock"
        observer = self.observer([{"state": "completed", "conclusion": "success"}])
        with ops.MonitorLease(lock):
            with self.assertRaisesRegex(ops.WorkflowOperationError, "another process"):
                ops.monitor_remote(self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2, observer)

    def test_completed_run_is_observed_after_disconnect_and_suspension(self):
        scenario = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        observations = scenario["completed_run_while_disconnected"]
        first_observer = self.observer(observations["before_disconnect"])
        first = ops.monitor_remote(self.root, "run-1", "run", "42", "HEAD", "ci", 1, 0.001, 2, first_observer)
        state_path = Path(first["state_artifact"])
        state = json.loads(state_path.read_text(encoding="utf-8"))
        suspension = scenario["machine_suspension"]
        state["last_observed_at"] -= suspension["elapsed_seconds"]
        ops.atomic_json(state_path, state)
        second_observer = self.observer(observations["after_reconnect"])
        second = ops.monitor_remote(
            self.root,
            "run-1",
            "run",
            "42",
            "HEAD",
            "ci",
            1,
            suspension["poll_seconds"],
            2,
            second_observer,
        )
        self.assertTrue(second["reconnected"])
        self.assertTrue(second["terminal"])
        self.assertEqual("success", second["observation"]["conclusion"])
        self.assertGreaterEqual(second["timing"]["suspended_offline_seconds"], suspension["minimum_offline_seconds"])

    def head_or_base(self):
        return self.git("rev-parse", "HEAD")


class TelemetryTests(RepositoryFixture):
    def transcript(self):
        path = Path(self.temp.name) / "session.jsonl"
        records = [
            {
                "timestamp": "2026-09-09T10:00:00Z",
                "type": "token_usage_record",
                "payload": {
                    "turn_id": "turn-1",
                    "thread_token_usage": {
                        "input_tokens": 1000,
                        "cached_input_tokens": 800,
                        "output_tokens": 50,
                    },
                },
            },
            {
                "timestamp": "2026-09-09T10:00:01Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "call-1",
                    "name": "wait",
                    "arguments": "{}",
                },
            },
            {
                "timestamp": "2026-09-09T10:00:03Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "call-1",
                },
            },
            {
                "timestamp": "2026-09-09T10:10:03Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "call_id": "call-2",
                    "name": "exec",
                    "input": "Get-Content skill/SKILL.md",
                },
            },
            {
                "timestamp": "2026-09-09T10:10:04Z",
                "type": "token_usage_record",
                "payload": {
                    "turn_id": "turn-2",
                    "thread_token_usage": {
                        "input_tokens": 1500,
                        "cached_input_tokens": 1200,
                        "output_tokens": 75,
                    },
                },
            },
        ]
        path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        return path

    def test_transcript_metrics_separate_cached_usage_and_offline_time(self):
        metrics = ops.transcript_telemetry(self.transcript(), "codex", 300)
        self.assertEqual(2, metrics["model_turns"])
        self.assertEqual(2, metrics["tool_calls"])
        self.assertEqual(1, metrics["wait_poll_calls"])
        self.assertEqual(1, metrics["skill_load_calls"])
        self.assertEqual(300, metrics["uncached_input_tokens"])
        self.assertEqual(1200, metrics["cached_input_tokens"])
        self.assertEqual(75, metrics["output_tokens"])
        self.assertGreaterEqual(metrics["suspended_offline_seconds"], 600)

    def test_incident_scale_metrics_breach_soft_and_hard_budgets(self):
        metrics = {
            "model_turns": 468,
            "tool_calls": 439,
            "wait_poll_calls": 222,
            "uncached_input_tokens": 700000,
            "cached_input_tokens": 54300000,
            "output_tokens": 92000,
            "active_execution_seconds": 20000,
            "remote_waiting_seconds": 5269,
            "suspended_offline_seconds": 24720,
            "skill_load_calls": 28,
        }
        budget = json.loads((OPERATIONS.parent / "budgets.json").read_text(encoding="utf-8"))
        result = ops.budget_result(metrics, budget)
        self.assertFalse(result["allowed"])
        breached = {item["metric"] for item in result["breaches"]}
        self.assertIn("wait_poll_calls", breached)
        self.assertIn("cached_input_tokens", breached)
        self.assertIn("suspended_offline_seconds", breached)

    def test_codex_reasoning_items_and_nested_waits_are_counted(self):
        path = Path(self.temp.name) / "codex-session.jsonl"
        records = [
            {"type": "response_item", "payload": {"type": "reasoning"}},
            {"type": "response_item", "payload": {"type": "reasoning"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "call_id": "call-1",
                    "name": "exec",
                    "input": "await tools.write_stdin({session_id: 1});",
                },
            },
        ]
        path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")
        metrics = ops.transcript_telemetry(path, "codex", 300)
        self.assertEqual(2, metrics["model_turns"])
        self.assertEqual(1, metrics["wait_poll_calls"])


if __name__ == "__main__":
    unittest.main()
