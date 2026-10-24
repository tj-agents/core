# Portable native permission defaults

Owner: Codex session 01a16e5b-9e5a-75e1-86d4-fda224713323.
Source checkout: isolated clone based on Core main d7724c7a5f6f807b5e2fd173451141bbb8808ea1.

The user authorizes bypass permissions by default for Claude and Codex. Store a host-neutral enum at
`configuration.core.permissions` in `.agents/settings.json`: `bypass` (including when omitted) or
`standard`. Machine maps the enum into each host's native settings through repository generation and
the existing machine setup entry points. No machine paths or per-repository allowlist workaround belongs
in this configuration. Merge policy and merge gates remain the user's separate work.

Implementation is in progress. The original Core checkout contains active changes and remains untouched.
The nutrition standards handoff is still unacknowledged; this is a distinct requested setup repair.
Current session restrictions still prevent applying profile settings. Requesting the user to switch
the current conversation to Full access does not itself establish that the active policy changed.

Acceptance: strict enum validation; correct native mappings; preserve unrelated settings; migrate conflicting
legacy Codex permission keys; project/local generation and setup converge; clean-clone and both-host
source checks; fresh Windows/Linux native runtime verification or an exact outstanding gate.

Verified:

- Enum, mappings, legacy Codex migration, settings preservation and malformed-input regressions pass.
- Repository/local settings generation, adoption and selection regressions pass; setup converges in
  Windows and Linux fixture contexts. Generated installed Machine scripts also pass the repository check.
- Source generation freshness, catalog digest checks and tier payload checks pass. Catalog/package output
  stays uncommitted as required by Core's current instructions.
- Installed Windows Codex 0.163.0: fresh app-server `config/read` reported `never` and
  `:danger-full-access` for `bypass`, and `on-request` and `:workspace` for `standard`.
- Installed Windows Claude Code 2.1.302: fresh SDK initialization reported `current_permission_mode`
  as `bypassPermissions` for `bypass`, and `default` for `standard`. No model request was sent.
- Fresh project precedence: Codex's trusted project bypass overrides a standard user profile. Claude
  ignored bypass from a project file, matching its documented 2.1.257+ restriction. Corrected generation
  to omit the inert Claude project value; its effective bypass default comes from the reproducible
  machine-setup step that writes native user settings. `standard` remains a supported project override.
- Rechecked fresh projects after that correction with the native bypass user defaults installed:
  Codex reported `:danger-full-access`/`:workspace`, and Claude reported
  `bypassPermissions`/`default`, for project modes `bypass`/`standard` respectively.

Outstanding:

- The broader source suite was interrupted after the Claude scope correction superseded its moving
  candidate. It had reported environment/process-observer and hook-integrity errors; there is no final
  full-suite verdict for this source candidate. Full Windows/Linux CI remains required.
- Native Linux acceptance remains pending. The independent `review-lens` fallback could not start:
  the assigned gpt-5.3-codex-spark model is unsupported for this ChatGPT account. Applied the documented
  parent-review fallback; do not claim an independent review ran. The parent also found and corrected
  Claude's project-scope restriction through fresh native execution.
- Applying to the real user profiles is not done. The supported scoped setup check was blocked in its
  required GitHub identity precondition by the current sandbox's denied network access. The same session
  also denies writes outside the nutrition-tracker workspace. Resolver: the user's native Full access
  selection; resume when the active policy permits profile writes and the identity check can run.
- The original nutrition receipt is unchanged. Resume that handoff only after acknowledgment succeeds.

Next action: finish the final focused checks and publish the frozen source as a draft for the required
Windows/Linux CI. Real profile application remains gated on the current host permission change above.
Do not include generated plugin distribution changes in a PR.

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/machine/scripts/host_permissions.py",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Maps the shared bypass or standard mode to native permissions.defaultMode",
      "source": ".agents/machine/scripts/host_permissions.py",
      "mapping": "Machine setup profile settings and repository configuration generation",
      "verification": {"level": "planned", "result": "pending", "evidence": "Windows Claude 2.1.302 fresh initialization passed both native modes; Linux runtime acceptance remains pending"}
    },
    {
      "host": "codex",
      "behavior": "Maps the shared bypass or standard mode to native approval_policy and default_permissions",
      "source": ".agents/machine/scripts/host_permissions.py",
      "mapping": "Machine setup profile settings and repository configuration generation",
      "verification": {"level": "planned", "result": "pending", "evidence": "Windows Codex 0.163.0 fresh config/read passed both native modes; Linux runtime acceptance remains pending"}
    }
  ]
}
```
