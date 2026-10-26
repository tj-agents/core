import importlib
import sys
from pathlib import Path
from unittest.mock import patch


def main(installed: Path) -> int:
    sys.path.insert(0, str(installed))
    hook_trust = importlib.import_module("codex.hook_trust")
    websocket = importlib.import_module("codex.websocket")
    if not Path(websocket.__file__).is_relative_to(installed):
        print(f"codex.websocket loaded from {websocket.__file__}", file=sys.stderr)
        return 1
    loaded = RuntimeError("transport-loaded")
    with patch.object(hook_trust.subprocess, "Popen", side_effect=loaded):
        try:
            hook_trust.AppServer("unused", installed, existing=True)
        except RuntimeError as error:
            if error is not loaded:
                raise
    print("transport-loaded")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
