"""Prepare and execute verified post-report closure of this completed CLI."""

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import uuid


MAX_TAIL = 1 << 20
MAX_AGE = 3600
DONE = re.compile(r"^\s*(?:\*\*)?(?:done|all done|all complete|work complete|completed)(?:\*\*)?[.!:]?(?:\s|$)", re.I)
KEEP_OPEN = re.compile(r"\b(?:keep|leave)\b[^.!?\n]{0,50}\bopen\b|\b(?:do not|don't|never)\s+close\b", re.I)


def peer_scripts():
    for root in Path(__file__).resolve().parents:
        candidate = root / '.agents/machine/utility/peer-cli/scripts'
        if (candidate / 'session_close.py').is_file():
            return candidate
    raise RuntimeError('machine:close cannot locate its shipped peer-cli runtime')


def runtime():
    path = str(peer_scripts())
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module('session_close')


def ticket_path(session):
    root = Path(os.environ.get('AGENT_STATE_DIRECTORY') or Path.home() / '.agents-state')
    digest = hashlib.sha256(session.encode('utf-8')).hexdigest()
    return root / 'session-close' / (digest + '.json')


def read_ticket(session):
    try:
        value = json.loads(ticket_path(session).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def save_ticket(session, value):
    path = ticket_path(session)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def arm(remove_worktree=False):
    shared = runtime()
    entry = shared.own_host_and_entry()
    store = shared.register_session._load_session_store()
    if store is None:
        raise shared.Refusal('session turn store is unavailable')
    connection = store.connect()
    try:
        activity = store.get_session(connection, store.session_handle(entry['host'], entry['session_id']))
    finally:
        connection.close()
    if (not isinstance(activity, dict) or activity.get('ended_at') is not None
            or activity.get('turn_state') not in ('working', 'awaiting_input')
            or not shared.finite_positive(activity.get('last_activity_at'))):
        raise shared.Refusal('this session has no active verified turn')
    if remove_worktree:
        shared.fresh_removable_receipt(shared.worktree_from_cwd())
    value = {'entry': entry, 'armed_at': time.time(), 'remove_worktree': remove_worktree,
             'status': 'armed', 'cwd': str(Path.cwd().resolve()), 'nonce': uuid.uuid4().hex,
             'activity': activity['last_activity_at'], 'turn_state': activity['turn_state']}
    save_ticket(entry['session_id'], value)
    return {'operation': 'session-close', 'status': 'armed', 'session_id': entry['session_id'],
            'checkout': 'remove-after-verified-exit' if remove_worktree else 'retain'}


def turn_messages(data):
    """Read only the current turn's final answer, never quoted tool output or old turns."""
    path = data.get('transcript_path') or data.get('transcriptPath')
    if not isinstance(path, str):
        return '', ''
    try:
        with Path(path).open('rb') as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - MAX_TAIL))
            lines = stream.read().splitlines()
    except OSError:
        return '', ''
    prompt, answer = '', ''
    for line in lines:
        try:
            record = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if not isinstance(record, dict) or record.get('isSidechain') or record.get('isMeta'):
            continue
        value = record.get('payload') if record.get('type') == 'response_item' else record.get('message', record)
        if not isinstance(value, dict):
            continue
        role = value.get('role') or record.get('type')
        if role == 'user':
            content = value.get('content')
            if isinstance(content, str) or (isinstance(content, list) and any(
                    isinstance(item, dict) and item.get('type') in ('text', 'input_text') for item in content)):
                answer = ''
                prompt = content if isinstance(content, str) else '\n'.join(
                    item['text'] for item in content if isinstance(item, dict)
                    and item.get('type') in ('text', 'input_text') and isinstance(item.get('text'), str))
        if role != 'assistant' or value.get('channel') in ('analysis', 'commentary'):
            continue
        content = value.get('content')
        if isinstance(content, str):
            answer = content
        elif isinstance(content, list):
            text = '\n'.join(item['text'] for item in content if isinstance(item, dict)
                             and item.get('type') in ('text', 'output_text') and isinstance(item.get('text'), str))
            if text:
                answer = text
    return prompt.strip(), answer.strip()


def blocked(reason):
    return {'decision': 'block', 'reason': 'SESSION CLOSE: ' + reason}


def complete():
    """Explicit foreground operation after the host returns every Stop-gate verdict."""
    shared = runtime()
    entry = shared.own_host_and_entry()
    session = entry['session_id']
    ticket = read_ticket(session)
    if not ticket or ticket.get('status') != 'reported':
        raise shared.Refusal('no prepared completion report has passed through Stop')
    armed = ticket.get('armed_at')
    if (not isinstance(armed, (int, float)) or isinstance(armed, bool)
            or not math.isfinite(armed) or not 0 <= time.time() - armed <= MAX_AGE
            or not isinstance(ticket.get('nonce'), str)
            or re.fullmatch('[0-9a-f]{32}', ticket['nonce']) is None):
        raise shared.Refusal('reported closure expired or has an invalid identity')
    if ticket.get('entry') != entry or shared.path_key(Path.cwd()) != shared.path_key(ticket['cwd']):
        raise shared.Refusal('reported host identity or attachment changed')
    shared.awaiting_input_activity(entry)
    claim = ticket_path(session).with_suffix('.' + ticket['nonce'] + '.close-claim')
    try:
        descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise shared.Refusal('this close attempt has already been claimed')
    os.close(descriptor)
    if read_ticket(session) != ticket:
        raise shared.Refusal('reported closure was cancelled or replaced')
    ticket['status'] = 'closing'
    save_ticket(session, ticket)
    try:
        module = importlib.import_module('finish' if ticket.get('remove_worktree') else 'close')
        result = module.main([])
        if result:
            raise shared.Refusal('verified close helper failed')
    except Exception as error:
        ticket.update(status='refused', error=str(error))
        save_ticket(session, ticket)
        raise
    return None


def stop(data, session):
    ticket = read_ticket(session)
    prompt, answer = turn_messages(data)
    retry = data.get('stop_hook_active') or data.get('stopHookActive')
    if KEEP_OPEN.search(prompt):
        ticket_path(session).unlink(missing_ok=True)
        return None
    if ticket is None:
        if DONE.match(answer) and not retry:
            return blocked('You reported completion without preparing session closure. Load machine:close, '
                           'verify all owned work is done, and arm its post-report close operation. '
                           'If work remains or the user requested keep-open, explain that actual state instead.')
        return None
    if ticket.get('status') != 'armed':
        if ticket.get('status') == 'reported':
            return {'systemMessage': 'SESSION CLOSE: the report is delivered. Resolve every other Stop-gate blocker, '
                    'then run machine:close complete --stop-gates-accepted. The Stop hook never terminates the host.'}
        if ticket.get('status') == 'closing':
            return {'systemMessage': 'SESSION CLOSE: the prepared attempt is in progress; do not start a second close or claim verified exit.'}
        return {'systemMessage': 'SESSION CLOSE: closure was not verified: ' + str(ticket.get('error', 'unknown refusal'))}
    if not answer:
        return None
    armed = ticket.get('armed_at')
    if (not isinstance(armed, (int, float)) or isinstance(armed, bool)
            or not math.isfinite(armed) or not 0 <= time.time() - armed <= MAX_AGE):
        ticket.update(status='refused', error='prepared closure expired')
        save_ticket(session, ticket)
        return blocked('Prepared closure expired. Reload machine:close; no host was closed.')
    shared = runtime()
    try:
        entry = shared.own_host_and_entry()
        expected = ticket.get('entry')
        if not isinstance(expected, dict) or any(entry.get(key) != expected.get(key)
                for key in ('host', 'session_id', 'pid', 'pid_started_at', 'cwd')) or entry['session_id'] != session:
            raise shared.Refusal('prepared host identity or attachment changed')
        if shared.path_key(Path.cwd()) != shared.path_key(ticket['cwd']):
            raise shared.Refusal('prepared working directory changed')
        if read_ticket(session) != ticket:
            raise shared.Refusal('prepared closure was cancelled or replaced')
        nonce = ticket.get('nonce')
        if not isinstance(nonce, str) or re.fullmatch('[0-9a-f]{32}', nonce) is None:
            raise shared.Refusal('prepared closure identity is invalid')
        claim = ticket_path(session).with_suffix('.' + nonce + '.claim')
        try:
            descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            return None
        os.close(descriptor)
        if read_ticket(session) != ticket:
            raise shared.Refusal('prepared closure was cancelled or replaced')
        store = shared.register_session._load_session_store()
        if store is None:
            raise shared.Refusal('session turn store is unavailable')
        connection = store.connect()
        try:
            handle = store.session_handle(entry['host'], entry['session_id'])
            unchanged = store.record_prepared_stop(connection, handle, ticket['activity'], ticket['turn_state'])
        finally:
            connection.close()
        if not unchanged:
            raise shared.Refusal('prepared turn activity changed; preserve the active dialogue')
        ticket['status'] = 'reported'
        save_ticket(session, ticket)
        # Do not signal a process inside a Stop hook: other plugins may still return block.
        return blocked('The completion report is delivered. Inspect every Stop-gate verdict and resolve '
                       'all other blockers before invoking machine:close with '
                       '`close_session.py complete --stop-gates-accepted`. '
                       'No host was closed by this hook. No new user answer is needed for this operation.')
    except Exception as error:
        ticket.update(status='refused', error=str(error))
        save_ticket(session, ticket)
        return blocked('Verified close refused: ' + str(error) + '. Preserve this session and report the limitation; '
                       'do not force-close or claim closure succeeded.')
    return None


def hook(data):
    session = data.get('session_id') or data.get('sessionId')
    if not isinstance(session, str) or not session:
        return None
    event = data.get('hook_event_name') or data.get('hookEventName')
    if event == 'UserPromptSubmit':
        ticket_path(session).unlink(missing_ok=True)
        return None
    if event == 'Stop':
        return stop(data, session)
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('arm')
    prepare.add_argument('--remove-worktree', action='store_true')
    finish = commands.add_parser('complete')
    finish.add_argument('--stop-gates-accepted', action='store_true', required=True,
                        help='confirm every other Stop gate accepted completion before closing')
    commands.add_parser('hook')
    arguments = parser.parse_args(argv)
    if arguments.command == 'arm':
        output = arm(arguments.remove_worktree)
    elif arguments.command == 'complete':
        output = complete()
    else:
        data = json.load(sys.stdin)
        output = hook(data) if isinstance(data, dict) else None
    if output:
        print(json.dumps(output))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print('machine:close: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
