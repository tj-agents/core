"""Exercise the shipped startup observer against an isolated native host."""

import argparse
import json
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.agents/machine/scripts'))
import startup_binding


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True, choices=('codex', 'claude'))
    parser.add_argument('--target', required=True)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    arguments = parser.parse_args()

    def report(state, **details):
        arguments.receipt.parent.mkdir(parents=True, exist_ok=True)
        arguments.receipt.write_text(json.dumps({'state': state, **details}), encoding='utf-8')

    def terminate(*_):
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, terminate)
    native_arguments = arguments.arguments[1:] if arguments.arguments[:1] == ['--'] else arguments.arguments
    try:
        return startup_binding.run_session(
            arguments.host, arguments.target, arguments.project, native_arguments, require_session_start=True,
            on_running=lambda pid: report('confirmed', child_pid=pid),
            on_unconfirmed=lambda pid: report('unconfirmed', child_pid=pid),
        )
    except startup_binding.StartupBindingError as error:
        report('failed', error=str(error))
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
