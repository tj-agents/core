# Offline Unix shell-profile oracle

## Outcome and authority

Deliver phase 1a: a test-only offline oracle for all 394 source-backed Unix shell-profile rows, including edition/conditional distinctions, vendor variants, and signed zsh maps. Validate completeness and established old-`extract_command` compatibility only; do not change or claim production parser behavior.

The accepted sequence is 1a Unix oracle; 1b PowerShell descriptors plus 80 acceptance cases (33 literal / 24 nonliteral / 23 refusal; 474 total rows if other counts remain), only after 1a normal merge and causal publication; then phase 2 extractor/consumer changes after both oracle phases publish. Phase 1b requires its complete contract before execution. No stacked PR. Parent owns review and all publication/delivery decisions. Authorization covers Claude/Codex source work, not installation, billing/protection bypass, credential changes, or repository opt-in.

Use the [immutable published design](https://github.com/tj-agents/docs/blob/0d74933ff0889251f6228c96d81b7553ed95a736/plans/tj-agents-auto-merge/PLAN.md). The parent-accepted split preserves readable data below the 1,000-line trigger; never minify or drop coverage.

## Current checkout and ownership

Work in Core checkout `C:/Users/TommySeery/source/repos/tj-agents/core/.worktrees/Fix-ShellCommandOperands`, branch `Fix/ShellCommandOracle`, at committed SO01/SO02 candidate `9add4e22eece41c3c48b60847ac64f3f2ced820d` based on `73f1fbcc24efdda8ed1c0b0ccf07dc4064e7782c`. SO03 owns only the helper, its existing test, and this Goal; it preserves the source fixtures and review work order. Parent owns the review work order, staging, commit, fresh incremental review, and delivery. Preserve old candidate `7e8b650f721b3c872446f9205922efe685be81b1` and stashes `1f6d7365409f259710ae9873ceebdbef041cbfcb` / `f51170a6a0982c976f727495dd6b7d03bb386962`.

Primary-source recovery is complete. The remediation's first focused run exposed a test-only `KeyError` for signed-map rows; after reading absent conditions with `get`, captured `oracle-r3` passed all 7 tests. SO03 captured `oracle-r4` passing all 7 focused tests after enforcing the fixed source condition/derivation metadata. Credential (23), catalog, harness, and generated-output checks also passed. Linux exact-head CI and native activation remain pending. Supplementary audit `.agents/continuation/shell-primary-source-recovery.json` has SHA-256 `e02ba2c9f94d3c144e88db4821343e044a79c290e37d651566410de3c906d55a`; all execution-critical source facts are recorded here.

Phase 1a owns only these four files plus Goal: `.agents/hooks/tests/fixtures/shell_option_profiles.json`, `.agents/hooks/tests/fixtures/shell_profile_sources.json`, `.agents/hooks/tests/fixtures/shell_profile_oracle.py`, `.agents/hooks/tests/test_shell_profile_oracle.py`, and `plans/shell-command-operands/GOAL.md`. Do not create `shell_extraction_cases.json`, add PowerShell descriptors, change production runtime/native wiring/consumers, or alter the existing `.agents/plugins/harness/engineering.json` Claude/Codex mapping.

## Phase 1a oracle contract

The profile fixture holds 394 Unix rows: Bash 105, dash union 19, zsh names/aliases 197, and signed zsh native/sh/ksh maps 73. Store stable source-backed IDs, typed group/meaning, source edition, and conditional/vendor variants. Shared metadata belongs at group level. The source fixture records canonical/observed URL, edition/revision, member hash, source location, condition, and derivation; the standard-library helper validates offline with no fetch in tests or CI. Assert counts, IDs/groups/source links, variants/maps and malformed records.

Bash rises from 104 to 105 because the uppercase-`O` union is 59: 58 GNU `shopt.def` names plus vendor `completion_strip_exe`; retain `syslog_history` under `SYSLOG_HISTORY && SYSLOG_SHOPT` and vendor `igncr` separately under `__CYGWIN__`. The vendor pin below is Bash 5.3.015 and does not prove installed Git-for-Windows 5.2.37 contents. Dash union is 19 and contains `privileged`, not `priv`: Debian maps short `p` to exact `privileged`; `strcmp` gives no alias/prefix. Upstream 0.5.13.5 is a separate 18-name edition. Phase 1b must refuse a `priv` case and accept literal `privileged`, preserving the 80 partition unless a real input requires a reported change.

Phase 1a tests only established facade behavior: supported raw command fields; ordinary Bash/sh/zsh/dash `-c` with sole script; unknown-executable joining; non-shell and nondictionary or empty tool inputs returning `None`. Do not test future parser/refusal/last-argv outcomes here.

Final verification after the SO03 provenance correction: captured `oracle-r4` passed all 7 focused oracle tests.

## Primary source evidence

These hashes identify bytes actually inspected; no archive signature, tag-to-archive cryptographic authentication, or installed-package equivalence is claimed. Source recovery used the immutable references and cached bytes below. The source fixtures/tests must not fetch sources at runtime or in CI.

| Profile and source | Edition, immutable URL, and inspected bytes |
|---|---|
| GNU Bash | `5.2.37`, canonical [`ftp.gnu.org` archive](https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz); retrieved from [`ibiblio mirror`](https://mirrors.ibiblio.org/pub/mirrors/gnu/bash/bash-5.2.37.tar.gz). Archive SHA-256 `9599b22ecd1d5787ad7d3b7bf0c59f312b3396d1e281175dd1f8a4014da621ff`. Members: `builtins/shopt.def` `c1bb281be9ac815fce0ab20022689d8ca8702e63c0de2cae94ebc9b4e812d91d`; `shell.c` `69a6622c9460b228632cf4deb57233e59159f2bac8a600baa3c1f72635fbeff0`; `flags.c` `62b377da2431b15843a4d13a2814b387eb95bed789e2a0c618efce7c1646719f`; `builtins/set.def` `60cc498e28d4e9edd49a1415f1b5f92cfd326c6cb0d17d0d0827757f23580793`; `patchlevel.h` `fa3955e6c42bf4a8a1ab6077ea96991c95bb1024a86768eea4c733010112ed15` (PATCHLEVEL 37). `shopt.def` row `syslog_history` is conditional on `SYSLOG_HISTORY && SYSLOG_SHOPT`.
| Git-for-Windows/MSYS Bash variant | Immutable [`MSYS2-packages` PKGBUILD](https://raw.githubusercontent.com/git-for-windows/MSYS2-packages/39014c49183d3635c93151c390604318d2655da1/bash/PKGBUILD), revision `39014c49183d3635c93151c390604318d2655da1`, SHA-256 `b2aeaff6799073b992b716efd1da2753198ca099dee9de05315ceca431f7ad50`; [`Cygwin patch`](https://raw.githubusercontent.com/git-for-windows/MSYS2-packages/39014c49183d3635c93151c390604318d2655da1/bash/0001-bash-4.4-cygwin.patch), SHA-256 `81f5fcb0990199e555f78ecf57dd6874d4b0ca781d4e7d26eac5a76ba729ac59`. PKGBUILD declares base `5.3`, patchlevel `015`; `completion_strip_exe` is `shopt/O` and `igncr` is `set/o`, both under `__CYGWIN__`. This is a separate pinned vendor variant, not evidence of installed 5.2.37 package contents.
| Debian dash package | `.dsc` at [`ftp.debian.org`](https://ftp.debian.org/debian/pool/main/d/dash/dash_0.5.12-2.dsc), version `0.5.12-2`, SHA-256 `25c0fb805c735fdb7470ce485ce76dae1a7b6c04efdfb0fdac5eab921cbd78a5`; orig archive [`dash_0.5.12.orig.tar.gz`](https://ftp.debian.org/debian/pool/main/d/dash/dash_0.5.12.orig.tar.gz), SHA-256 `6a474ac46e8b0b32916c4c60df694c82058d3297d8b385b74508030ca4a8f28a`; Debian patch archive [`dash_0.5.12-2.debian.tar.xz`](https://ftp.debian.org/debian/pool/main/d/dash/dash_0.5.12-2.debian.tar.xz), SHA-256 `bddd9129215eb60f4cc43a0ffdcc42d8f25e0bd09730520d599a2b7bc492e375`. The inspected `.dsc` declares archive sizes/hashes matching these bytes; its included PGP signature was not verified. Raw orig members `src/options.h` SHA-256 `12f632ce480f03ccbe67e640c2ea24b7de713033015d52336a6d8c8845d32132`, `src/options.c` `0a883024ad3a298071a6269a13901a975b0be9954c576326c8fad75e94c91855`. Debian `series` SHA-256 `1e0f7009609809bbe00204190e41788cf12a4e293d3f7fe6ee8206983adac9bf`; relevant patches `9001-Add-privmode-Part-1.diff` `be5aaf6df52edd49fd54c0978c964b4d0da59eb1d6c712de6a07063c276e6b66`, `9002-Add-privmode-Part-2.diff` `5ca803204938bc6710c88b425ea3c8b024ff0eca3e725246cb4f904eba86da7e`, and the series-listed `0020-Update-manpages.patch` `f367b2d401193365f5c95628358346859ac33aa3222eb32fccd0f69826c30915`. All relevant hunks applied at exact context with zero offset to the inspected orig members. Derived final `src/options.c` SHA-256 `1824c933e413c5518d018b8d308bc5e49153fbbe59487a68a0545304c9dc26db`; `src/options.h` `b56725e62ba42b94d4789be3572721c16cbf6f0c0def9a229ca48b542ee11476`. This is an explicitly derived post-series source, not a separately downloaded file. `src/mystring.h` defines equality using `strcmp` (member SHA-256 `86d83aeaa8feb716adbf99e737532e8580f21a8220c925810b74654a060ac861`).
| Upstream dash | `v0.5.13.5`, [`options.c`](https://kernel.googlesource.com/pub/scm/utils/dash/dash/+/refs/tags/v0.5.13.5/src/options.c), SHA-256 `267289ec56fa51d6a21ec4b0eb91b1ebae66e9310007670d8eb6eef65b08fff4`; this source has 18 names and is a distinct edition.
| zsh | `5.9`, [`Src/init.c`](https://raw.githubusercontent.com/zsh-users/zsh/zsh-5.9/Src/init.c), SHA-256 `cdbe96fe80e4c56af6101d2837ef1bdaab7f1aa79f0d61206081c82395e4ce12`; [`Src/options.c`](https://raw.githubusercontent.com/zsh-users/zsh/zsh-5.9/Src/options.c), SHA-256 `d3c5d5095922f5b42087e37512b6ae966b70dd32bc84926bd4a65d388cc85de0`. Preserve source signs and variant-specific native/sh/ksh mappings.

## Deferred phase 1b evidence

After 1a publication, phase 1b records 42 PowerShell `MatchSwitch` name/prefix descriptors and the 80 cases; it must first promote the complete case and PowerShell contract. Use dated immutable docs, not an inferred Windows PowerShell parser: 5.1 `about_PowerShell_exe` commit `f09ce0b678c2da1ae0fa70f0b4789a607183cc63` (ms.date `2024-07-23`, updated `2025-09-29`) says `-Version` takes one value; pwsh 7.5 `about_Pwsh` commit `9fc54e7fc4954f7b4af134def74ba8e8cac7e23c` (ms.date `2026-01-18`, updated `2026-04-08`) says `-Version` displays version and ignores trailing parameters.

The two recorded pwsh 7.6 parser hashes `a7fc6b5c391bb8cbd06b78edd6e3b9867f3b89c1e634a610e7eddc7086a49783` and `abf566b2768f65586cab9e77cb0330fb8926950c9e7720b46f0fc0a69ebed6fe` remain discrepant. Preserve both with their provenance; neither establishes Windows PowerShell 5.1 behavior.

## Sequential completion and verification

Phase 1a passes when all 394 Unix rows/variants have primary provenance, oracle completeness and compatibility tests pass on Windows and Linux, and catalog/generation/harness checks pass with derived output uncommitted. Use `python` on Windows and `python3` on Linux/macOS. Exercise counts, stable IDs, fixed group contracts, source editions/member URLs and hashes, Bash conditional/vendor variants, exact dash `privileged` (no `priv` alias), zsh names/signed maps, malformed records, and supported raw-command/`-c` facade behavior. No 1a fixture or test may fetch sources; source tests do not establish native activation.

The SO01/SO02/SO03 remediation keeps the four established fixture/test paths plus this Goal as one frozen review slice. It passed captured oracle-r4 plus prior credential, catalog, harness, and generated-output checks. Parent approved the bounded exception above the 1,000-line trigger; do not add 1b data or compress records. Parent reviews before any PR; do not push or open a PR before parent review.

After 1a normal merge and causal publication, phase 1b owns PowerShell profiles and the 80-case oracle but no parser changes. After 1b publication, phase 2 atomically updates `.agents/hooks/git_auth_scope_gate.py` and its tests plus `test_delivery_binding_gate.py`, `test_merge_cleanup_gate.py`, and new `test_shell_command_operands.py`; run all cases against the public facade, preserve `str`/`None`/`SystemExit(2)`, and qualify credential/body/cleanup consumers. Keep the accepted algorithm and `7e8` checkpoint. Native wiring follows phase 2 review, exact-head Windows/Linux/guard CI, normal merge and causal publication.

The final base-to-working candidate measures 1,010 additions, above the 1,000-line trigger under the parent-approved frozen-scope exception: the 394-row fixture, fixed source data, helper contract, regressions, and Goal remain one atomic review slice.

## Both-host source coverage

```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/tests/fixtures/shell_profile_oracle.py and its Unix fixtures/self-tests",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Validate the complete offline Unix profile oracle while retaining established old-facade compatibility behavior.",
      "source": ".agents/hooks/tests/fixtures/shell_option_profiles.json, shell_profile_sources.json, shell_profile_oracle.py, and .agents/hooks/tests/test_shell_profile_oracle.py.",
      "mapping": "Existing .agents/plugins/harness/engineering.json maps shared consumers for Claude; preserve its package closure.",
      "verification": {"level": "source", "result": "limited", "evidence": "Committed SO01/SO02 source head 9add4e22eece41c3c48b60847ac64f3f2ced820d preserves the offline oracle and facade compatibility checks. SO03 captured oracle-r4 passing 7 tests with all 394 rows, IDs, and 35 guard conditions; Windows/Linux exact-head CI and installed native profiles remain unverified."},
      "exception": {"constraint_evidence": "Source tests only; exact-head Linux CI and installed native profiles were not run.", "supported_other_host_outcome": "Both hosts share the offline oracle and unchanged consumers; neither normal profile is claimed active."}
    },
    {
      "host": "codex",
      "behavior": "Validate the complete offline Unix profile oracle while retaining established old-facade compatibility behavior.",
      "source": ".agents/hooks/tests/fixtures/shell_option_profiles.json, shell_profile_sources.json, shell_profile_oracle.py, and .agents/hooks/tests/test_shell_profile_oracle.py.",
      "mapping": "Existing .agents/plugins/harness/engineering.json maps shared consumers for Codex; preserve its package closure.",
      "verification": {"level": "source", "result": "limited", "evidence": "Committed SO01/SO02 source head 9add4e22eece41c3c48b60847ac64f3f2ced820d preserves the offline oracle and facade compatibility checks. SO03 captured oracle-r4 passing 7 tests with all 394 rows, IDs, and 35 guard conditions; Windows/Linux exact-head CI and installed native profiles remain unverified."},
      "exception": {"constraint_evidence": "Source tests only; exact-head Linux CI and installed native profiles were not run.", "supported_other_host_outcome": "Both hosts share the offline oracle and unchanged consumers; neither normal profile is claimed active."}
    }
  ]
}
```

## Execution readiness

Verdict: SO03 remediation is ready for parent inspection and fresh incremental review. Linux exact-head CI and native activation remain pending.

## Next Steps

Parent inspects the SO01/SO02 remediation, commits the fixture/test slice, and runs fresh incremental review before exact-head CI, normal merge, and causal publication. Linux CI and native activation remain pending. Phase 1b may begin only after normal merge and causal publication; phase 2 remains blocked until phase 1b is also published. The parent retains the full rollout and all delivery decisions.
