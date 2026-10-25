"""Close this verified CLI client while retaining its terminal and checkout (Python 3.9+)."""

import argparse
import os
import sys

import session_close


def close_host(entry, before_signal=lambda: None):
    session_close.stop_cli_client(entry, before_signal)


def close_session(entry):
    if not session_close.attached_to(os.getcwd(), entry):
        raise session_close.Refusal("current directory is not this session's registered attachment")
    activity = session_close.awaiting_input_activity(entry)
    close_host(entry, lambda: session_close.awaiting_input_activity(entry, activity))
    session_close._record_own_end(entry, "closed")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    entry = session_close.own_host_and_entry()
    try:
        return close_session(entry)
    except session_close.Refusal as error:
        session_close.record_close_refusal(entry, __file__, list(argv) if argv is not None else sys.argv[1:], error)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (session_close.Refusal, OSError) as error:
        print("close: " + str(error), file=sys.stderr)
        raise SystemExit(2)
