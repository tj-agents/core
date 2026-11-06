import os
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

HOOK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOK_ROOT))

import hook_runtime


class PayloadRootResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.payload_root = self.root / "plugin"
        self.hook = self.payload_root / "hooks" / "hook.py"
        self.hook.parent.mkdir(parents=True)
        self.hook.touch()

    def test_each_harness_root_resolves_when_it_owns_the_hook(self):
        for name in hook_runtime.PLUGIN_ROOT_VARIABLES:
            with self.subTest(name=name), patch.dict(
                os.environ, {name: str(self.payload_root)}, clear=True
            ):
                self.assertEqual(
                    self.payload_root, hook_runtime.declared_plugin_root(self.hook)
                )
                self.assertEqual(
                    self.payload_root, hook_runtime.own_payload_root(self.hook)
                )

    def test_each_unrelated_harness_root_falls_back_beside_the_hook(self):
        unrelated = self.root / "unrelated"
        unrelated.mkdir()

        for name in hook_runtime.PLUGIN_ROOT_VARIABLES:
            with self.subTest(name=name), patch.dict(
                os.environ, {name: str(unrelated)}, clear=True
            ):
                self.assertEqual(
                    self.payload_root, hook_runtime.own_payload_root(self.hook)
                )

    def test_workspace_ancestor_is_not_a_declared_plugin_root(self):
        with patch.dict(os.environ, {"PLUGIN_ROOT": str(self.root)}, clear=True):
            self.assertIsNone(hook_runtime.declared_plugin_root(self.hook))
            self.assertEqual(self.payload_root, hook_runtime.own_payload_root(self.hook))

    def test_hook_file_itself_is_not_a_declared_plugin_root(self):
        with patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": str(self.hook)}, clear=True):
            self.assertIsNone(hook_runtime.declared_plugin_root(self.hook))
            self.assertEqual(self.payload_root, hook_runtime.own_payload_root(self.hook))

    def test_unrelated_earlier_root_does_not_hide_a_later_valid_root(self):
        unrelated = self.root / "unrelated"
        unrelated.mkdir()

        with patch.dict(
            os.environ,
            {
                "PLUGIN_ROOT": str(unrelated),
                "CLAUDE_PLUGIN_ROOT": str(self.payload_root),
            },
            clear=True,
        ):
            self.assertEqual(self.payload_root, hook_runtime.own_payload_root(self.hook))


class ClaimRetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.temp_patch = patch.object(
            hook_runtime.tempfile, "gettempdir", return_value=str(self.root)
        )
        self.temp_patch.start()
        self.addCleanup(self.temp_patch.stop)

    def payload(self, tool_use_id):
        return {
            "hook_event_name": "PreToolUse",
            "session_id": "retention-session",
            "tool_use_id": tool_use_id,
        }

    def test_claim_prunes_expired_claims_and_keeps_recent_claims(self):
        stale = self.root / f"{hook_runtime.CLAIM_PREFIX}stale.claim"
        recent = self.root / f"{hook_runtime.CLAIM_PREFIX}recent.claim"
        stale.write_text("stale", encoding="utf-8")
        recent.write_text("recent", encoding="utf-8")
        expired = time.time() - hook_runtime.CLAIM_RETENTION_SECONDS - 1
        os.utime(stale, (expired, expired))

        self.assertTrue(hook_runtime.claim_invocation(self.payload("cleanup"), "router"))

        self.assertFalse(stale.exists())
        self.assertTrue(recent.exists())
        self.assertTrue((self.root / hook_runtime.PRUNE_LOCK_NAME).exists())
        self.assertTrue((self.root / hook_runtime.PRUNE_MARKER_NAME).exists())

    def test_repeated_claims_do_not_lock_or_scan_before_pruning_is_due(self):
        with patch.object(
            hook_runtime,
            "_try_acquire_prune_lock",
            wraps=hook_runtime._try_acquire_prune_lock,
        ) as acquire, patch.object(
            hook_runtime,
            "_remove_expired_claims",
            wraps=hook_runtime._remove_expired_claims,
        ) as scan:
            self.assertTrue(hook_runtime.claim_invocation(self.payload("first"), "router"))
            self.assertTrue(hook_runtime.claim_invocation(self.payload("second"), "router"))

        self.assertEqual(1, acquire.call_count)
        self.assertEqual(1, scan.call_count)

    def test_due_pruning_recovers_after_lock_contention(self):
        stale = self.root / f"{hook_runtime.CLAIM_PREFIX}stale.claim"
        stale.write_text("stale", encoding="utf-8")
        expired = time.time() - hook_runtime.CLAIM_RETENTION_SECONDS - 1
        os.utime(stale, (expired, expired))

        with patch.object(hook_runtime, "_try_acquire_prune_lock", return_value=None):
            self.assertTrue(hook_runtime.claim_invocation(self.payload("contended"), "router"))

        self.assertTrue(stale.exists())
        self.assertFalse((self.root / hook_runtime.PRUNE_MARKER_NAME).exists())
        self.assertTrue(hook_runtime.claim_invocation(self.payload("retry"), "router"))
        self.assertFalse(stale.exists())
        self.assertTrue((self.root / hook_runtime.PRUNE_MARKER_NAME).exists())

    def test_expired_current_claim_remains_suppressive_until_another_invocation_prunes_it(self):
        payload = self.payload("same-call")
        self.assertTrue(hook_runtime.claim_invocation(payload, "router"))
        claim = next(self.root.glob(f"{hook_runtime.CLAIM_PREFIX}*.claim"))
        expired = time.time() - hook_runtime.CLAIM_RETENTION_SECONDS - 1
        os.utime(claim, (expired, expired))
        marker = self.root / hook_runtime.PRUNE_MARKER_NAME
        due = time.time() - hook_runtime.CLAIM_PRUNE_INTERVAL_SECONDS - 1
        os.utime(marker, (due, due))

        self.assertFalse(hook_runtime.claim_invocation(payload, "router"))
        self.assertTrue(claim.exists())
        os.utime(marker, (due, due))
        self.assertTrue(hook_runtime.claim_invocation(self.payload("later-call"), "router"))
        self.assertFalse(claim.exists())

    def test_concurrent_duplicate_claims_have_exactly_one_winner(self):
        payload = self.payload("concurrent-call")
        with ThreadPoolExecutor(max_workers=16) as executor:
            results = list(
                executor.map(
                    lambda _: hook_runtime.claim_invocation(payload, "router"), range(64)
                )
            )

        self.assertEqual(1, results.count(True))
        self.assertEqual(63, results.count(False))



if __name__ == "__main__":
    unittest.main()
