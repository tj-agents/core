"""Stop hook: close a session once the pull request it worked on merged at its worktree's head (Python 3.9+).

Runs after the session store records the stop. It arms only for a clean linked worktree whose branch has a
pull request merged at exactly its HEAD after this session started; the watcher then closes the tab and the
worktree sweep removes the checkout only with its own proof.
"""

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

import closeout

GH_TIMEOUT_SECONDS = 20


def merged_pulls(cwd, branch):
    try:
        result = subprocess.run(['gh', 'pr', 'list', '--head', branch, '--state', 'merged',
                                 '--json', 'headRefOid,mergedAt', '--limit', '20'],
                                cwd=str(cwd), stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=GH_TIMEOUT_SECONDS, check=False)
        pulls = json.loads(result.stdout or '[]') if result.returncode == 0 else []
    except (OSError, subprocess.SubprocessError, ValueError):
        return []
    return pulls if isinstance(pulls, list) else []


def merged_at(cwd, git):
    code, output, _error = git(cwd, 'rev-parse', '--path-format=absolute', '--git-dir', '--git-common-dir', 'HEAD')
    lines = output.splitlines()
    if code or len(lines) != 3 or lines[0] == lines[1]:
        return None
    code, branch, _error = git(cwd, 'symbolic-ref', '--short', '-q', 'HEAD')
    if code or not branch:
        return None
    code, changes, _error = git(cwd, 'status', '--porcelain')
    if code or changes:
        return None
    pulls = merged_pulls(cwd, branch)
    times = [datetime.fromisoformat(pull['mergedAt'].replace('Z', '+00:00')).timestamp()
             for pull in pulls if isinstance(pull, dict) and pull.get('headRefOid') == lines[2]
             and isinstance(pull.get('mergedAt'), str)]
    return max(times) if times else None


def main():
    try:
        data = json.load(sys.stdin)
    except (OSError, UnicodeError, ValueError):
        return 0
    cwd = data.get('cwd') if isinstance(data, dict) else None
    if not isinstance(cwd, str) or not cwd:
        return 0
    try:
        shared = closeout.close_session.runtime()
        session_id = data.get('session_id') or data.get('sessionId')
        if not isinstance(session_id, str) or not session_id:
            return 0
        armed = shared.read_json(closeout.close_session.armed_path(shared, session_id))
        outcome = shared.read_json(shared.state_directory() / 'session-close' / (session_id + '.json')) or {}
        if (isinstance(armed, dict) and shared.finite_positive(armed.get('armed_at'))
                and 0 <= time.time() - armed['armed_at'] < 900
                and not outcome.get('at', 0) >= armed['armed_at']):
            return 0
        landed = merged_at(Path(cwd), shared.git)
        if landed is not None:
            closeout.arm_after_stop(landed, session_id)
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
