#!/usr/bin/env python3
"""Hand prepared work to an independent Codex session in a new terminal tab.

Run as `python launch_codex.py ...` on Windows (where `python3` is often the Microsoft Store alias stub
rather than a real interpreter) and `python3 launch_codex.py ...` elsewhere; the shebang and exec bit are
not relied on.
"""

import argparse
import importlib.util
import sys
from pathlib import Path

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


def _load_codex_marketplace_sync(agent_cli):
    # Beside whichever agent_cli.py was actually found above, so both move together under every layout.
    path = Path(agent_cli.__file__).resolve().parent / 'codex_marketplace_sync.py'
    if not path.is_file():
        raise agent_cli.LaunchError(f'Codex sync script missing: {path}')
    spec = importlib.util.spec_from_file_location('codex_marketplace_sync', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args(argv, agent_cli):
    parser = argparse.ArgumentParser(description='Hand prepared work to an independent Codex session in a new terminal tab.')
    parser.add_argument('--working-directory', required=True)
    parser.add_argument('--prompt-path', required=True)
    parser.add_argument('--title', default='Codex handoff')
    parser.add_argument('--model')
    parser.add_argument('--reasoning-effort', choices=('low', 'medium', 'high', 'xhigh', 'max', 'ultra'))
    parser.add_argument('--lane', choices=('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7'))
    parser.add_argument('--frontier', action='store_true')
    parser.add_argument('--minimum-version', default='0.154.0')
    parser.add_argument('--bypass-hook-trust', action='store_true')
    args = parser.parse_args(argv)

    # --frontier is the tier no lane resolves to and tolerates no competing selection beside it, so
    # passing it alongside --lane or --model is a contradiction to reject rather than an ambiguity to
    # rank. --reasoning-effort is the one flag it still accepts, for a user who named the pace as well as
    # the tier.
    if args.frontier and (args.lane or args.model):
        raise agent_cli.LaunchError(
            '--frontier rejects --lane and --model beside it: the frontier tier is an explicit user '
            'request, not one selection among several.'
        )

    return args


def resolve_model(args, agent_cli):
    """(model, effort, tier text for the success message) per this launcher's selection precedence.

    An explicit --model or --reasoning-effort wins for whichever half it names outright. --lane fills
    whichever half the caller left out, from the same shipped lane table; the lane is never guessed from
    the prompt. --frontier resolves both halves as a pair from the tier above the ladder, and only an
    explicit --reasoning-effort still wins over its own effort, for a user who named the pace as well as
    the tier.
    """
    model = args.model
    effort = args.reasoning_effort
    tier = ''
    if args.frontier:
        tier = 'frontier -> '
        model, frontier_effort = agent_cli.resolve_lane_model('codex', frontier=True)
        if not effort:
            effort = frontier_effort
    elif args.lane and not (model and effort):
        lane_model, lane_effort = agent_cli.resolve_lane_model('codex', lane=args.lane)
        if not model:
            model = lane_model
            tier = f'lane {args.lane} -> '
        if not effort:
            effort = lane_effort

    return model, effort, tier


def build_arguments(working_directory, model, effort, bypass_hook_trust, prompt_sentence):
    arguments = ['--cd', str(working_directory)]
    if model:
        arguments += ['--model', model]
    if effort:
        arguments += ['--config', f'model_reasoning_effort={effort}']
    if bypass_hook_trust:
        arguments.append('--dangerously-bypass-hook-trust')

    arguments.append(prompt_sentence)
    return arguments


def main(argv=None):
    agent_cli = _load_agent_cli()
    agent_cli.make_stdio_encoding_lossy()
    try:
        args = parse_args(argv, agent_cli)

        # parse_args already rejected the one argparse-level contradiction (--frontier beside --lane or
        # --model). What happens here is the first filesystem or lane-table work, so the directory is
        # checked before any of it -- whichever of it is also wrong, the directory's error is never
        # shadowed by a later check that only looked irrelevant.
        working_directory = agent_cli.resolve_tab_directory(args.working_directory)
        prompt_sentence, prompt_path = agent_cli.prompt_file_argument(args.prompt_path)

        codex, version = agent_cli.resolve_codex_executable(minimum=args.minimum_version)
        model, effort, tier = resolve_model(args, agent_cli)
        arguments = build_arguments(working_directory, model, effort, args.bypass_hook_trust, prompt_sentence)

        sync = _load_codex_marketplace_sync(agent_cli)
        try:
            sync.sync_codex_standards(codex, working_directory)
        except sync.SyncError as exc:
            raise agent_cli.LaunchError(str(exc)) from None

        # TERM is CLEARED here, never forced -- the opposite of handoff-claude, and not an oversight.
        # Claude Code exports TERM=xterm-256color; Codex is a Rust/crossterm binary, and on native Windows
        # an unset TERM is what selects the console's truecolor path. Handing it a POSIX terminfo name
        # instead caps the palette at 256 colours and visibly wrecks the theme. Do not "align" this with
        # the Claude launcher. Nothing is forced on: every capability variable this launcher could set is
        # one Windows Terminal and the console already negotiate correctly for a native child, and the one
        # that was set -- TERM -- is what broke it. On POSIX this clearing has no effect either way:
        # launch_tab never forces or clears TERM there, because the terminal that actually starts the tab
        # sets TERM for that session itself.
        agent_cli.launch_tab(working_directory, codex, args.title, arguments=arguments, clear=('TERM',))

        selection = f'{tier}{model}' if model else 'the CLI default model'
        if effort:
            selection += f' at {effort}'
        print(f"Launched codex-cli {version['text']} from {codex} on {selection}")
        return 0
    except agent_cli.LaunchError as exc:
        return agent_cli.report_launch_failure(exc)


if __name__ == '__main__':
    sys.exit(main())
