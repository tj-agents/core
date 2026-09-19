import json
import re
import subprocess
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Protocol


CONTRACT_VERSION = "v2"
RELEASES = ("A", "B", "C")
ENTRY_KINDS = ("compatibility-entry", "driver")
ENTRY_STATUSES = ("supported", "deprecated", "retained")
IDENTITY_FIELDS = ("contract_version", "workflow_id", "workflow_run_id", "stage_id", "dispatch_id")


class ContractViolation(ValueError):
    pass


class WorkflowStateProvider(Protocol):
    provider_id: str

    def probe(self):
        ...

    def resolve(self, *arguments, **keywords):
        ...


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pointer(document, reference):
    if not reference.startswith("#/"):
        raise ContractViolation(f"unsupported schema reference {reference!r}")
    value = document
    for raw in reference[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        value = value[key]
    return value


def _matches_type(value, expected):
    choices = expected if isinstance(expected, list) else [expected]
    for choice in choices:
        if choice == "null" and value is None:
            return True
        if choice == "object" and isinstance(value, dict):
            return True
        if choice == "array" and isinstance(value, list):
            return True
        if choice == "string" and isinstance(value, str):
            return True
        if choice == "boolean" and isinstance(value, bool):
            return True
        if choice == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if choice == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
    return False


def _is_valid(value, schema, root):
    try:
        _validate(value, schema, root, "$")
        return True
    except ContractViolation:
        return False


def _validate(value, schema, root, location):
    if "$ref" in schema:
        _validate(value, _pointer(root, schema["$ref"]), root, location)
    if "allOf" in schema:
        for item in schema["allOf"]:
            _validate(value, item, root, location)
    if "anyOf" in schema:
        if not any(_is_valid(value, item, root) for item in schema["anyOf"]):
            raise ContractViolation(f"{location} matches no anyOf branch")
    if "oneOf" in schema:
        matches = sum(_is_valid(value, item, root) for item in schema["oneOf"])
        if matches != 1:
            raise ContractViolation(f"{location} matches {matches} oneOf branches")
    if "not" in schema and _is_valid(value, schema["not"], root):
        raise ContractViolation(f"{location} matches a forbidden schema")
    if "if" in schema:
        selected = schema.get("then") if _is_valid(value, schema["if"], root) else schema.get("else")
        if selected is not None:
            _validate(value, selected, root, location)
    if "const" in schema and value != schema["const"]:
        raise ContractViolation(f"{location} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractViolation(f"{location} is not one of {schema['enum']!r}")
    if "type" in schema and not _matches_type(value, schema["type"]):
        raise ContractViolation(f"{location} has the wrong type")

    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [name for name in required if name not in value]
        if missing:
            raise ContractViolation(f"{location} is missing {missing!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            if extras:
                raise ContractViolation(f"{location} has unsupported fields {extras!r}")
        for name, child in properties.items():
            if name in value:
                _validate(value[name], child, root, f"{location}.{name}")
        if len(value) < schema.get("minProperties", 0):
            raise ContractViolation(f"{location} has too few properties")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ContractViolation(f"{location} has too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ContractViolation(f"{location} has too many items")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                raise ContractViolation(f"{location} contains duplicate items")
        if "items" in schema:
            for index, item in enumerate(value):
                _validate(item, schema["items"], root, f"{location}[{index}]")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ContractViolation(f"{location} is too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ContractViolation(f"{location} is too long")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise ContractViolation(f"{location} does not match {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ContractViolation(f"{location} is below its minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ContractViolation(f"{location} is above its maximum")


def _repository_path_key(value, repository_root=None):
    if not isinstance(value, str) or not value:
        return None
    for path in (PurePosixPath(value), PureWindowsPath(value)):
        if path.drive or path.root or path.anchor or ".." in path.parts:
            return None
    normalized = PurePosixPath(value.replace("\\", "/"))
    if not normalized.parts:
        return None
    if repository_root is not None:
        root = Path(repository_root).resolve()
        candidate = root.joinpath(*normalized.parts).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
    return normalized.as_posix()


def _relative_repository_path(value, repository_root=None):
    return _repository_path_key(value, repository_root) is not None


class WorkflowContract:
    def __init__(self, source_root=None, version=CONTRACT_VERSION, repository_root=None):
        workflow_root = Path(source_root) if source_root else Path(__file__).resolve().parent
        self.workflow_root = workflow_root.resolve()
        self.repository_root = Path(repository_root).resolve() if repository_root else None
        self.version = version
        self.contract_root = self.workflow_root / "contract" / version
        self.capabilities = _load_json(self.contract_root / "capabilities.json")
        self.compatibility = _load_json(self.contract_root / "compatibility.json")
        self.schemas = {
            name: _load_json(self.contract_root / filename)
            for name, filename in self.compatibility["schemas"].items()
        }

    def validate(self, record_type, record):
        schema = self.schemas[record_type]
        _validate(record, schema, schema, "$")
        return record

    def validate_fragment(self, definition, record):
        schema = self.schemas["state"]
        _validate(record, schema["$defs"][definition], schema, "$")
        return record

    def for_repository(self, repository_root):
        root = Path(repository_root).resolve()
        if self.repository_root is None:
            return WorkflowContract(self.workflow_root, self.version, root)
        if self.repository_root != root:
            raise ContractViolation("workflow contract is bound to a different repository")
        return self

    def select_semantic_stage(self, evidence):
        if not evidence:
            raise ContractViolation("semantic stage selection requires evidence")
        routing = self.capabilities["semantic_stage_routing"]
        stages = routing["stages"]
        known = {
            signal
            for definition in stages.values()
            for signal in definition["signals"]
        }
        unknown = set(evidence) - known
        if unknown:
            raise ContractViolation(f"unknown semantic stage evidence {sorted(unknown)!r}")
        selected = [
            stage
            for stage in routing["selection_priority"]
            if set(evidence) & set(stages[stage]["signals"])
        ]
        if not selected:
            raise ContractViolation("semantic stage evidence selects no stage")
        return selected[0]

    def validate_dispatch(self, dispatch):
        self.validate("dispatch", dispatch)
        permissions = dispatch["permissions"]
        paths = dispatch["context"]["repository_paths"] + permissions["files"]
        writer_lease = permissions.get("writer_lease")
        if writer_lease:
            paths += writer_lease["paths"]
        for path in paths:
            if not _relative_repository_path(path, self.repository_root):
                raise ContractViolation(f"dispatch path must be repository-relative: {path}")
        capability = self.capabilities["delegable_capabilities"][dispatch["capability"]]
        semantic_stage = dispatch.get("semantic_stage", capability["default_semantic_stage"])
        if semantic_stage not in capability["allowed_semantic_stages"]:
            raise ContractViolation(
                "dispatch semantic stage is incompatible with its capability"
            )
        if permissions["mode"] != capability["mode"]:
            raise ContractViolation("dispatch mode differs from the capability contract")
        if dispatch["capability"] == "review-lens":
            artifacts = dispatch["context"]["immutable_artifacts"]
            if not artifacts:
                raise ContractViolation("review-lens dispatch requires immutable artifacts")
            if len(artifacts) != len(set(artifacts)):
                raise ContractViolation("review-lens dispatch immutable artifacts must be unique")
        boundary = dispatch["decision_boundary"]
        for field in ("may_decide", "must_not_decide"):
            if set(boundary[field]) != set(capability[field]):
                raise ContractViolation(f"dispatch {field} differs from the capability contract")
        if writer_lease:
            permitted = {
                _repository_path_key(path, self.repository_root) for path in permissions["files"]
            }
            leased = {
                _repository_path_key(path, self.repository_root) for path in writer_lease["paths"]
            }
            if not leased.issubset(permitted):
                raise ContractViolation("writer lease paths exceed the permitted files")
        return dispatch

    def validate_result(self, result, dispatch=None):
        self.validate("result", result)
        evidence_ids = [item["evidence_id"] for item in result["evidence"]]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ContractViolation("result evidence identifiers must be unique")
        known = set(evidence_ids)
        for item in result["claims"] + result["acceptance_conditions"]:
            missing = set(item["evidence_ids"]) - known
            if missing:
                raise ContractViolation(f"result cites unknown evidence {sorted(missing)!r}")
        if result["status"] == "complete" and not all(
            item["passed"] for item in result["acceptance_conditions"]
        ):
            raise ContractViolation("a complete result cannot fail an acceptance condition")
        if dispatch is not None:
            self.validate_dispatch(dispatch)
            for field in IDENTITY_FIELDS:
                if result[field] != dispatch[field]:
                    raise ContractViolation(f"result {field} does not match its dispatch")
            expected = dispatch["acceptance_conditions"]
            actual = [item["condition"] for item in result["acceptance_conditions"]]
            if actual != expected:
                raise ContractViolation("result acceptance conditions do not match the dispatch")
            if dispatch["capability"] == "review-lens":
                expected_artifacts = set(dispatch["context"]["immutable_artifacts"])
                artifact_evidence = [
                    item
                    for item in result["evidence"]
                    if item["kind"] == "immutable-artifact"
                ]
                observed_artifacts = {item["locator"] for item in artifact_evidence}
                if (
                    len(artifact_evidence) != len(expected_artifacts)
                    or observed_artifacts != expected_artifacts
                ):
                    raise ContractViolation(
                        "review-lens result immutable artifacts differ from its dispatch"
                    )
                artifact_ids = {item["evidence_id"] for item in artifact_evidence}
                for item in result["claims"] + result["acceptance_conditions"]:
                    if not artifact_ids.issubset(item["evidence_ids"]):
                        raise ContractViolation(
                            "review-lens claims and acceptance conditions must cite immutable artifacts"
                        )
            is_writer = dispatch["capability"] == "mechanical-worker"
            if is_writer != ("writer" in result):
                raise ContractViolation("writer details must appear exactly for mechanical-worker results")
            if is_writer:
                lease = {
                    _repository_path_key(path, self.repository_root)
                    for path in dispatch["permissions"]["writer_lease"]["paths"]
                }
                reported = set()
                for path in result["writer"]["changed_paths"] + result["writer"]["partial_paths"]:
                    key = _repository_path_key(path, self.repository_root)
                    if key is None:
                        raise ContractViolation(f"writer result path must be repository-relative: {path}")
                    reported.add(key)
                if not reported.issubset(lease):
                    raise ContractViolation("writer result paths exceed the writer lease")
        return result

    def transition(self, kind, reason, target_stage_id=None, dispatch_id=None, resume_condition=None):
        record = {
            "contract_version": self.version,
            "transition": kind,
            "owner": "parent",
            "reason": reason,
        }
        optional = {
            "target_stage_id": target_stage_id,
            "dispatch_id": dispatch_id,
            "resume_condition": resume_condition,
        }
        record.update({key: value for key, value in optional.items() if value is not None})
        return self.validate_fragment("transition", record)

    def gate(self, kind, status, owner, action, resume_condition, evidence=None):
        record = {
            "contract_version": self.version,
            "gate_kind": kind,
            "status": status,
            "owner": owner,
            "action": action,
            "resume_condition": resume_condition,
            "evidence": evidence or [],
        }
        return self.validate_fragment("gate", record)

    def verify_bundle(self):
        if self.capabilities["contract_version"] != self.version:
            raise ContractViolation("capability contract version mismatch")
        if self.compatibility["contract_version"] != self.version or not self.compatibility["current"]:
            raise ContractViolation("compatibility contract is not current")
        dispatch_capabilities = set(self.schemas["dispatch"]["properties"]["capability"]["enum"])
        if dispatch_capabilities != set(self.capabilities["delegable_capabilities"]):
            raise ContractViolation("dispatch capabilities differ from capabilities.json")
        statuses = set(self.schemas["result"]["properties"]["status"]["enum"])
        if statuses != set(self.capabilities["result_statuses"]):
            raise ContractViolation("result statuses differ from capabilities.json")
        transitions = set(self.schemas["state"]["$defs"]["transition"]["properties"]["transition"]["enum"])
        if transitions != set(self.capabilities["transitions"]):
            raise ContractViolation("state transitions differ from capabilities.json")
        stage_routing = self.capabilities["semantic_stage_routing"]
        stages = set(stage_routing["stages"])
        schema_stages = set(
            self.schemas["dispatch"]["properties"]["semantic_stage"]["enum"]
        )
        if stages != schema_stages:
            raise ContractViolation("semantic stages differ from dispatch.schema.json")
        priority = stage_routing["selection_priority"]
        if len(priority) != len(stages) or set(priority) != stages:
            raise ContractViolation("semantic stage priority is incomplete")
        if not set(stage_routing["protected_stages"]).issubset(stages):
            raise ContractViolation("protected semantic stages are unknown")
        provider_ids = set(self.schemas["provider"]["properties"]["provider_id"]["enum"])
        if provider_ids != set(self.compatibility["providers"]):
            raise ContractViolation("provider identifiers differ from compatibility.json")
        provider_operations = {
            operation
            for provider in self.compatibility["providers"].values()
            for operation in provider["operations"]
        }
        schema_operations = set(
            self.schemas["provider"]["properties"]["capabilities"]["items"]["enum"]
        )
        if schema_operations != provider_operations:
            raise ContractViolation("provider capabilities differ from compatibility.json")
        host_ids = set(self.schemas["host"]["$defs"]["host"]["enum"])
        if host_ids != set(self.compatibility["host_adapters"]):
            raise ContractViolation("host identifiers differ from compatibility.json")
        decks = self.compatibility.get("execution_decks", {})
        for deck_id, deck in decks.items():
            if deck_id in provider_ids:
                raise ContractViolation(f"{deck_id} cannot be both a deck and a state provider")
            resource = (self.contract_root / deck["resource"]).resolve()
            if not resource.is_file():
                raise ContractViolation(f"missing {deck_id} deck resource")
            if deck.get("launch_mode") != "native-cli-passthrough":
                raise ContractViolation(f"{deck_id} deck launch mode is incompatible")
            if deck.get("workflow_state_api") is not False:
                raise ContractViolation(f"{deck_id} must not become a workflow-state API")
            if not deck.get("owns"):
                raise ContractViolation(f"{deck_id} deck ownership is empty")
        role_ids = set(self.capabilities["delegable_capabilities"])
        fallback_reasons = set(self.schemas["host"]["$defs"]["fallbackReason"]["enum"])
        for host_id, adapter in self.compatibility["host_adapters"].items():
            manifest_path = (self.contract_root / adapter["manifest"]).resolve()
            if not manifest_path.is_file():
                raise ContractViolation(f"missing {host_id} host manifest")
            manifest = _load_json(manifest_path)
            if manifest["host"] != host_id or manifest["contract_version"] != self.version:
                raise ContractViolation(f"{host_id} host manifest identity mismatch")
            if manifest["status"] != adapter["status"]:
                raise ContractViolation(f"{host_id} host status differs from compatibility.json")
            override_agent_name = manifest.get("model_override_agent_name")
            if not isinstance(override_agent_name, str) or not override_agent_name:
                raise ContractViolation(f"{host_id} model override agent is required")
            if set(manifest["semantic_stages"]) != stages:
                raise ContractViolation(f"{host_id} semantic stages differ from capabilities.json")
            if set(manifest["roles"]) != role_ids:
                raise ContractViolation(f"{host_id} roles differ from capabilities.json")
            if set(manifest["fallback_reasons"]) != fallback_reasons:
                raise ContractViolation(f"{host_id} fallback reasons differ from host.schema.json")
            if manifest.get("concurrency") != {
                "readers": "parallel",
                "writers": "serialized",
                "nested_dispatch": False,
            }:
                raise ContractViolation(f"{host_id} concurrency policy is incompatible")
            for stage_id, stage in manifest["semantic_stages"].items():
                fallbacks = stage.get("fallback_models", [])
                if "fallback_models" in stage and not isinstance(fallbacks, list):
                    raise ContractViolation(
                        f"{host_id} {stage_id} fallback models must be a list"
                    )
                if any(not isinstance(model, str) or not model for model in fallbacks):
                    raise ContractViolation(
                        f"{host_id} {stage_id} fallback models must be nonempty strings"
                    )
                if stage["model"] in fallbacks or len(fallbacks) != len(set(fallbacks)):
                    raise ContractViolation(
                        f"{host_id} {stage_id} fallback model route is invalid"
                    )
            for capability_id, role in manifest["roles"].items():
                default_stage = role.get("default_stage")
                allowed_stages = set(role.get("allowed_stages", []))
                capability = self.capabilities["delegable_capabilities"][capability_id]
                if default_stage != capability["default_semantic_stage"]:
                    raise ContractViolation(f"{host_id} role default differs from shared policy")
                if allowed_stages != set(capability["allowed_semantic_stages"]):
                    raise ContractViolation(f"{host_id} role stages differ from shared policy")
                if default_stage not in stages or default_stage not in allowed_stages:
                    raise ContractViolation(f"{host_id} role has an invalid default stage")
                if not allowed_stages.issubset(stages):
                    raise ContractViolation(f"{host_id} role allows an unknown semantic stage")
                stage = manifest["semantic_stages"][default_stage]
                if role["model"] != stage["model"]:
                    raise ContractViolation(f"{host_id} role model differs from its default stage")
                expected_effort = stage.get("reasoning_effort", stage.get("effort"))
                actual_effort = role.get("reasoning_effort", role.get("effort"))
                if actual_effort != expected_effort:
                    raise ContractViolation(
                        f"{host_id} role effort differs from its default stage"
                    )
                body = (manifest_path.parent / role["body"]).resolve()
                if not body.is_file():
                    raise ContractViolation(f"missing {host_id} role body {role['body']}")
        example_count = 0
        loaded = {}
        for record_type, relatives in self.compatibility["examples"].items():
            loaded[record_type] = []
            for relative in relatives:
                example = _load_json(self.contract_root / relative)
                self.validate(record_type, example)
                loaded[record_type].append(example)
                example_count += 1
        self.validate_result(loaded["result"][0], loaded["dispatch"][0])
        provider_examples = {
            example["provider_id"]: example for example in loaded["provider"]
        }
        if len(provider_examples) != len(loaded["provider"]) or set(provider_examples) != provider_ids:
            raise ContractViolation("provider examples differ from compatibility.json")
        for provider_id, example in provider_examples.items():
            expected = self.compatibility["providers"][provider_id]
            if example["status"] != expected["status"]:
                raise ContractViolation(f"{provider_id} example status differs from compatibility.json")
            if set(example["capabilities"]) != set(expected["operations"]):
                raise ContractViolation(f"{provider_id} operations differ from compatibility.json")
        for relative in self.compatibility["fixture"].values():
            if not (self.contract_root / relative).resolve().is_file():
                raise ContractViolation(f"missing fixture input {relative}")
        role_manifest_path = (
            self.contract_root / self.compatibility["fixture"]["role_manifest"]
        ).resolve()
        role_manifest = _load_json(role_manifest_path)
        role_body = role_manifest_path.parent / role_manifest["body"]
        if not role_body.is_file():
            raise ContractViolation(f"missing fixture role body {role_manifest['body']}")
        release = self.compatibility["release"]
        if release not in RELEASES:
            raise ContractViolation(f"unknown compatibility release {release}")
        entries = self.compatibility["compatibility_entries"]
        for name, entry in entries.items():
            if entry["kind"] not in ENTRY_KINDS:
                raise ContractViolation(f"{name} declares an unknown compatibility kind")
            if entry["status"] not in ENTRY_STATUSES:
                raise ContractViolation(f"{name} declares an unknown compatibility status")
            if entry["replacement"] == name:
                raise ContractViolation(f"{name} cannot replace itself")
            if entry["replacement"] in entries:
                raise ContractViolation(f"{name} names another compatibility entry as its replacement")
            if entry["status"] == "deprecated" and release == "A":
                raise ContractViolation(f"{name} cannot be deprecated before release B")
            if entry["kind"] == "driver" and entry["status"] != "retained":
                raise ContractViolation(f"{name} is a driver and must stay retained")
        discovered_skills = list(self.workflow_root.rglob("SKILL.md"))
        if discovered_skills:
            raise ContractViolation(f"shared workflow resources contain discoverable skills: {discovered_skills!r}")
        return {
            "version": self.version,
            "schemas": len(self.schemas),
            "examples": example_count,
            "capabilities": len(dispatch_capabilities),
            "transitions": len(transitions),
            "providers": len(provider_ids),
            "decks": len(decks),
            "hosts": len(host_ids),
            "roles": len(role_ids),
            "release": release,
            "compatibility_entries": len(entries),
        }


def _git(root, *arguments):
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _section(text, heading):
    match = re.search(
        rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)",
        text,
    )
    return match.group(1).strip() if match else ""


def _headers(text):
    values = {}
    for name, value in re.findall(r"(?m)^- ([A-Za-z][A-Za-z /_-]*):\s*(.+?)\s*$", text):
        values[name] = value.strip().strip("`")
    return values


def _bullets(text):
    return [value.strip() for value in re.findall(r"(?m)^-\s+(.+?)\s*$", text)]


def _open_review_findings(root, reviews):
    findings = []
    for relative in reviews:
        key = _repository_path_key(relative, root)
        if key is None or not key.startswith("reviews/"):
            raise ContractViolation(f"review path must stay under reviews/: {relative}")
        path = root.joinpath(*PurePosixPath(key).parts).resolve()
        if not path.is_file():
            raise ContractViolation(f"review work order does not exist: {relative}")
        text = path.read_text(encoding="utf-8")
        for finding_id in re.findall(r"(?m)^- \[(?: |~)\] \*\*([A-Za-z0-9._/-]+)", text):
            findings.append(f"{key}#{finding_id}")
    return findings


class RepositoryStateProvider:
    provider_id = "repository"

    def __init__(self, repository_root, contract=None):
        self.root = Path(repository_root).resolve()
        resolved_contract = contract or WorkflowContract(self.root / ".agents" / "workflows")
        self.contract = resolved_contract.for_repository(self.root)

    def probe(self):
        _git(self.root, "rev-parse", "--show-toplevel")
        record = {
            "contract_version": self.contract.version,
            "record_type": "probe",
            "provider_id": self.provider_id,
            "status": "available",
            "supported_contract_versions": [self.contract.version],
            "capabilities": [
                "discover",
                "resolve-task",
                "read-state",
                "checkpoint-state",
                "bind-worktree",
            ],
            "authoritative_fields": [
                "portable-intent",
                "next-action",
                "review-work-order",
                "git-identity",
            ],
        }
        return self.contract.validate("provider", record)

    def resolve(self, ledger, workflow_run_id, stage_id):
        ledger_path = (self.root / ledger).resolve()
        try:
            ledger_path.relative_to(self.root)
        except ValueError as error:
            raise ContractViolation("ledger must be inside the repository") from error
        text = ledger_path.read_text(encoding="utf-8")
        headers = _headers(text)
        required = ("Plan", "Roadmap", "Roadmap item", "Worktree", "Branch")
        missing = [name for name in required if not headers.get(name)]
        if missing:
            raise ContractViolation(f"ledger is missing headers {missing!r}")
        artifact_paths = {}
        for name in ("Plan", "Roadmap"):
            relative = headers[name]
            key = _repository_path_key(relative, self.root)
            if key is None or not self.root.joinpath(*PurePosixPath(key).parts).is_file():
                raise ContractViolation(f"ledger {name} must name an existing repository artifact")
            artifact_paths[name] = key
        actual_worktree = Path(_git(self.root, "rev-parse", "--show-toplevel")).resolve()
        recorded_worktree = Path(headers["Worktree"]).resolve()
        if str(recorded_worktree).casefold() != str(actual_worktree).casefold():
            raise ContractViolation("ledger worktree does not match the repository provider")
        branch = _git(self.root, "branch", "--show-current")
        if headers["Branch"] != branch:
            raise ContractViolation("ledger branch does not match the repository provider")
        head = _git(self.root, "rev-parse", "HEAD")
        next_steps = _section(text, "Next Steps")
        if not next_steps:
            raise ContractViolation("ledger has no resolved Next Steps")
        scope_fields = {}
        for field in ("Scope", "Current slice", "Remaining scope", "Done when"):
            match = re.search(rf"(?mi)^{re.escape(field)}:\s*(.+)$", next_steps)
            if match:
                scope_fields[field] = match.group(1).strip()
        if set(scope_fields) != {"Scope", "Current slice", "Remaining scope", "Done when"}:
            raise ContractViolation("ledger Next Steps do not expose the complete execution scope")
        scope_prefixes = tuple(f"{field}:" for field in scope_fields)
        action_steps = "\n".join(
            line for line in next_steps.splitlines() if not line.startswith(scope_prefixes)
        ).strip()
        next_kind = "continue"
        status = "active"
        blocker = None
        transition_kind = "continue"
        owner = None
        resume_condition = None
        target_stage = None
        if action_steps.startswith("Paused:"):
            next_kind = "pause"
            status = "paused"
            transition_kind = "pause"
            first_line = action_steps.splitlines()[0]
            paused = first_line.removeprefix("Paused:").strip()
            owner = re.split(r"\s+[—-]\s+", paused, maxsplit=1)[0]
            resume_condition = first_line
        elif action_steps.startswith("Blocked:"):
            next_kind = "block"
            status = "blocked"
            transition_kind = "block"
            fields = dict(
                line.split(":", 1)
                for line in action_steps.splitlines()
                if ":" in line and line.split(":", 1)[0] in {"Blocked", "Blocked by", "Unblock action", "Resume when"}
            )
            if set(fields) != {"Blocked", "Blocked by", "Unblock action", "Resume when"}:
                raise ContractViolation("blocked Next Steps do not contain the four required fields")
            owner = fields["Blocked by"].strip()
            resume_condition = fields["Resume when"].strip()
            blocker = self.contract.gate(
                "dependency",
                "open",
                owner,
                fields["Unblock action"].strip(),
                resume_condition,
                [fields["Blocked"].strip()],
            )
        elif action_steps.startswith("Transfer:"):
            next_kind = "transfer"
            transition_kind = "transfer"
            fields = dict(
                line.split(":", 1)
                for line in action_steps.splitlines()
                if ":" in line
                and line.split(":", 1)[0]
                in {"Transfer", "Transfer to", "Resume stage", "Resume when"}
            )
            if set(fields) != {"Transfer", "Transfer to", "Resume stage", "Resume when"}:
                raise ContractViolation("transfer Next Steps do not contain the four required fields")
            owner = fields["Transfer to"].strip()
            target_stage = fields["Resume stage"].strip()
            resume_condition = fields["Resume when"].strip()
        elif action_steps.startswith("Complete:") or action_steps.startswith("Terminal:"):
            next_kind = "complete"
            status = "complete"
            transition_kind = "complete"
        reviews_text = _section(text, "Reviews")
        reviews = []
        for candidate in re.findall(r"(?:`|\()((?:reviews/)[^`)\s]+\.md)", reviews_text):
            key = _repository_path_key(candidate, self.root)
            if key is None or not key.startswith("reviews/"):
                raise ContractViolation(f"review path must stay under reviews/: {candidate}")
            if key not in reviews:
                reviews.append(key)
        state = {
            "contract_version": self.contract.version,
            "workflow_id": headers["Roadmap item"],
            "workflow_run_id": workflow_run_id,
            "stage_id": stage_id,
            "status": status,
            "provider_id": self.provider_id,
            "owner": {
                "repository": self.root.name,
                "worktree": str(actual_worktree),
                "branch": branch,
                "head": head,
            },
            "artifacts": {
                "plan": artifact_paths["Plan"],
                "ledger": ledger_path.relative_to(self.root).as_posix(),
                "roadmap": artifact_paths["Roadmap"],
                "reviews": reviews,
            },
            "decisions": _bullets(_section(text, "Decisions, discoveries, blockers, and deviations")),
            "open_findings": _open_review_findings(self.root, reviews),
            "next_action": {
                "kind": next_kind,
                "description": action_steps,
                "scope": scope_fields["Scope"],
                "current_slice": scope_fields["Current slice"],
                "remaining_scope": scope_fields["Remaining scope"],
                "done_when": scope_fields["Done when"],
            },
            "transition": self.contract.transition(
                transition_kind,
                "The repository ledger resolved the current next action.",
                target_stage_id=(
                    target_stage
                    if transition_kind == "transfer"
                    else stage_id if transition_kind == "continue" else None
                ),
                resume_condition=resume_condition,
            ),
        }
        if owner:
            state["next_action"]["owner"] = owner
        if resume_condition:
            state["next_action"]["resume_condition"] = resume_condition
        if blocker:
            state["blocker"] = blocker
        return self.contract.validate("state", state)

    def validate_checkpoint(self, state):
        self.contract.validate("state", state)
        ledger = (self.root / state["artifacts"]["ledger"]).resolve()
        try:
            ledger.relative_to(self.root)
        except ValueError as error:
            raise ContractViolation("checkpoint ledger must be inside the repository") from error
        if not ledger.is_file():
            raise ContractViolation("checkpoint ledger does not exist")
        current = self.resolve(
            state["artifacts"]["ledger"],
            state["workflow_run_id"],
            state["stage_id"],
        )
        if current != state:
            raise ContractViolation("checkpoint state differs from current repository state")
        return state


def select_state_provider(repository_root, contract=None):
    root = Path(repository_root).resolve()
    resolved_contract = (
        contract or WorkflowContract(root / ".agents" / "workflows")
    ).for_repository(root)
    return RepositoryStateProvider(root, resolved_contract)
