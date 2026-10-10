"""Configure Windows Terminal to close exited tabs; other terminals need no global mutation."""
import argparse
import os


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    if os.name != "nt":
        print("configure-terminal-tab-close: kitty/tmux/Konsole close exact native tabs directly; no Linux setting is changed.")
    else:
        print("configure-terminal-tab-close: set Windows Terminal profile defaults closeOnExit to always in Settings. The Python port does not edit user settings automatically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
