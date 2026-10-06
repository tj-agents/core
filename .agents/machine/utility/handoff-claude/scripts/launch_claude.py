#!/usr/bin/env python3
"""Hand prepared work to an independent Claude Code session in a new terminal tab.

Run as `python launch_claude.py ...` on Windows (where `python3` is often the Microsoft Store alias stub
rather than a real interpreter) and `python3 launch_claude.py ...` elsewhere; the shebang and exec bit are
not relied on.
"""

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

_EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')


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
    parser.add_argument('--effort', choices=_EFFORTS)
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
    """(model, effort, tier text for the success message) per this launcher's selection precedence.

    An explicit --model wins, a --lane resolves through the shipped lane table, and neither leaves
    claude on its own configured default, same as an interactively launched session. The lane is never
    guessed here: a transport that inferred one from the prompt would quietly decide the cost of every
    handoff. A lane's effort travels with its model, but only when the lane actually resolved the model:
    an explicit --model beating the lane means no lane effort applies either. An explicit --effort wins
    over a lane's effort either way, mirroring how launch-codex.ps1's -ReasoningEffort beats the lane.
    """
    model = args.model
    lane_effort = None
    tier = ''
    if args.frontier:
        model, lane_effort = agent_cli.resolve_lane_model('claude', frontier=True)
        tier = 'frontier -> '
    elif not model and args.lane:
        model, lane_effort = agent_cli.resolve_lane_model('claude', lane=args.lane)
        tier = f'lane {args.lane} -> '

    effort = args.effort if args.effort is not None else lane_effort
    return model, effort, tier


def build_arguments(args, model, effort, prompt_sentence):
    arguments = []
    if args.dangerously_skip_permissions:
        arguments.append('--dangerously-skip-permissions')
    if model:
        arguments += ['--model', model]
    if effort:
        arguments += ['--effort', effort]

    arguments.append(prompt_sentence)
    return arguments


def main(argv=None):
    agent_cli = _load_agent_cli()
    agent_cli.make_stdio_encoding_lossy()
    try:
        args = parse_args(argv, agent_cli)

        prompt_sentence = agent_cli.prompt_file_argument(args.prompt_path)
        prompt_path = Path(args.prompt_path).resolve()
        model, effort, tier = resolve_model(args, agent_cli)
        arguments = build_arguments(args, model, effort, prompt_sentence)

        working_directory = agent_cli.open_claude_tab(args.working_directory, args.title, arguments)

        selection = f'{tier}{model}' if model else 'the CLI default model'
        if effort:
            selection += f' at {effort}'
        print(f"Launched claude handoff tab '{args.title}' in {working_directory} on {selection} with prompt {prompt_path}")
        return 0
    except agent_cli.LaunchTimeout as exc:
        print(str(exc), file=sys.stderr)
        print('The tab may already have opened; check the terminal before launching another.', file=sys.stderr)
        return 3
    except agent_cli.LaunchError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
