import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from host_runtime import HostAdapterRegistry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--host", choices=("codex", "claude"), required=True)
    parser.add_argument("--codex-home", type=Path)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    profile_roots = {"codex": arguments.codex_home} if arguments.codex_home else None
    registry = HostAdapterRegistry(
        root / ".agents" / "workflows",
        root,
        profile_roots=profile_roots,
    )
    print(json.dumps(registry.probe(arguments.host), sort_keys=True))


if __name__ == "__main__":
    main()
