import importlib.util
import json
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".agents" / "workflows"))
SPEC = importlib.util.spec_from_file_location("auto_merge", ROOT / ".agents/workflows/auto_merge.py")
AUTO_MERGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUTO_MERGE)


HEAD = "a" * 40


class AutoMergeTests(unittest.TestCase):
    def binding(self, root):
        return {
            "repository": "example/repository",
            "pr_number": 42,
            "worktree": str(root),
            "branch": "feature/auto-merge",
            "remote_head_sha": HEAD,
            "auto_merge": True,
            "merge_authorization": {"mode": "auto", "instruction": "merge when green"},
        }

    def test_cli_requires_only_an_absolute_root_argument(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertEqual(root.resolve(), AUTO_MERGE.parse_root(["auto_merge.py", "--root", str(root)]))
        for argv in (
            ["auto_merge.py"],
            ["auto_merge.py", "--root", "relative"],
            ["auto_merge.py", "--root", "C:/root", "extra"],
            ["auto_merge.py", "--other", "C:/root"],
        ):
            with self.subTest(argv=argv):
                with self.assertRaises(AUTO_MERGE.AutoMergeError):
                    AUTO_MERGE.parse_root(argv)

    def test_readiness_rejects_empty_pending_or_failed_checks(self):
        base = {"state": "OPEN", "isDraft": False, "mergeStateStatus": "CLEAN", "headRefOid": HEAD}
        for rollup in ([], [{"status": "IN_PROGRESS", "conclusion": ""}], [{"status": "COMPLETED", "conclusion": "FAILURE"}]):
            with self.subTest(rollup=rollup):
                with self.assertRaises(AUTO_MERGE.AutoMergeError):
                    AUTO_MERGE.green_exact_head({**base, "statusCheckRollup": rollup}, HEAD)

    def test_readiness_rejects_closed_draft_wrong_head_and_ineligible_base(self):
        base = {
            "state": "OPEN", "isDraft": False, "mergeStateStatus": "CLEAN", "headRefOid": HEAD,
            "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}],
        }
        for changed in (
            {"state": "CLOSED"}, {"isDraft": True}, {"headRefOid": "b" * 40},
            {"mergeStateStatus": "BEHIND"},
        ):
            with self.subTest(changed=changed), self.assertRaises(AUTO_MERGE.AutoMergeError):
                AUTO_MERGE.green_exact_head({**base, **changed}, HEAD)

    def test_arm_executes_only_the_fixed_guarded_merge_arguments(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            binding = self.binding(root)
            observed = {
                "number": 42,
                "headRefName": binding["branch"],
                "headRefOid": HEAD,
                "state": "OPEN",
                "isDraft": False,
                "mergeStateStatus": "CLEAN",
                "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}],
            }
            with (
                patch.object(AUTO_MERGE, "read_binding", return_value=binding),
                patch.object(AUTO_MERGE, "exact_local_identity"),
                patch.object(AUTO_MERGE.workflow_ops, "pull_request_state", return_value=observed),
                patch.object(AUTO_MERGE, "current_authorization", return_value=["README.md"]),
                patch.object(AUTO_MERGE, "current_review"),
                patch.object(AUTO_MERGE.workflow_ops, "run_process") as run_process,
            ):
                AUTO_MERGE.arm(root)
            self.assertEqual(
                [
                    "gh", "pr", "merge", "42", "--repo", "example/repository", "--merge", "--auto",
                    "--match-head-commit", HEAD,
                ],
                run_process.call_args.args[0],
            )
            self.assertEqual(root, run_process.call_args.args[1])

    def test_arm_never_runs_merge_when_any_live_gate_rejects(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            binding = self.binding(root)
            observed = {
                "number": 42, "headRefName": binding["branch"], "headRefOid": HEAD,
                "state": "OPEN", "isDraft": False, "mergeStateStatus": "CLEAN",
                "statusCheckRollup": [{"status": "COMPLETED", "conclusion": "SUCCESS"}],
            }
            for name in ("exact_local_identity", "green_exact_head", "current_authorization", "current_review"):
                with self.subTest(name=name), patch.object(AUTO_MERGE, "read_binding", return_value=binding), \
                     patch.object(AUTO_MERGE.workflow_ops, "pull_request_state", return_value=observed), \
                     patch.object(AUTO_MERGE.workflow_ops, "run_process") as run_process, \
                     patch.object(AUTO_MERGE, name, side_effect=AUTO_MERGE.AutoMergeError(name)):
                    with self.assertRaises(AUTO_MERGE.AutoMergeError):
                        AUTO_MERGE.arm(root)
                    self.assertFalse(
                        any(call.args[0][0] == "gh" for call in run_process.call_args_list)
                    )

    def test_current_authorization_rechecks_opt_in_authority_and_every_stop(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            (root / ".agents").mkdir()
            binding = self.binding(root)
            value = {"files": [{"path": "README.md"}], "changedFiles": 1, "labels": []}
            policy = root / ".agents" / "delivery-authorization.json"
            base = {"standing_authorization": "auto", "instruction": "merge when green"}
            with patch.object(AUTO_MERGE.workflow_ops, "changed_paths", return_value=["README.md"]), \
                 patch.object(AUTO_MERGE.workflow_ops, "scoped_approval", return_value=None):
                for declared in (None, False):
                    with self.subTest(auto_merge=declared):
                        current = dict(base)
                        if declared is not None:
                            current["auto_merge"] = declared
                        policy.write_text(json.dumps(current), encoding="utf-8")
                        with self.assertRaisesRegex(AUTO_MERGE.AutoMergeError, "not enabled"):
                            AUTO_MERGE.current_authorization(root, binding, value)
                policy.write_text(json.dumps({**base, "auto_merge": True}), encoding="utf-8")
                self.assertEqual(["README.md"], AUTO_MERGE.current_authorization(root, binding, value))
                stops = [
                    ".agents/delivery-authorization.json", ".github/workflows/check.yml", "db/migrations/1.sql",
                    "identity/token.py", "billing/invoice.py", "contracts/api.json", "private/handler.py",
                ]
                for path in stops:
                    with self.subTest(stop=path), patch.object(AUTO_MERGE.workflow_ops, "changed_paths", return_value=[path]):
                        if path == "private/handler.py":
                            policy.write_text(json.dumps({**base, "auto_merge": True, "always_stop_paths": [r"^private/"]}), encoding="utf-8")
                        else:
                            policy.write_text(json.dumps({**base, "auto_merge": True}), encoding="utf-8")
                        with self.assertRaisesRegex(AUTO_MERGE.AutoMergeError, "authorization"):
                            AUTO_MERGE.current_authorization(root, binding, value)
                policy.write_text(json.dumps({**base, "auto_merge": True, "hold_label": "hold"}), encoding="utf-8")
                with patch.object(AUTO_MERGE.workflow_ops, "changed_paths", return_value=["README.md"]):
                    with self.assertRaisesRegex(AUTO_MERGE.AutoMergeError, "authorization"):
                        AUTO_MERGE.current_authorization(root, binding, {**value, "labels": [{"name": "hold"}]})

    def test_current_review_rejects_missing_stale_open_and_missing_security_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            (root / ".agents").mkdir()
            (root / ".agents" / "merge-gate.json").write_text(json.dumps({"security_paths": []}), encoding="utf-8")
            binding = self.binding(root)
            clean = f"**Reviewed up to commit:** `{HEAD}`\n- [x] complete\n"
            cases = [
                (SimpleNamespace(returncode=1, stdout=""), [], "absent"),
                (SimpleNamespace(returncode=0, stdout=f"**Reviewed up to commit:** `{'b' * 40}`\n"), [], "stale"),
                (SimpleNamespace(returncode=0, stdout=clean + "- [ ] finding\n"), [], "unresolved"),
                (SimpleNamespace(returncode=0, stdout=clean), ["authorization/token.py"], "security"),
            ]
            for result, changed, message in cases:
                with self.subTest(message=message), patch.object(AUTO_MERGE.workflow_ops, "run_process", return_value=result), \
                     patch.object(AUTO_MERGE.merge_review_gate, "security_no_longer_covered", return_value=True):
                    with self.assertRaisesRegex(AUTO_MERGE.AutoMergeError, message):
                        AUTO_MERGE.current_review(root, binding, changed)

    def test_current_review_uses_the_local_canonical_work_order_when_head_tree_lacks_it(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            (root / ".agents").mkdir()
            (root / ".agents" / "merge-gate.json").write_text(json.dumps({"security_paths": []}), encoding="utf-8")
            binding = self.binding(root)
            review = root / "reviews" / "feature-auto-merge.md"
            review.parent.mkdir()
            review.write_text(f"**Reviewed up to commit:** `{HEAD}`\n- [x] complete\n", encoding="utf-8")
            with patch.object(AUTO_MERGE.workflow_ops, "run_process", return_value=SimpleNamespace(returncode=1, stdout="")):
                AUTO_MERGE.current_review(root, binding, [])

    def test_local_canonical_review_fallback_rejects_stale_findings_and_missing_security(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            (root / ".agents").mkdir()
            (root / ".agents" / "merge-gate.json").write_text(json.dumps({"security_paths": []}), encoding="utf-8")
            binding = self.binding(root)
            review = root / "reviews" / "feature-auto-merge.md"
            review.parent.mkdir()
            clean = f"**Reviewed up to commit:** `{HEAD}`\n- [x] complete\n"
            cases = [
                (f"**Reviewed up to commit:** `{'b' * 40}`\n", [], "stale"),
                (clean + "- [ ] unresolved\n", [], "unresolved"),
                (clean, ["authorization/token.py"], "security"),
            ]
            for content, changed, message in cases:
                with self.subTest(message=message):
                    review.write_text(content, encoding="utf-8")
                    with patch.object(AUTO_MERGE.workflow_ops, "run_process", return_value=SimpleNamespace(returncode=1, stdout="")), \
                         patch.object(AUTO_MERGE.merge_review_gate, "security_no_longer_covered", return_value=True):
                        with self.assertRaisesRegex(AUTO_MERGE.AutoMergeError, message):
                            AUTO_MERGE.current_review(root, binding, changed)


if __name__ == "__main__":
    unittest.main()
