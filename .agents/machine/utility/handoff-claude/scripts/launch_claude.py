#!/usr/bin/env python3
"""Hand prepared work to an independent Claude Code session in a new terminal tab.

Run as `python3 launch_claude.py ...` (or `python` on Windows); the shebang and exec bit are not relied on.
"""

import argparse
import importlib.util
import os
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
    parser = argparse.ArgumentParser(description='Hand prepared work to an independent Claude Code session in a new terminal tab.')
    parser.add_argument('--working-directory', required=True)
    parser.add_argument('--prompt-path', required=True)
    parser.add_argument('--title', default='Claude handoff')
    parser.add_argument('--model')
    parser.add_argument('--lane', choices=('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7'))
    parser.add_argument('--frontier', action='store_true')
    parser.add_argument('--dangerously-skip-permissions', action='store_true')
    args = parser.parse_args(argv)

    # --frontier is the tier no lane resolves to and tolerates no competing selection beside it, so
    # passing it alongside --lane or --model is a contradiction to reject rather than an ambiguity to
    # rank.
    if args.frontier and (args.lane or args.model):
        raise agent_cli.LaunchError(
            '--frontier rejects --lane and --model beside it: the frontier tier is an explicit user '
            'request, not one selection among several.'
        )

    return args


def resolve_model(args, agent_cli):
    """(model, tier text for the success message) per this launcher's selection precedence.

    An explicit --model wins, a --lane resolves through the shipped lane table, and neither leaves
    claude on its own configured default, same as an interactively launched session. The lane is never
    guessed here: a transport that inferred one from the prompt would quietly decide the cost of every
    handoff.
    """
    model = args.model
    tier = ''
    if args.frontier:
        model, _ = agent_cli.resolve_lane_model('claude', frontier=True)
        tier = 'frontier -> '
    elif not model and args.lane:
        model, _ = agent_cli.resolve_lane_model('claude', lane=args.lane)
        tier = f'lane {args.lane} -> '

    return model, tier


def build_arguments(args, model, prompt_path):
    arguments = []
    if args.dangerously_skip_permissions:
        arguments.append('--dangerously-skip-permissions')
    if model:
        arguments += ['--model', model]

    arguments.append(f'Read the file at {prompt_path} and follow its instructions, working from the current directory.')
    return arguments


def main(argv=None):
    agent_cli = _load_agent_cli()
    try:
        args = parse_args(argv, agent_cli)

        # Absolute but not resolved: Claude Code keys a session's history by the directory string it
        # started in, so a symlinked checkout or a Windows mapped or subst drive must reach the tab as
        # given.
        working_directory = Path(os.path.abspath(args.working_directory))
        if not working_directory.is_dir():
            raise agent_cli.LaunchError(f'Working directory is not a directory: {working_directory}')

        prompt_path = Path(args.prompt_path).resolve()
        if not prompt_path.is_file():
            raise agent_cli.LaunchError(f'Prompt path is not a file: {prompt_path}')

        claude = agent_cli.resolve_claude_executable()

        model, tier = resolve_model(args, agent_cli)
        arguments = build_arguments(args, model, prompt_path)

        agent_cli.sync_claude_standards(working_directory, claude=claude)

        # Forced, not merely un-cleared: an automation-spawned terminal tab is not the interactive shell
        # a human would have launched it from, so colour/terminal-capability auto-detection cannot be
        # trusted to land on a good value on its own. FORCE_COLOR is the de-facto Node CLI convention
        # (chalk/supports-color) to force colour on outright; TERM=xterm-256color is a known-good profile
        # every supported terminal fully supports, set explicitly rather than left blank so nothing falls
        # back to a conservative dumb-terminal default.
        agent_cli.launch_tab(
            working_directory,
            claude,
            args.title,
            arguments=arguments,
            force={'FORCE_COLOR': '1', 'TERM': 'xterm-256color'},
        )

        selection = f'{tier}{model}' if model else 'the CLI default model'
        print(f"Launched claude handoff tab '{args.title}' in {working_directory} on {selection} with prompt {prompt_path}")
        return 0
    except agent_cli.LaunchError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
