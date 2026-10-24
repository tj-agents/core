"""Arm a detached watcher that closes this CLI once its final reply is delivered (Python 3.9+)."""

import argparse
import importlib
import importlib.util
import json
import math
import os
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


def verified_entry(shared):
    entry = shared.own_host_and_entry()
    for _path, other in shared.entries():
        if (isinstance(other, dict) and other.get('pid') == entry['pid']
                and other.get('pid_started_at') == entry['pid_started_at']
                and other.get('session_id') != entry['session_id']):
            raise shared.Refusal('registered host is shared by multiple session identities; do not close it')
    return entry


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


def claude_transcript(session_id):
    home = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude')
    matches = list((home / 'projects').glob('*/' + session_id + '.jsonl'))
    return matches[0] if len(matches) == 1 else None


def own_session(shared):
    entry = verified_entry(shared)
    store = shared.register_session._load_session_store()
    if store is None:
        raise shared.Refusal('session turn store is unavailable')
    connection = store.connect()
    try:
        activity = store.get_session(connection, store.session_handle(entry['host'], entry['session_id']))
    finally:
        connection.close()
    if not isinstance(activity, dict) or activity.get('ended_at') is not None:
        raise shared.Refusal('this session has no active turn to close after')
    return entry, activity


def armed_path(shared, session_id):
    return shared.state_directory() / 'session-close' / (session_id + '.armed.json')


def start_watcher(shared, entry, armed_at):
    arguments = ['--host', entry['host'], '--session-id', entry['session_id'], '--pid', str(entry['pid']),
                 '--pid-started-at', repr(entry['pid_started_at']), '--armed-at', repr(armed_at),
                 '--state-directory', str(shared.state_directory()),
                 '--host-names', os.environ.get('AGENT_CLI_HOST_NAMES', '')]
    transcript = claude_transcript(entry['session_id']) if entry['host'] == 'claude' else None
    if transcript:
        arguments += ['--transcript', str(transcript), '--transcript-offset', str(transcript.stat().st_size)]
    primary, sweep = primary_checkout(shared), sweep_script(shared)
    if primary and sweep:
        arguments += ['--repo', str(primary), '--sweep', str(sweep)]
    shared.write_json(armed_path(shared, entry['session_id']), {'armed_at': armed_at})
    here = Path(__file__).resolve()
    scripts = peer_scripts()
    shared.start_detached(here.with_name('close_watcher.py'), arguments,
                          [scripts / 'close.py', scripts / 'close_tab.py', scripts / 'windows_terminal_uia.ps1'])
    return {'operation': 'session-close', 'status': 'armed', 'session_id': entry['session_id'],
            'transcript_checked': transcript is not None}


def arm():
    shared = runtime()
    entry, activity = own_session(shared)
    if activity.get('turn_state') != 'working':
        raise shared.Refusal('this session has no active turn to close after')
    return start_watcher(shared, entry, time.time())


def arm_after_stop(landed_at):
    """Arm from a Stop hook that runs after the session store recorded this turn's stop."""
    shared = runtime()
    entry, activity = own_session(shared)
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
