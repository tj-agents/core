"""Read selected local Codex or Claude history; never writes or uploads transcripts."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys


def records(path):
    with path.open(encoding='utf-8') as stream:
        for number, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue  # A running session can have an incomplete trailing record.
            if isinstance(value, dict):
                yield number, value


def text_content(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ' '.join(v.get('text', '') for v in value if isinstance(v, dict)
                        and v.get('type') in ('text', 'input_text', 'output_text'))
    return ''


def session(path, host):
    result = dict(session=None, cwd=None, branch=None, messages=[], host=host)
    for number, event in records(path):
        kind = event.get('type')
        if host == 'codex':
            payload = event.get('payload', {})
            if not isinstance(payload, dict):
                continue
            if kind == 'session_meta':
                if isinstance(payload.get('source'), dict) and 'subagent' in payload['source']:
                    return None
                result.update(session=payload.get('id'), cwd=payload.get('cwd'))
                result['branch'] = (payload.get('git') or {}).get('branch')
            elif kind == 'response_item' and payload.get('type') == 'message':
                role = payload.get('role')
                if role in ('user', 'assistant'):
                    text = text_content(payload.get('content'))
                    if text:
                        result['messages'].append((number, role, text))
        else:
            if event.get('isSidechain'):
                continue
            if kind in ('user', 'assistant'):
                result['session'] = event.get('sessionId') or result['session'] or path.stem
                result['cwd'] = event.get('cwd') or result['cwd']
                result['branch'] = event.get('gitBranch') or result['branch']
                message = event.get('message', {})
                text = text_content(message.get('content')) if isinstance(message, dict) else ''
                if text:
                    result['messages'].append((number, kind, text))
    if not result['session'] or not result['messages']:
        return None
    # Native IDs are opaque identifiers, never shell fragments.
    if not re.fullmatch(r'[A-Za-z0-9_-]+', result['session']):
        return None
    result['modified'] = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    result['resume'] = (f'codex resume {result["session"]}' if host == 'codex'
                        else f'claude --resume {result["session"]}')
    return result


def history_root(host):
    if host == 'codex':
        return Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'sessions'
    return Path(os.environ.get('CLAUDE_CONFIG_DIR', str(Path.home() / '.claude'))) / 'projects'


def query(root, host, *, cwd=None, project=None, count=5, pattern=None, regex=False, show_lines=False):
    if not root.is_dir():
        raise ValueError(f'No {host} history directory at {root}; select the correct profile or --history-root.')
    if count < 1:
        raise ValueError('--count must be positive')
    expression = re.compile(pattern if regex else re.escape(pattern), re.I) if pattern is not None else None
    files = root.rglob('*.jsonl') if host == 'codex' else root.glob('*/*.jsonl')
    results = []
    for path in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True):
        item = session(path, host)
        if not item:
            continue
        if cwd and (not item['cwd'] or Path(item['cwd']).resolve() != Path(cwd).resolve()):
            continue
        if project and project.casefold() not in (item['cwd'] or path.parent.name).casefold():
            continue
        messages = item.pop('messages')
        if expression:
            hits = [(line, text) for line, _, text in messages if expression.search(text)]
            if not hits:
                continue
            item['hits'] = len(hits)
            if show_lines:
                item['matches'] = [dict(line=line, text=text) for line, text in hits]
        item['message_count'] = len(messages)
        item['preview'] = next((re.sub(r'\s+', ' ', text)[:160] for _, role, text in messages
                                if role == 'user' and not text.lstrip().startswith('<')), '(no user preview)')
        results.append(item)
        if len(results) >= count:
            break
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('recent', 'search'))
    parser.add_argument('--host', choices=('codex', 'claude'), required=True)
    parser.add_argument('--history-root', type=Path, help='Override the transcript data directory, not a helper path')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--cwd', type=Path)
    selection.add_argument('--project')
    selection.add_argument('--all-projects', action='store_true')
    parser.add_argument('--count', type=int, default=5)
    parser.add_argument('--pattern')
    parser.add_argument('--regex', action='store_true')
    parser.add_argument('--show-lines', action='store_true')
    args = parser.parse_args()
    if args.operation == 'search' and args.pattern is None:
        parser.error('search requires --pattern')
    cwd = args.cwd
    if args.operation == 'recent' and not (cwd or args.project or args.all_projects):
        cwd = Path.cwd()
    try:
        result = query(args.history_root or history_root(args.host), args.host, cwd=cwd,
                       project=args.project, count=args.count, pattern=args.pattern,
                       regex=args.regex, show_lines=args.show_lines)
    except (OSError, ValueError, re.error) as error:
        print(f'History query failed: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
