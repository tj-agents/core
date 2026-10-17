from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "machine" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / ".agents" / "hooks"))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ROLLING = load("runtime_binding_rolling", SCRIPTS / "rolling_plugins.py")
sys.modules["rolling_plugins"] = ROLLING
RUNTIME = load("runtime_binding", SCRIPTS / "codex_runtime_binding.py")
ROUTER = load("runtime_binding_router", ROOT / ".agents" / "hooks" / "skill_router.py")


class CodexRuntimeBindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="runtime binding ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "codex"
        self.package = self.root / "package"
        self.package.mkdir()
        self.verified = ROLLING.VerifiedRoot(
            "base@base-agents", self.package, "a" * 40, "https://github.com/tj-agents/core.git",
        )
        self.prepared = ROLLING.Prepared(
            "codex", (), (self.verified,), self.home / "plugins/cache/.tj-agents-rolling/codex/catalogs/codex/a",
            {}, (), (), self.home / "plugins", ROLLING.Deadline(), (),
        )

    def test_runtime_arguments_preserve_dotted_plugin_policy_and_third_party_configuration(self):
        dotted = ROLLING.VerifiedRoot(
            "base.alpha@base.agents", self.package, "a" * 40, "https://github.com/tj-agents/core.git",
        )
        prepared = ROLLING.Prepared(
            "codex", (), (dotted,), self.prepared.catalog_root, {}, (), (), self.prepared.plugins_root,
            self.prepared.deadline, (),
        )
        catalog = self.root / "catalog"
        arguments = RUNTIME._runtime_arguments(
            prepared,
            {
                "effective_plugin_configuration": {
                    "base.alpha@base.agents": {"enabled": True, "policy": {"mode": "strict", "levels": [1, 2]}},
                    "third.party@outside.market": {"enabled": False, "metadata": {"local": "keep"}},
                },
                "effective_marketplace_configuration": {
                    "base.agents": {"source_type": "git", "source": "https://github.com/tj-agents/core.git", "metadata": {"keep": True}},
                },
            },
            catalog,
            {"base.agents": "tj-run-aabbcc-base.agents"},
            ("-c", "features.hooks=true"),
        )
        values = arguments[1::2]
        self.assertFalse(any(value.startswith("plugins.base.alpha@base.agents.") for value in values))
        plugins = next(value for value in values if value.startswith("plugins="))
        self.assertIn('"base.alpha@base.agents" = { "enabled" = false', plugins)
        self.assertIn('"base.alpha@tj-run-aabbcc-base.agents" = { "enabled" = true', plugins)
        self.assertIn('"third.party@outside.market" = { "enabled" = false, "metadata" = { "local" = "keep" } }', plugins)
        alias = plugins
        self.assertIn('"policy" = { "levels" = [1, 2], "mode" = "strict" }', alias)
        marketplace = next(value for value in values if value.startswith("marketplaces="))
        self.assertIn('"metadata" = { "keep" = true }', marketplace)

    def test_disabled_logical_hook_state_is_mapped_to_its_runtime_alias(self):
        states = RUNTIME._disabled_hook_states(
            {
                "base@base-agents:hooks/codex.json:stop:0": {"enabled": False, "trusted_hash": "sha256:x"},
                "other@outside:hooks/codex.json": {"enabled": False},
            },
            {"base@base-agents": "base@tj-run-aabbcc-base-agents"},
        )
        self.assertEqual({
            "base@tj-run-aabbcc-base-agents:hooks/codex.json:stop:0": {"enabled": False, "trusted_hash": "sha256:x"},
        }, states)

    def test_trust_hash_does_not_reenable_a_disabled_hook(self):
        state = RUNTIME._runtime_hook_state(
            {"base@base-agents:hooks/codex.json:stop:0": {"enabled": False}},
            {"base@base-agents:hooks/codex.json:stop:0": {"trusted_hash": "sha256:x"}},
        )
        self.assertEqual({"enabled": False, "trusted_hash": "sha256:x"},
                         state["base@base-agents:hooks/codex.json:stop:0"])

    def test_runtime_receipt_rejects_tampering_and_validly_signed_path_escape(self):
        session = self.home / "plugins/cache/.tj-agents-rolling/codex/sessions/token"
        catalog = session / "catalog"
        runtime = self.home / "plugins/cache/tj-run-aabbcc-base-agents/base/local"
        catalog.mkdir(parents=True)
        runtime.mkdir(parents=True)
        receipt = session / "runtime-receipt.json"
        payload = {
            "schema_version": 1,
            "codex_home": str(self.home),
            "catalog": str(catalog),
            "roots": [str(runtime)],
        }
        data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        receipt.write_bytes(data)
        environment = {
            "CODEX_HOME": str(self.home),
            "TJ_AGENTS_CODEX_RUNTIME_RECEIPT": str(receipt),
            "TJ_AGENTS_CODEX_RUNTIME_RECEIPT_SHA256": __import__("hashlib").sha256(data).hexdigest(),
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            self.assertEqual((runtime.resolve(),), ROUTER._runtime_receipt_roots())
            receipt.write_bytes(data + b"x")
            with self.assertRaises(ROUTER.NativePluginDiscoveryError):
                ROUTER._runtime_receipt_roots()
            escaped = dict(payload, roots=[str(self.root / "outside")])
            (self.root / "outside").mkdir()
            escaped_data = (json.dumps(escaped, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            receipt.write_bytes(escaped_data)
            os.environ["TJ_AGENTS_CODEX_RUNTIME_RECEIPT_SHA256"] = __import__("hashlib").sha256(escaped_data).hexdigest()
            with self.assertRaises(ROUTER.NativePluginDiscoveryError):
                ROUTER._runtime_receipt_roots()

    def test_cleanup_removes_only_the_owned_alias_and_session_after_exit(self):
        cache = self.home / "plugins/cache"
        alias = cache / "tj-run-aabbcc-base-agents"
        alias.mkdir(parents=True)
        unrelated = cache / "base-agents"
        unrelated.mkdir()
        directory = cache / ".tj-agents-rolling/codex/sessions/token"
        directory.mkdir(parents=True)
        binding = RUNTIME.RuntimeBinding(self.prepared, directory, {"base-agents": alias.name},
                                         directory / "runtime-receipt.json", "digest", {})
        RUNTIME.cleanup_runtime(binding, self.home)
        self.assertFalse(alias.exists())
        self.assertFalse(directory.exists())
        self.assertTrue(unrelated.is_dir())

    def test_primary_preparation_error_survives_cleanup_failure(self):
        directory = self.home / "plugins/cache/.tj-agents-rolling/codex/sessions/token"
        directory.mkdir(parents=True)
        with mock.patch.object(RUNTIME, "_runtime_directory", return_value=directory), \
                mock.patch.object(RUNTIME, "_runtime_catalog", side_effect=RuntimeError("primary failure")), \
                mock.patch.object(RUNTIME, "cleanup_runtime", side_effect=RuntimeError("cleanup failure")):
            with self.assertRaisesRegex(RuntimeError, "primary failure"):
                RUNTIME.prepare_runtime("codex", self.root, self.home, self.prepared, {}, ())


if __name__ == "__main__":
    unittest.main()
