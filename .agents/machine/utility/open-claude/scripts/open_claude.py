#!/usr/bin/env python3
"""Open an interactive Claude Code CLI in a new terminal tab on an exact directory.

Run as `python3 open_claude.py ...` (or `python` on Windows); the shebang and exec bit are not relied on.
"""

import argparse
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _load_agent_cli():
    # The shared launch primitives, from the authored source layout or either installed package layout.
    candidates = (
        HERE / '../../../scripts/agent_cli.py',
        HERE / '../../../resources/machine/scripts/agent_cli.py',
        HERE / '../../../../../resources/machine/scripts/agent_cli.py',
    )
    for candidate in candidates:
        path = candidate.resolve()
        if path.is_file():
            spec = importlib.util.spec_from_file_location('agent_cli', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise SystemExit(f'The shared agent_cli.py library was not found relative to {HERE}.')


def parse_args(argv, agent_cli):
    parser = argparse.ArgumentParser(description='Open a Claude Code CLI in a new terminal tab.')
    parser.add_argument('--working-directory', default='.')
    parser.add_argument('--resume')
    parser.add_argument('--continue', dest='continue_', action='store_true')
    parser.add_argument('--prompt')
    parser.add_argument('--prompt-path')
    parser.add_argument('--title', default='Claude')
    parser.add_argument('--model')
    parser.add_argument('--dangerously-skip-permissions', action='store_true')
    args = parser.parse_args(argv)

    if args.resume and args.continue_:
        raise agent_cli.LaunchError('Pass --resume for a specific session or --continue for the most recent one, not both.')

    if args.prompt and args.prompt_path:
        raise agent_cli.LaunchError('Pass --prompt for a short instruction or --prompt-path for a prepared file, not both.')

    # A prompt this long is no longer the short instruction --prompt exists for, and a command line is
    # the worst place to keep one: nothing on the receiving end can report a prompt that arrived damaged,
    # and once the tab is gone the text is gone with it. handoff-claude takes only --prompt-path for this
    # reason.
    if args.prompt and len(args.prompt) > 500:
        raise agent_cli.LaunchError(
            f'The inline --prompt is {len(args.prompt)} characters. Write it to a file and pass --prompt-path '
            'instead; --prompt is for a short instruction.'
        )

    return args


def build_arguments(args, agent_cli):
    arguments = []
    if args.resume:
        arguments += ['--resume', args.resume]
    if args.continue_:
        arguments.append('--continue')
    if args.dangerously_skip_permissions:
        arguments.append('--dangerously-skip-permissions')
    if args.model:
        arguments += ['--model', args.model]

    if args.prompt_path:
        resolved_prompt_path = Path(args.prompt_path).resolve()
        if not resolved_prompt_path.is_file():
            raise agent_cli.LaunchError(f'Prompt path is not a file: {resolved_prompt_path}')
        arguments.append(f'Read the file at {resolved_prompt_path} and follow its instructions, working from the current directory.')
    elif args.prompt:
        arguments.append(args.prompt)

    return arguments


def main(argv=None):
    agent_cli = _load_agent_cli()
    try:
        args = parse_args(argv, agent_cli)

        working_directory = Path(args.working_directory).resolve()
        if not working_directory.is_dir():
            raise agent_cli.LaunchError(f'Working directory is not a directory: {working_directory}')

        claude = agent_cli.resolve_claude_executable()
        arguments = build_arguments(args, agent_cli)

        agent_cli.sync_claude_standards(working_directory, claude=claude)

        agent_cli.launch_tab(
            working_directory,
            claude,
            args.title,
            arguments=arguments,
            force={'FORCE_COLOR': '1', 'TERM': 'xterm-256color'},
        )

        print(f"Launched claude tab '{args.title}' in {working_directory}")
        return 0
    except agent_cli.LaunchError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
