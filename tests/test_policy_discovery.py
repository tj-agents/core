import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agents" / "hooks"))
import installed_skills


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_disabled_policy_is_available_only_to_explicit_bounded_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host: str
) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    installed = tmp_path / "plugins/cache/tj-agents/personal/local"
    entry = {
        "enabled": False,
        "name": "personal",
        "marketplaceName": "tj-agents",
        "version": "local",
        "installPath": str(installed),
    }
    inventory = {"installed": [entry]} if host == "codex" else [entry]
    installed_skills._native_install_roots.cache_clear()
    try:
        with (
            patch("installed_skills.shutil.which", return_value=host),
            patch(
                "installed_skills.plugin_inventory_command", return_value=([host], {})
            ),
            patch(
                "installed_skills.process.run",
                return_value=subprocess.CompletedProcess(
                    [], 0, json.dumps(inventory), ""
                ),
            ),
        ):
            assert installed_skills.native_install_roots(host) == ()
            assert installed_skills.native_install_roots(host, True) == (installed,)
    finally:
        installed_skills._native_install_roots.cache_clear()
