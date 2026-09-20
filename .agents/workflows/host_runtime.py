import copy
import hashlib
import os
import shutil
import subprocess
import threading
import weakref
from pathlib import Path

from workflow_runtime import ContractViolation, WorkflowContract, _load_json, _repository_path_key


class WriterReconciliationRequired(ContractViolation):
    def __init__(self, detail, observed_paths):
        super().__init__(detail)
        self.observed_paths = tuple(sorted(observed_paths))


class RepositoryWriterLock:
    def __init__(self, repository_root):
        self.repository_root = Path(repository_root).resolve()
        self.stream = None

    def acquire(self):
        try:
            completed = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.repository_root),
                    "rev-parse",
                    "--git-path",
                    "agent-workflows/writer.lock",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            path = Path(completed.stdout.strip())
            if not path.is_absolute():
                path = self.repository_root / path
            path = path.resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            stream = path.open("a+b")
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
        except (OSError, subprocess.SubprocessError) as error:
            raise ContractViolation(f"cannot open repository writer lock: {error}") from error
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            stream.close()
            raise ContractViolation("another writer lease is already active") from error
        self.stream = stream

    def release(self):
        stream = self.stream
        if stream is None:
            return
        self.stream = None
        try:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            stream.close()


class WriterLeaseRegistry:
    repositories = weakref.WeakValueDictionary()
    repositories_lock = threading.Lock()

    def __init__(self, repository_root=None):
        self.active = None
        self.lock = threading.Lock()
        self.repository_lock = (
            RepositoryWriterLock(repository_root) if repository_root is not None else None
        )

    @classmethod
    def for_repository(cls, repository_root):
        key = os.path.normcase(str(Path(repository_root).resolve()))
        with cls.repositories_lock:
            registry = cls.repositories.get(key)
            if registry is None:
                registry = cls(repository_root)
                cls.repositories[key] = registry
            return registry

    def acquire(self, dispatch):
        lease = dispatch["permissions"].get("writer_lease")
        if lease is None:
            return None
        with self.lock:
            if self.active is not None:
                raise ContractViolation("another writer lease is already active")
            if self.repository_lock is not None:
                self.repository_lock.acquire()
            self.active = {
                "dispatch_id": dispatch["dispatch_id"],
                "lease_id": lease["lease_id"],
                "paths": tuple(lease["paths"]),
            }
        return lease["lease_id"]

    def release(self, dispatch_id):
        with self.lock:
            if self.active and self.active["dispatch_id"] == dispatch_id:
                if self.repository_lock is not None:
                    self.repository_lock.release()
                self.active = None


class RepositoryChangeObserver:
    def __init__(self, repository_root):
        self.repository_root = Path(repository_root).resolve()

    def capture(self):
        return {path: self._fingerprint(path) for path in self._visible_paths()}

    def changed_since(self, baseline):
        current = self.capture()
        return {
            path
            for path in set(baseline) | set(current)
            if baseline.get(path) != current.get(path)
        }

    def _visible_paths(self):
        tracked = self._git("diff", "HEAD", "--name-only", "--no-renames", "-z", "--")
        untracked = self._git("ls-files", "--others", "--exclude-standard", "-z", "--")
        return {
            path.replace("\\", "/")
            for path in (tracked + untracked).split("\0")
            if path
        }

    def _git(self, *arguments):
        try:
            completed = subprocess.run(
                ["git", "-C", str(self.repository_root), *arguments],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise ContractViolation(f"cannot observe repository changes: {error}") from error
        return completed.stdout

    def _fingerprint(self, relative):
        path = self.repository_root / relative
        try:
            if path.is_symlink():
                return ("link", os.readlink(path))
            if not path.exists():
                return ("missing",)
            if path.is_dir():
                return ("directory",)
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
        except OSError as error:
            raise ContractViolation(f"cannot observe repository path {relative!r}: {error}") from error
        return ("file", digest.hexdigest())


class HostAdapterRegistry:
    def __init__(
        self,
        workflow_root,
        repository_root,
        executable_resolver=None,
        command_runner=None,
        lease_registry=None,
        repository_observer=None,
    ):
        self.workflow_root = Path(workflow_root).resolve()
        self.repository_root = Path(repository_root).resolve()
        self.contract = WorkflowContract(
            self.workflow_root,
            repository_root=self.repository_root,
        )
        self.executable_resolver = executable_resolver or shutil.which
        self.command_runner = command_runner or subprocess.run
        self.lease_registry = lease_registry or WriterLeaseRegistry.for_repository(self.repository_root)
        self.repository_observer = repository_observer or RepositoryChangeObserver(self.repository_root)
        self.active_lock = threading.Lock()
        self.manifests = {
            host: _load_json(self.workflow_root / "hosts" / f"{host}.json")
            for host in self.contract.compatibility["host_adapters"]
        }
        self.active_dispatches = {}
        self.model_failures = {}

    def probe(self, host):
        manifest = self._manifest(host)
        surface = self.repository_root / manifest["delivery"]["project_directory"]
        if not surface.is_dir() and self.workflow_root.parent.name == ".agents":
            source_root = self.workflow_root.parent.parent
            surface = (
                source_root
                / "plugins"
                / "engineering"
                / manifest["delivery"]["plugin_directory"]
            )
        elif (
            not surface.is_dir()
            and manifest["delivery"].get("plugin_loading") == "supported"
        ):
            surface = self.workflow_root.parent / manifest["delivery"]["plugin_directory"]
        available_roles = sorted(
            capability
            for capability, role in manifest["roles"].items()
            if (surface / role["filename"]).is_file()
        )
        executable = self.executable_resolver(manifest["probe"]["command"])
        if executable is None:
            return self._probe_record(host, "unavailable", "host-unavailable", None, available_roles)
        try:
            completed = self.command_runner(
                [executable, *manifest["probe"]["version_arguments"]],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return self._probe_record(host, "unavailable", "host-unavailable", None, available_roles)
        if completed.returncode != 0:
            return self._probe_record(host, "unavailable", "host-unavailable", None, available_roles)
        output = (completed.stdout or completed.stderr).strip().splitlines()
        if not output:
            return self._probe_record(host, "unavailable", "host-unavailable", None, available_roles)
        version = output[0]
        return self._probe_record(host, "available", None, version, available_roles)

    def prepare(self, host, dispatch, probe=None, available_models=None):
        self.contract.validate_dispatch(dispatch)
        manifest = self._manifest(host)
        capability = dispatch["capability"]
        semantic_stage = dispatch.get("semantic_stage")
        if capability not in manifest["roles"]:
            return self._fallback(
                host,
                dispatch["dispatch_id"],
                "unsupported-capability",
                capability,
                semantic_stage=semantic_stage,
            )
        role = manifest["roles"][capability]
        semantic_stage = semantic_stage or role["default_stage"]
        if semantic_stage not in role["allowed_stages"]:
            return self._fallback(
                host,
                dispatch["dispatch_id"],
                "unsupported-capability",
                f"{capability} cannot execute the {semantic_stage} stage",
                semantic_stage=semantic_stage,
            )
        stage = manifest["semantic_stages"][semantic_stage]
        observed = probe or self.probe(host)
        self.contract.validate("host", observed)
        if observed["record_type"] != "host-probe" or observed["host"] != host:
            raise ContractViolation(f"{host} adapter received a probe for a different host")
        if observed["status"] != "available":
            reason = observed["reason_code"] or "host-unavailable"
            return self._fallback(
                host,
                dispatch["dispatch_id"],
                reason,
                "host capability probe failed",
                semantic_stage=semantic_stage,
            )
        if capability not in observed["available_roles"]:
            return self._fallback(
                host,
                dispatch["dispatch_id"],
                "role-unavailable",
                capability,
                semantic_stage=semantic_stage,
            )
        model_route = [stage["model"], *stage.get("fallback_models", [])]
        route_key = self._model_route_key(host, dispatch, capability, semantic_stage)
        failed_models = self.model_failures.get(route_key, set())
        eligible_models = [model for model in model_route if model not in failed_models]
        selected_model = eligible_models[0] if eligible_models else None
        if available_models is not None:
            selected_model = next(
                (model for model in eligible_models if model in available_models),
                None,
            )
        if selected_model is None:
            transition = "pause" if stage["unavailable"] == "decision" else "fallback"
            return self._fallback(
                host,
                dispatch["dispatch_id"],
                "model-unavailable",
                ", ".join(model_route),
                transition,
                semantic_stage,
            )
        lease_id = dispatch["permissions"].get("writer_lease", {}).get("lease_id")
        role_agent_name = role["agent_name"]
        agent_name = role_agent_name
        if selected_model != role["model"]:
            agent_name = manifest["model_override_agent_name"]
        invocation = {
            "contract_version": self.contract.version,
            "record_type": "host-invocation",
            "host": host,
            "dispatch_id": dispatch["dispatch_id"],
            "capability": capability,
            "semantic_stage": semantic_stage,
            "agent_name": agent_name,
            "role_agent_name": role_agent_name,
            "role_body": role["body"],
            "primary_model": stage["model"],
            "model": selected_model,
            "model_selection": (
                "primary" if selected_model == stage["model"] else "fallback"
            ),
            "reasoning_effort": stage.get(
                "reasoning_effort",
                stage.get("effort", "medium"),
            ),
            "mode": dispatch["permissions"]["mode"],
            "writer_lease_id": lease_id,
        }
        validated = self.contract.validate("host", invocation)
        with self.active_lock:
            if dispatch["dispatch_id"] in self.active_dispatches:
                raise ContractViolation(f"dispatch {dispatch['dispatch_id']!r} is already active")
            self.lease_registry.acquire(dispatch)
            try:
                duplicate = any(
                    active["host"] == host
                    and active["dispatch"]["workflow_id"] == dispatch["workflow_id"]
                    and active["dispatch"]["workflow_run_id"] == dispatch["workflow_run_id"]
                    and active["dispatch"]["stage_id"] == dispatch["stage_id"]
                    and active["dispatch"]["capability"] == capability
                    and active["semantic_stage"] == semantic_stage
                    for active in self.active_dispatches.values()
                )
                if duplicate:
                    raise ContractViolation("an equivalent semantic-stage dispatch is already active")
                snapshot = self.repository_observer.capture() if lease_id else None
                self.active_dispatches[dispatch["dispatch_id"]] = {
                    "host": host,
                    "dispatch": copy.deepcopy(dispatch),
                    "invocation": copy.deepcopy(validated),
                    "model_route_key": route_key,
                    "semantic_stage": semantic_stage,
                    "snapshot": snapshot,
                    "state": "running",
                }
            except Exception:
                self.lease_registry.release(dispatch["dispatch_id"])
                raise
        return validated

    def report_model_unavailable(self, host, dispatch, invocation, detail):
        manifest = self._manifest(host)
        dispatch_id = dispatch["dispatch_id"]
        if not isinstance(detail, str) or not detail:
            raise ContractViolation("model failure detail is required")
        with self.active_lock:
            active = self.active_dispatches.get(dispatch_id)
            if active is None:
                return self._fallback(
                    host,
                    dispatch_id,
                    "invalid-result",
                    "dispatch is not active",
                )
            if active["host"] != host:
                return self._fallback(
                    host,
                    dispatch_id,
                    "invalid-result",
                    "dispatch belongs to another host",
                )
            if active["state"] != "running":
                raise ContractViolation("dispatch is not running")
            if active["dispatch"] != dispatch or active["invocation"] != invocation:
                raise ContractViolation("model failure differs from the prepared invocation")
            semantic_stage = active["semantic_stage"]
            stage = manifest["semantic_stages"][semantic_stage]
            model_route = [stage["model"], *stage.get("fallback_models", [])]
            failed_model = invocation["model"]
            failures = self.model_failures.setdefault(active["model_route_key"], set())
            failures.add(failed_model)
            remaining = [model for model in model_route if model not in failures]
            transition = (
                "fallback"
                if remaining or stage["unavailable"] != "decision"
                else "pause"
            )
            terminal = self._fallback(
                host,
                dispatch_id,
                "model-unavailable",
                detail,
                transition,
                semantic_stage,
                failed_model=failed_model,
                next_model=remaining[0] if remaining else None,
            )
            self._release(dispatch_id)
            return terminal

    def accept_result(self, host, dispatch, result):
        self._manifest(host)
        dispatch_id = dispatch["dispatch_id"]
        with self.active_lock:
            active = self.active_dispatches.get(dispatch_id)
            if active is None:
                return self._fallback(host, dispatch_id, "invalid-result", "dispatch is not active")
            if active["host"] != host:
                return self._fallback(host, dispatch_id, "invalid-result", "dispatch belongs to another host")
            if active["state"] == "reconciliation-required":
                raise ContractViolation("dispatch requires parent reconciliation")
            try:
                if active["dispatch"] != dispatch:
                    raise ContractViolation("dispatch differs from the prepared envelope")
                validated = self.contract.validate_result(result, active["dispatch"])
            except ContractViolation as error:
                return self._invalid_result(active, error)
            try:
                self._validate_writer_changes(active, result)
            except WriterReconciliationRequired as error:
                return self._require_reconciliation(
                    active,
                    "invalid-result",
                    str(error),
                    error.observed_paths,
                )
            self._release(dispatch_id, clear_model_failures=True)
            return validated

    def request_cancel(self, host, dispatch_id):
        self._manifest(host)
        with self.active_lock:
            active = self.active_dispatches.get(dispatch_id)
            if active is None:
                return self._fallback(host, dispatch_id, "invalid-result", "dispatch is not active")
            if active["host"] != host:
                return self._fallback(host, dispatch_id, "invalid-result", "dispatch belongs to another host")
            if active["state"] != "running":
                raise ContractViolation("dispatch is not running")
            active["state"] = "cancel-requested"
            return self.contract.validate(
                "host",
                {
                    "contract_version": self.contract.version,
                    "record_type": "host-cancel-request",
                    "host": host,
                    "dispatch_id": dispatch_id,
                },
            )

    def confirm_cancelled(self, host, dispatch_id, detail="The host confirmed cancellation."):
        self._manifest(host)
        with self.active_lock:
            active = self.active_dispatches.get(dispatch_id)
            if active is None:
                return self._fallback(host, dispatch_id, "invalid-result", "dispatch is not active")
            if active["host"] != host:
                return self._fallback(host, dispatch_id, "invalid-result", "dispatch belongs to another host")
            if active["state"] != "cancel-requested":
                raise ContractViolation("cancellation was not requested")
            try:
                observed_paths = self._validate_writer_changes(active, None)
            except WriterReconciliationRequired as error:
                return self._require_reconciliation(
                    active,
                    "invalid-result",
                    str(error),
                    error.observed_paths,
                )
            if observed_paths:
                return self._require_reconciliation(
                    active,
                    "cancelled",
                    detail,
                    observed_paths,
                )
            terminal = self._fallback(host, dispatch_id, "cancelled", detail, "cancel")
            self._release(dispatch_id, clear_model_failures=True)
            return terminal

    def complete_reconciliation(
        self,
        host,
        dispatch_id,
        detail="The parent completed writer reconciliation.",
    ):
        self._manifest(host)
        with self.active_lock:
            active = self.active_dispatches.get(dispatch_id)
            if active is None:
                return self._fallback(host, dispatch_id, "invalid-result", "dispatch is not active")
            if active["host"] != host:
                return self._fallback(host, dispatch_id, "invalid-result", "dispatch belongs to another host")
            if active["state"] != "reconciliation-required":
                raise ContractViolation("dispatch does not require reconciliation")
            reconciliation = active["reconciliation"]
            terminal_detail = f"{reconciliation['detail']} {detail}"
            transition = "cancel" if reconciliation["reason_code"] == "cancelled" else "fallback"
            terminal = self._fallback(
                host,
                dispatch_id,
                reconciliation["reason_code"],
                terminal_detail,
                transition,
            )
            self._release(dispatch_id, clear_model_failures=True)
            return terminal

    def _manifest(self, host):
        if host not in self.manifests:
            raise ContractViolation(f"unknown host adapter {host!r}")
        return self.manifests[host]

    def _probe_record(self, host, status, reason_code, version, available_roles):
        return self.contract.validate(
            "host",
            {
                "contract_version": self.contract.version,
                "record_type": "host-probe",
                "host": host,
                "status": status,
                "reason_code": reason_code,
                "version": version,
                "available_roles": available_roles,
            },
        )

    def _fallback(
        self,
        host,
        dispatch_id,
        reason_code,
        detail,
        transition="fallback",
        semantic_stage=None,
        failed_model=None,
        next_model=None,
    ):
        manifest = self._manifest(host)
        if reason_code not in manifest["fallback_reasons"]:
            raise ContractViolation(f"unsupported fallback reason {reason_code!r}")
        record = {
            "contract_version": self.contract.version,
            "record_type": "host-fallback",
            "host": host,
            "dispatch_id": dispatch_id,
            "reason_code": reason_code,
            "detail": detail,
            "parent_transition": transition,
        }
        if semantic_stage is not None:
            record["semantic_stage"] = semantic_stage
        if failed_model is not None:
            record["failed_model"] = failed_model
            record["next_model"] = next_model
        return self.contract.validate(
            "host",
            record,
        )

    def _invalid_result(self, active, error):
        try:
            observed_paths = self._validate_writer_changes(active, None)
        except WriterReconciliationRequired as observation_error:
            detail = f"{error}; {observation_error}"
            return self._require_reconciliation(
                active,
                "invalid-result",
                detail,
                observation_error.observed_paths,
            )
        if observed_paths:
            return self._require_reconciliation(
                active,
                "invalid-result",
                str(error),
                observed_paths,
            )
        dispatch_id = active["dispatch"]["dispatch_id"]
        terminal = self._fallback(active["host"], dispatch_id, "invalid-result", str(error))
        self._release(dispatch_id, clear_model_failures=True)
        return terminal

    def _require_reconciliation(self, active, reason_code, detail, observed_paths):
        dispatch = active["dispatch"]
        record = self.contract.validate(
            "host",
            {
                "contract_version": self.contract.version,
                "record_type": "host-reconciliation-required",
                "host": active["host"],
                "dispatch_id": dispatch["dispatch_id"],
                "writer_lease_id": dispatch["permissions"]["writer_lease"]["lease_id"],
                "reason_code": reason_code,
                "detail": detail,
                "observed_paths": list(observed_paths),
            },
        )
        active["state"] = "reconciliation-required"
        active["reconciliation"] = {
            "reason_code": reason_code,
            "detail": detail,
            "observed_paths": tuple(observed_paths),
        }
        return record

    def _model_route_key(self, host, dispatch, capability, semantic_stage):
        return (
            host,
            dispatch["workflow_id"],
            dispatch["workflow_run_id"],
            dispatch["stage_id"],
            capability,
            semantic_stage,
        )

    def _release(self, dispatch_id, clear_model_failures=False):
        active = self.active_dispatches.pop(dispatch_id)
        if clear_model_failures:
            self.model_failures.pop(active["model_route_key"], None)
        self.lease_registry.release(dispatch_id)

    def _validate_writer_changes(self, active, result):
        snapshot = active["snapshot"]
        if snapshot is None:
            return ()
        try:
            actual_paths = self.repository_observer.changed_since(snapshot)
        except ContractViolation as error:
            raise WriterReconciliationRequired(str(error), ()) from error
        actual = {}
        for path in actual_paths:
            key = _repository_path_key(path, self.repository_root)
            if key is None:
                raise WriterReconciliationRequired(
                    f"observed writer path escapes the repository: {path!r}",
                    actual_paths,
                )
            actual[key] = path
        lease = {
            _repository_path_key(path, self.repository_root)
            for path in active["dispatch"]["permissions"]["writer_lease"]["paths"]
        }
        unleased = sorted(actual.keys() - lease)
        if unleased:
            raise WriterReconciliationRequired(
                f"writer changed unleased repository paths: {unleased!r}",
                actual.values(),
            )
        if result is None:
            return tuple(sorted(actual.values()))
        reported = {
            _repository_path_key(path, self.repository_root)
            for path in result["writer"]["changed_paths"] + result["writer"]["partial_paths"]
        }
        if set(actual) != reported:
            raise WriterReconciliationRequired(
                f"writer result paths differ from observed repository changes: "
                f"observed={sorted(actual)!r}, reported={sorted(reported)!r}",
                actual.values(),
            )
        return tuple(sorted(actual.values()))
