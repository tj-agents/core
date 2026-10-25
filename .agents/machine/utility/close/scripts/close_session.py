"""Arm a detached watcher that closes this CLI once its final reply is delivered (Python 3.9+)."""

import argparse
import importlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time


def peer_scripts():
    candidate = Path(__file__).resolve().parents[2] / 'peer-cli/scripts'
    if (candidate / 'session_close.py').is_file():
        return candidate
    raise RuntimeError('machine:close cannot locate its shipped peer-cli runtime')


def runtime():
    path = str(peer_scripts())
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module('session_close')


def verified_entry(shared, session_id=None):
    return cli_runtime().verified_entry(shared, session_id)


def cli_runtime():
    here = Path(__file__).resolve()
    anchor = here.parents[4] if here.parents[4].name == '.agents' else here.parents[3] / '.agents'
    script = anchor / 'cli/utility/close/scripts/close_session.py'
    if not script.is_file():
        raise RuntimeError('machine:close cannot locate its shipped CLI close runtime')
    spec = importlib.util.spec_from_file_location('machine_cli_close_runtime', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def primary_checkout(shared):
    code, common, _error = shared.git(Path.cwd(), 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if code:
        return None
    common = Path(common)
    return common.parent if common.name == '.git' else None


def sweep_script(shared):
    here = Path(__file__).resolve()
    if here.parents[2].name in {'skills', 'codex-skills'}:
        candidates = [here.parents[3] / 'resources/machine/scripts/plugin_autoupdate.py']
    else:
        candidates = [
            here.parents[4] / 'machine/scripts/plugin_autoupdate.py',
            here.parents[5] / 'resources/machine/scripts/plugin_autoupdate.py',
        ]
    script = next((candidate for candidate in candidates if candidate.is_file()), None)
    if script is None:
        return None
    try:
        spec = importlib.util.spec_from_file_location('close_plugin_autoupdate', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.sweep_script(module.load_codex_config())
    except Exception:
        return None


def own_session(shared, session_id=None):
    return cli_runtime().own_session(shared, session_id)


def start_watcher(shared, entry, armed_at):
    primary, sweep = primary_checkout(shared), sweep_script(shared)
    cleanup = (primary, sweep) if primary and sweep else None
    return cli_runtime().start_watcher(shared, entry, armed_at, cleanup)


def arm():
    shared = runtime()
    entry, activity = own_session(shared)
    if activity.get('turn_state') != 'working':
        raise shared.Refusal('this session has no active turn to close after')
    return start_watcher(shared, entry, time.time())


def arm_after_stop(landed_at, session_id=None):
    """Arm from a Stop hook that runs after the session store recorded this turn's stop."""
    shared = runtime()
    entry, activity = own_session(shared, session_id)
    stopped = activity.get('last_activity_at')
    if activity.get('turn_state') != 'awaiting_input' or not shared.finite_positive(stopped):
        raise shared.Refusal('this session has no recorded stop to close after')
    started = activity.get('started_at')
    if not shared.finite_positive(started) or started >= landed_at:
        raise shared.Refusal('the delivery landed before this session started')
    return start_watcher(shared, entry, math.nextafter(stopped, 0.0))


def main(argv=None):
    if sys.version_info < (3, 9):
        print('machine:close requires Python 3.9 or newer', file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('arm')
    parser.parse_args(argv)
    print(json.dumps(arm()))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print('machine:close: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
