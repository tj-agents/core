import json
import os
from pathlib import Path
import re
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
    goal_path = Path(json.loads((root / ".agents/continuation/owner.json").read_text())["goal"])
    goal_body = goal_path.read_text(encoding="utf-8")
    completion = re.search(r"```completion\s*\n(.*?)\n```", goal_body, re.DOTALL)
    if completion:
        document = json.loads(completion.group(1))
        for delivery in document.get("deliveries", []):
            if delivery.get("repository") == binding["repo"] and delivery.get("pr") == binding["pr"]:
                delivery["head"] = binding["head"]
        goal_path.write_text(
            goal_body[:completion.start(1)] + json.dumps(document) + goal_body[completion.end(1):],
            encoding="utf-8",
        )
    receipt["rebind"] = {"old": old, "new": {key: binding[key] for key in old}}
    observation = json.loads((root / "observation.json").read_text())
    observation["headRefOid"] = binding["head"]
    observation["statusCheckRollup"] = [{"name": "CI", "status": "IN_PROGRESS"}]
    (root / "observation.json").write_text(json.dumps(observation))
if scenario.get("release_binding"):
    binding_path = root / ".agents/persistent-workflow-binding.json"
    receipt["released_binding"] = json.loads(binding_path.read_text())
    if scenario.get("retain_stale_binding"):
        binding = dict(receipt["released_binding"], head=receipt["rebind"]["old"]["head"])
        binding_path.write_text(json.dumps(binding))
    else:
        binding_path.unlink()
    receipt["state"] = scenario["release_state"]
receipt.update(scenario.get("receipt", {}))
Path(os.environ["CONTINUATION_RESULT_PATH"]).write_text(json.dumps(receipt))
time.sleep(scenario.get("after_receipt_sleep", 0))
