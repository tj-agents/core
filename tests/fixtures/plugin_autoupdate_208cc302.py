"""Frozen installed copier from Core208cc302dc3318a27908fc9ea23afc27ff8571af.

Only the exact RUNTIME assignment and self_update function are retained; package discovery is
replaced by the test's isolated package path. This models the code already installed before upgrade.
"""

import os
from pathlib import Path
import shutil

RUNTIME = ("plugin_autoupdate.py", "machine_events.py", "launch_check.py", "reload_plugins.py", "agent_cli.py",
           "codex_hook_trust.py", "required_plugins.py")


def packaged_copies(config):
    raise AssertionError("Test must supply isolated package discovery")


def self_update(current: Path, codex_config: dict) -> bool:
    candidates = [path for path in packaged_copies(codex_config) if path.resolve() != current.resolve()
                  and all(path.with_name(name).is_file() for name in RUNTIME)]
    if not candidates:
        return False
    newest = max(candidates, key=lambda path: path.stat().st_mtime)
    try:
        changed = False
        for name in RUNTIME:
            source, target = newest.with_name(name), current.with_name(name)
            if target.is_file() and source.read_bytes() == target.read_bytes():
                continue
            shutil.copyfile(source, target.with_name(target.name + ".next"))
            os.replace(target.with_name(target.name + ".next"), target)
            changed = True
    except OSError:
        return False
    return changed
