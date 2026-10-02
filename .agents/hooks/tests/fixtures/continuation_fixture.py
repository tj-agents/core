import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path.cwd()
scenario = json.loads((root / "scenario.json").read_text())
if sys.argv[1] == "observer":
    print(json.dumps(json.loads((root / "observation.json").read_text())))
    sys.exit(0)
(root / "host-started").write_text(str(os.getpid()))
time.sleep(scenario.get("sleep", 0))
mode = scenario["mode"]
if mode == "missing":
    sys.exit(0)
if mode == "unsupported":
    print("model is not supported when using this account", flush=True)
    sys.exit(1)
if mode == "transport":
    sys.exit(7)
receipt = {"owner_id": os.environ["CONTINUATION_OWNER_ID"],
           "nonce": os.environ["CONTINUATION_NONCE"],
           "state": "blocked" if mode == "gate" else "waiting" if mode == "repair" else "complete",
           "reason": "human approval required" if mode == "gate" else "fixture verified boundary",
           "next_action": "Ask for product approval" if mode == "gate" else "Wait for repaired checks"}
if mode == "badnonce":
    receipt["nonce"] = "wrong"
if mode == "repair":
    binding_path = root / ".agents/persistent-workflow-binding.json"
    binding = json.loads(binding_path.read_text())
    old = {key: binding[key] for key in ("repo", "worktree", "branch", "head")}
    (root / "repair.txt").write_text("fixed")
    subprocess.run(["git", "add", "repair.txt"], check=True)
    subprocess.run(["git", "commit", "-m", "Fixture repair"], check=True, capture_output=True)
    binding["head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    binding_path.write_text(json.dumps(binding))
    receipt["rebind"] = {"old": old, "new": {key: binding[key] for key in old}}
    observation = json.loads((root / "observation.json").read_text())
    observation["headRefOid"] = binding["head"]
    observation["statusCheckRollup"] = [{"name": "CI", "status": "IN_PROGRESS"}]
    (root / "observation.json").write_text(json.dumps(observation))
Path(os.environ["CONTINUATION_RESULT_PATH"]).write_text(json.dumps(receipt))
