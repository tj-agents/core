import json
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / ".agents/workflows"))

import completion
def forge_state(delivery, root):
    scenario = json.loads((Path(root) / "scenario.json").read_text(encoding="utf-8"))
    value = scenario.get("completion_forge", {}).get(str(delivery["pr"]))
    if value is None:
        return {"number": delivery["pr"], "headRefOid": delivery["head"], "state": "MERGED", "body": ""}
    return value


completion.forge_state = forge_state
sys.argv = [str(ROOT / ".agents/workflows/continuation_runtime.py"), *sys.argv[1:]]
runpy.run_path(sys.argv[0], run_name="__main__")
