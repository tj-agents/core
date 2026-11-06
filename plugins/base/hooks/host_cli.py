import os
import sys
from pathlib import Path

HOST_CLI_VARIABLE = "TJ_AGENTS_HOST_CLI"


def plugin_inventory_command(binary):
    binary = str(Path(binary).resolve())
    if sys.platform != "win32" or Path(binary).suffix.casefold() not in {
        ".bat",
        ".cmd",
    }:
        return [binary, "plugin", "list", "--json"], None
    environment = dict(os.environ)
    environment[HOST_CLI_VARIABLE] = binary
    command = '"!' + HOST_CLI_VARIABLE + '!" plugin list --json'
    return (
        [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/v:on", "/s", "/c", command],
        environment,
    )
