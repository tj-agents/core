import json
import os
from pathlib import Path
import sys


def empty_native_inventory_environment(root, environment, hosts):
    binaries = Path(root) / "native inventory bin"
    binaries.mkdir()
    for host in hosts:
        inventory = {"installed": []} if host == "codex" else []
        script = binaries / f"{host}_inventory.py"
        script.write_text(f"print({json.dumps(inventory)!r})\n", encoding="utf-8")
        if os.name == "nt":
            launcher = binaries / f"{host}.cmd"
            launcher.write_text(
                f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8"
            )
        else:
            launcher = binaries / host
            launcher.write_text(
                f"#!{sys.executable}\nimport runpy\n"
                f"runpy.run_path({str(script)!r}, run_name='__main__')\n",
                encoding="utf-8",
            )
            launcher.chmod(0o755)
    return dict(environment, PATH=str(binaries) + os.pathsep + environment.get("PATH", ""))
