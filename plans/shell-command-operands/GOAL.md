# Offline shell-profile and operand oracle

## Outcome and authority

Publish an offline, test-only oracle for the complete shell grammar before changing the production extractor. Phase 1a is delivered. Phase 1b preserves all 394 Unix rows, adds 42 ordered PowerShell descriptors (436 profile rows), and publishes all 80 fixed operand cases: 33 literal, 24 nonliteral and 23 refusal. Production extraction, shared consumers and native wiring follow only after all oracle slices have merged and published.

The existing parent rollout authorizes Claude and Codex source implementation, review, exact-head CI, normal merge and causal generated publication. It does not authorize profile installation, billing/protection bypass, credential changes or unrelated checkout cleanup. The parent retains review synthesis, commits and delivery decisions. Do not create a second goal or stack these slices.

## Published predecessor and current owner

Phase 1a Source head `261fb009177c558b2a48b8badd3e4a3da3385a4d` landed in Core PR #211 at merge `f25427e678dc1ab384260ffc97ddab4af69dbea5` on 2026-10-12 at 01:27:18 UTC. Exact PR CI `38190837766`, attempt 1, and causal main CI `38191948327`, attempt 1, completed successfully with guard/Windows/Linux as applicable. The causal regenerate log says “Generated output already current.” The merged checkout and its local branch were removed after cleanup proof. This is source publication; installed native activation is not claimed.

This successor is branch `Fix/PowerShellShellOracle`, based on published main `7fed153b078c60fa69b6db4b50ab03c0b3f5d025`. The canonical goal remains `plans/shell-command-operands/GOAL.md` in the active delivery checkout. The parent owns this document. The bounded L4 implementation writer completed and released the four existing fixture/helper/test paths listed below; the parent now owns acceptance and delivery. Preserve original checkpoint `7e8b650f721b3c872446f9205922efe685be81b1` and preserved generated/source stashes; never apply or remove them as part of this slice.

## Four sequential deliveries

The readable combined phase projects above the 1,000 substantive-addition trigger. The parent accepts four coherent deliveries, with no coverage reduction and no inherited phase 1a size exception. Measure actual substantive additions/deletions separately from maintained Goal documentation before review; reassess an oversized slice before growing it.

| Slice | Change | Published cases | Required predecessor | Projected substantive additions |
|---|---|---:|---|---:|
| 1b.1 | 42 descriptors, three provenance records, offline validation and meaningful malformed tests | 0 | Published 1a | 715–805 |
| 1b.2 | Fixed literal records and literal oracle validation | 33 | Published 1b.1 | 745–800 |
| 1b.3 | Fixed nonliteral records and boundary validation | 57 | Published 1b.2 | 409–444 |
| 1b.4 | Fixed refusal records and supplementary dash unknown-name regression | 80 | Published 1b.3 | 492–532 |

Publish in this order from the updated remote default branch. Do not start a successor's source changes before its predecessor's normal merge and causal publication. Metadata describes authored corpus coverage; runtime behavior must not depend on the test slice. Preserve previously published record IDs and semantics. No skipped, expected-failure, environment/head-selected or masked cases. All 80 cases and 42 descriptors remain mandatory before phase 2.

## Current 1b.1 lease and acceptance

Own only `.agents/hooks/tests/fixtures/shell_option_profiles.json`, `.agents/hooks/tests/fixtures/shell_profile_sources.json`, `.agents/hooks/tests/fixtures/shell_profile_oracle.py` and `.agents/hooks/tests/test_shell_profile_oracle.py`. Preserve all 11 Unix groups, nine existing provenance records, existing stable IDs and compatibility test class. Append the PowerShell data below and three primary provenance records. Total profile rows become 436: Bash 105, dash 19, zsh names 197, zsh signed maps 73 and PowerShell 42.

Implement standard-library offline validation and iteration with `pwsh:<name>` IDs, first ordered prefix resolution, explicit aliases, source conditions, Windows common projection/extra/Version override and fixed enums. Add meaningful malformed-copy tests: missing/reordered descriptors, lost or incorrect source conditions/aliases, bad arity/action, wrong source locations/provenance, removed raw/normalized hash distinction, missing immutable documentation metadata and falsely asserted parser revision. Existing facade compatibility covers only already published behavior. Do not add future extractor assertions to that compatibility class.

Do not create `shell_extraction_cases.json` in 1b.1. Do not edit production parser, consumers, native wiring, manifests, catalog, generated packages or either host mapping. The fixture/helper must not fetch sources, import the production gate as a second parser, decode encoded payloads, execute commands or read private host artifacts. Capture focused tests through the workflow run operation; run required source/generation/catalog/harness checks and exact-head Windows/Linux CI. Parent reviews the committed exact candidate before opening its PR.

## Ordered PowerShell fixture contract

The following data is fixed source union inspection, including platform/DEBUG branches; it does not prove installed platform availability. Windows PowerShell 5.1 common prefix handling is a source/docs-grounded compatibility inference, not a claim that the pwsh 7.6 parser implements Windows 5.1. Keep alias rows in source order and choose the first eligible case-insensitive match. Eligibility requires supplied length at least the minimum-prefix length and descriptor name beginning with the supplied name. Enumerate all minimum-to-full prefixes and alias precedence; a shorter token may match another earlier family, so do not blanket-refuse it.

```json
{
  "source": "pwsh-7.6.0-parser",
  "descriptors": [
    {
      "name": "version",
      "minimum_prefix": "v",
      "arity": 0,
      "action": "exit"
    },
    {
      "name": "help",
      "minimum_prefix": "h",
      "arity": 0,
      "action": "exit"
    },
    {
      "name": "?",
      "minimum_prefix": "?",
      "arity": 0,
      "action": "exit"
    },
    {
      "name": "login",
      "minimum_prefix": "l",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "noexit",
      "minimum_prefix": "noe",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "noprofile",
      "minimum_prefix": "nop",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "nologo",
      "minimum_prefix": "nol",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "noninteractive",
      "minimum_prefix": "noni",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "socketservermode",
      "minimum_prefix": "so",
      "arity": 0,
      "action": "opaque"
    },
    {
      "name": "v2socketservermode",
      "minimum_prefix": "v2so",
      "arity": 0,
      "action": "opaque"
    },
    {
      "name": "servermode",
      "minimum_prefix": "s",
      "arity": 0,
      "action": "opaque"
    },
    {
      "name": "namedpipeservermode",
      "minimum_prefix": "nam",
      "arity": 0,
      "action": "opaque"
    },
    {
      "name": "sshservermode",
      "minimum_prefix": "sshs",
      "arity": 0,
      "action": "opaque"
    },
    {
      "name": "noprofileloadtime",
      "minimum_prefix": "noprofileloadtime",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "interactive",
      "minimum_prefix": "i",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "configurationfile",
      "minimum_prefix": "configurationfile",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "configurationname",
      "minimum_prefix": "config",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "custompipename",
      "minimum_prefix": "cus",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "commandwithargs",
      "minimum_prefix": "commandwithargs",
      "arity": 1,
      "action": "cwa"
    },
    {
      "name": "cwa",
      "minimum_prefix": "cwa",
      "arity": 1,
      "action": "cwa"
    },
    {
      "name": "command",
      "minimum_prefix": "c",
      "arity": "remainder",
      "action": "command"
    },
    {
      "name": "windowstyle",
      "minimum_prefix": "w",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "file",
      "minimum_prefix": "f",
      "arity": 1,
      "action": "file"
    },
    {
      "name": "isswait",
      "minimum_prefix": "isswait",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "outputformat",
      "minimum_prefix": "o",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "of",
      "minimum_prefix": "o",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "inputformat",
      "minimum_prefix": "inp",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "if",
      "minimum_prefix": "if",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "executionpolicy",
      "minimum_prefix": "ex",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "ep",
      "minimum_prefix": "ep",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "encodedcommand",
      "minimum_prefix": "e",
      "arity": 1,
      "action": "opaque"
    },
    {
      "name": "ec",
      "minimum_prefix": "e",
      "arity": 1,
      "action": "opaque"
    },
    {
      "name": "encodedarguments",
      "minimum_prefix": "encodeda",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "ea",
      "minimum_prefix": "ea",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "settingsfile",
      "minimum_prefix": "settings",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "sta",
      "minimum_prefix": "sta",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "mta",
      "minimum_prefix": "mta",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "workingdirectory",
      "minimum_prefix": "wo",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "wd",
      "minimum_prefix": "wd",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "removeworkingdirectorytrailingcharacter",
      "minimum_prefix": "removeworkingdirectorytrailingcharacter",
      "arity": 0,
      "action": "continue"
    },
    {
      "name": "token",
      "minimum_prefix": "to",
      "arity": 1,
      "action": "continue"
    },
    {
      "name": "utctimestamp",
      "minimum_prefix": "utc",
      "arity": 1,
      "action": "continue"
    }
  ],
  "aliases": {
    "?": "help",
    "cwa": "commandwithargs",
    "of": "outputformat",
    "if": "inputformat",
    "ep": "executionpolicy",
    "ec": "encodedcommand",
    "ea": "encodedarguments",
    "wd": "workingdirectory"
  },
  "source_lines": {
    "version": 901,
    "help": 912,
    "?": 912,
    "login": 919,
    "noexit": 925,
    "noprofile": 931,
    "nologo": 936,
    "noninteractive": 941,
    "socketservermode": 946,
    "v2socketservermode": 953,
    "servermode": 960,
    "namedpipeservermode": 966,
    "sshservermode": 972,
    "noprofileloadtime": 978,
    "interactive": 983,
    "configurationfile": 988,
    "configurationname": 1001,
    "custompipename": 1014,
    "commandwithargs": 1041,
    "cwa": 1041,
    "command": 1054,
    "windowstyle": 1063,
    "file": 1092,
    "isswait": 1102,
    "outputformat": 1107,
    "of": 1107,
    "inputformat": 1113,
    "if": 1113,
    "executionpolicy": 1118,
    "ep": 1118,
    "encodedcommand": 1133,
    "ec": 1133,
    "encodedarguments": 1143,
    "ea": 1143,
    "settingsfile": 1152,
    "sta": 1162,
    "mta": 1182,
    "workingdirectory": 1202,
    "wd": 1202,
    "removeworkingdirectorytrailingcharacter": 1216,
    "token": 1220,
    "utctimestamp": 1235
  },
  "conditions": {
    "v2socketservermode": [
      "!UNIX"
    ],
    "isswait": [
      "DEBUG"
    ],
    "removeworkingdirectorytrailingcharacter": [
      "!UNIX"
    ],
    "token": [
      "!UNIX"
    ],
    "utctimestamp": [
      "!UNIX"
    ]
  },
  "windows_common_names": [
    "help",
    "?",
    "noexit",
    "noprofile",
    "nologo",
    "noninteractive",
    "configurationname",
    "command",
    "windowstyle",
    "file",
    "outputformat",
    "of",
    "inputformat",
    "if",
    "executionpolicy",
    "ep",
    "encodedcommand",
    "ec",
    "encodedarguments",
    "ea",
    "sta",
    "mta"
  ],
  "windows_extra": [
    {
      "name": "psconsolefile",
      "minimum_prefix": "psconsolefile",
      "arity": 1,
      "action": "continue",
      "source": "windows-powershell-5.1-cli-doc"
    }
  ],
  "windows_overrides": {
    "version": {
      "minimum_prefix": "v",
      "arity": 1,
      "action": "continue",
      "source": "windows-powershell-5.1-cli-doc"
    }
  },
  "enums": {
    "executionpolicy": [
      "default",
      "remotesigned",
      "bypass",
      "allsigned",
      "restricted",
      "unrestricted",
      "undefined"
    ],
    "inputformat": [
      "text",
      "xml"
    ],
    "outputformat": [
      "text",
      "xml"
    ],
    "windowstyle": [
      "normal",
      "minimized",
      "maximized",
      "hidden"
    ]
  }
}
```

## PowerShell semantic boundaries

### matching

After supported introducer/trim normalization, match supplied name length>=minimum_prefix length and descriptor name startswith supplied name case-insensitively. Choose first source-ordered match; retain aliases as distinct rows with canonical action/enum targets.

### prefix validation

Enumerate every minimum-through-full prefix for each42 and resolve first matching row using data operations only. Alias of with minimum o can resolve earlier outputformat; ec minimum e resolves earlier encodedcommand. A just-shorter string may match another family; assert its correct first match or unsupported, never blanket refusal. Exact-only names do not admit shorter form.

### windows profile

Ordered projection of accepted common names, plus documented psconsolefile and replacement Version/v value arity1/continue. CWA and pwsh-only descriptors unsupported for Windows. Common prefix inference remains separate from5.1 documented facts.

### enum policy

Known enum strings case-insensitive; aliases inherit canonical enum. Value arity is one even for flag-looking values; unknown enum refuses. External file/version/endpoint/token validity and platform availability are not extraction authority.

### boundaries

```json
{
  "arity": "Every known value option consumes one following argv even when it is -Command/-c. Missing operand reject. Do not validate external files/versions/endpoints/token values or OS availability. Unknown enum values are indeterminate; known source enum values can continue. Do not decode EncodedArguments; consume only its one operand.",
  "modeBoundary": "Explicit File/f owns remaining argv immediately (file or '-' stdin); no later Command/CWA is a launcher switch. pwsh's first genuine nonoption operand defaults to File. Windows powershell's first genuine nonoption expression defaults to Command and returns the joined expression without rescanning later words. A failed switch match is indeterminate, never a default File guess when version is unpinned.",
  "commandBoundary": "Explicit Command c through command returns joined remainder. CWA is pwsh exact commandwithargs or cwa and returns next argv alone; all following words are arguments, including unknown switches. Missing actual command operand reject; first '-' stdin. Windows CWA is unsupported -> indeterminate rather than imaginary support.",
  "exitOpaqueBoundary": "Known help, pwsh Version, encoded-command and established server execution mode provide no direct literal in this scope. Do not inspect/decode their payloads. Windows Version/v consumes one operand then continues toward Command, preserving e.g. -Version 5.1 -Command SCRIPT.",
  "conditionalSource": "token/utctimestamp/removeWorkingDirectoryTrailingCharacter/v2socketservermode are source Windows-build branches; isswait is DEBUG. Keep explicit source-known same-arity family coverage rather than pretending release/platform absence proves no execution. All are version/platform union inspection, not activation claims.",
  "windowEvidenceLimit": "Windows PowerShell common prefix support is source/docs-grounded compatibility inference plus earlier successful /c native probe; fresh exact Windows-Version activation not claimed. Tests must extract its documented operand correctly regardless of installed version availability."
}
```

### normalization limit

All80 require only accepted ASCII minus/slash and pwsh second identical dash. Optional Unicode dash set is delegated to CharExtensions.IsDash, whose definition was not read; phase2 must inspect its primary source if implementing it. No1b descriptor/case blocker.

## Primary source evidence retained from published 1a


These hashes identify bytes actually inspected; no archive signature, tag-to-archive cryptographic authentication, or installed-package equivalence is claimed. Source recovery used the immutable references and cached bytes below. The source fixtures/tests must not fetch sources at runtime or in CI.

| Profile and source | Edition, immutable URL, and inspected bytes |
|---|---|
| GNU Bash | `5.2.37`, canonical [`ftp.gnu.org` archive](https://ftp.gnu.org/gnu/bash/bash-5.2.37.tar.gz); retrieved from [`ibiblio mirror`](https://mirrors.ibiblio.org/pub/mirrors/gnu/bash/bash-5.2.37.tar.gz). Archive SHA-256 `9599b22ecd1d5787ad7d3b7bf0c59f312b3396d1e281175dd1f8a4014da621ff`. Members: `builtins/shopt.def` `c1bb281be9ac815fce0ab20022689d8ca8702e63c0de2cae94ebc9b4e812d91d`; `shell.c` `69a6622c9460b228632cf4deb57233e59159f2bac8a600baa3c1f72635fbeff0`; `flags.c` `62b377da2431b15843a4d13a2814b387eb95bed789e2a0c618efce7c1646719f`; `builtins/set.def` `60cc498e28d4e9edd49a1415f1b5f92cfd326c6cb0d17d0d0827757f23580793`; `patchlevel.h` `fa3955e6c42bf4a8a1ab6077ea96991c95bb1024a86768eea4c733010112ed15` (PATCHLEVEL 37). `shopt.def` row `syslog_history` is conditional on `SYSLOG_HISTORY && SYSLOG_SHOPT`.
| Git-for-Windows/MSYS Bash variant | Immutable [`MSYS2-packages` PKGBUILD](https://raw.githubusercontent.com/git-for-windows/MSYS2-packages/39014c49183d3635c93151c390604318d2655da1/bash/PKGBUILD), revision `39014c49183d3635c93151c390604318d2655da1`, SHA-256 `b2aeaff6799073b992b716efd1da2753198ca099dee9de05315ceca431f7ad50`; [`Cygwin patch`](https://raw.githubusercontent.com/git-for-windows/MSYS2-packages/39014c49183d3635c93151c390604318d2655da1/bash/0001-bash-4.4-cygwin.patch), SHA-256 `81f5fcb0990199e555f78ecf57dd6874d4b0ca781d4e7d26eac5a76ba729ac59`. PKGBUILD declares base `5.3`, patchlevel `015`; `completion_strip_exe` is `shopt/O` and `igncr` is `set/o`, both under `__CYGWIN__`. This is a separate pinned vendor variant, not evidence of installed 5.2.37 package contents.
| Debian dash package | `.dsc` at [`ftp.debian.org`](https://ftp.debian.org/debian/pool/main/d/dash/dash_0.5.12-2.dsc), version `0.5.12-2`, SHA-256 `25c0fb805c735fdb7470ce485ce76dae1a7b6c04efdfb0fdac5eab921cbd78a5`; orig archive [`dash_0.5.12.orig.tar.gz`](https://ftp.debian.org/debian/pool/main/d/dash/dash_0.5.12.orig.tar.gz), SHA-256 `6a474ac46e8b0b32916c4c60df694c82058d3297d8b385b74508030ca4a8f28a`; Debian patch archive [`dash_0.5.12-2.debian.tar.xz`](https://ftp.debian.org/debian/pool/main/d/dash/dash_0.5.12-2.debian.tar.xz), SHA-256 `bddd9129215eb60f4cc43a0ffdcc42d8f25e0bd09730520d599a2b7bc492e375`. The inspected `.dsc` declares archive sizes/hashes matching these bytes; its included PGP signature was not verified. Raw orig members `src/options.h` SHA-256 `12f632ce480f03ccbe67e640c2ea24b7de713033015d52336a6d8c8845d32132`, `src/options.c` `0a883024ad3a298071a6269a13901a975b0be9954c576326c8fad75e94c91855`. Debian `series` SHA-256 `1e0f7009609809bbe00204190e41788cf12a4e293d3f7fe6ee8206983adac9bf`; relevant patches `9001-Add-privmode-Part-1.diff` `be5aaf6df52edd49fd54c0978c964b4d0da59eb1d6c712de6a07063c276e6b66`, `9002-Add-privmode-Part-2.diff` `5ca803204938bc6710c88b425ea3c8b024ff0eca3e725246cb4f904eba86da7e`, and the series-listed `0020-Update-manpages.patch` `f367b2d401193365f5c95628358346859ac33aa3222eb32fccd0f69826c30915`. All relevant hunks applied at exact context with zero offset to the inspected orig members. Derived final `src/options.c` SHA-256 `1824c933e413c5518d018b8d308bc5e49153fbbe59487a68a0545304c9dc26db`; `src/options.h` `b56725e62ba42b94d4789be3572721c16cbf6f0c0def9a229ca48b542ee11476`. This is an explicitly derived post-series source, not a separately downloaded file. `src/mystring.h` defines equality using `strcmp` (member SHA-256 `86d83aeaa8feb716adbf99e737532e8580f21a8220c925810b74654a060ac861`).
| Upstream dash | `v0.5.13.5`, [`options.c`](https://kernel.googlesource.com/pub/scm/utils/dash/dash/+/refs/tags/v0.5.13.5/src/options.c), SHA-256 `267289ec56fa51d6a21ec4b0eb91b1ebae66e9310007670d8eb6eef65b08fff4`; this source has 18 names and is a distinct edition.
| zsh | `5.9`, [`Src/init.c`](https://raw.githubusercontent.com/zsh-users/zsh/zsh-5.9/Src/init.c), SHA-256 `cdbe96fe80e4c56af6101d2837ef1bdaab7f1aa79f0d61206081c82395e4ce12`; [`Src/options.c`](https://raw.githubusercontent.com/zsh-users/zsh/zsh-5.9/Src/options.c), SHA-256 `d3c5d5095922f5b42087e37512b6ae966b70dd32bc84926bd4a65d388cc85de0`. Preserve source signs and variant-specific native/sh/ksh mappings.


## Additional fixed PowerShell provenance

The three records below preserve the actual inspected bytes and evidence limits. The two pwsh parser hashes reconcile as raw CRLF bytes and normalized LF bytes; no new fetch, verified tag-to-commit resolution or Windows 5.1 parser equivalence is claimed.

```json
{
  "pwsh-7.6.0-parser": {
    "edition": "v7.6.0",
    "url": "https://raw.githubusercontent.com/PowerShell/PowerShell/v7.6.0/src/Microsoft.PowerShell.ConsoleHost/host/msh/CommandLineParameterParser.cs",
    "member": "src/Microsoft.PowerShell.ConsoleHost/host/msh/CommandLineParameterParser.cs",
    "sha256": "a7fc6b5c391bb8cbd06b78edd6e3b9867f3b89c1e634a610e7eddc7086a49783",
    "byte_form": "UTF-8 no BOM; existing CRLF cache",
    "normalized_lf_sha256": "abf566b2768f65586cab9e77cb0330fb8926950c9e7720b46f0fc0a69ebed6fe",
    "resolved_commit": null,
    "provenance": "Existing attributed cache, v7.6.0 tag not resolved/verified; no5.1 parser equivalence.",
    "locations": {
      "normalization": [
        709,
        737
      ],
      "matching": [
        797,
        805
      ],
      "descriptors": [
        901,
        1246
      ],
      "policy_enum": [
        756,
        792
      ],
      "format_enum": [
        1293,
        1325
      ],
      "file": [
        1344,
        1435
      ],
      "command": [
        1493,
        1554
      ]
    }
  },
  "windows-powershell-5.1-cli-doc": {
    "edition": "5.1",
    "url": "https://raw.githubusercontent.com/MicrosoftDocs/PowerShell-Docs/f09ce0b678c2da1ae0fa70f0b4789a607183cc63/reference/5.1/Microsoft.PowerShell.Core/About/about_PowerShell_exe.md",
    "member": "about_powershell_exe-5.1-f09ce0.md",
    "sha256": "cdbaa30b2186ebedf4c78e21c529f2691c2bedf105faa7ebe7f420c2b6b1e4da",
    "revision": "f09ce0b678c2da1ae0fa70f0b4789a607183cc63",
    "ms_date": "2024-07-23T00:00:00Z",
    "updated_at": "2025-09-29T22:08:00Z",
    "observed_utc": "2026-10-11T11:52:12.832991+00:00",
    "locations": [
      [
        25,
        267,
        269,
        270,
        271,
        272
      ],
      [
        112,
        148
      ],
      [
        193,
        218
      ],
      [
        219,
        253
      ],
      [
        255,
        259
      ],
      [
        275,
        290
      ]
    ]
  },
  "pwsh-7.5-cli-doc": {
    "edition": "7.5",
    "url": "https://raw.githubusercontent.com/MicrosoftDocs/PowerShell-Docs/9fc54e7fc4954f7b4af134def74ba8e8cac7e23c/reference/7.5/Microsoft.PowerShell.Core/About/about_Pwsh.md",
    "member": "about_pwsh-7.5-9fc54e.md",
    "sha256": "6237731762df03b74e9768c30a228d9f03ab6ba98c39b03d6635e7e237cc3bb2",
    "revision": "9fc54e7fc4954f7b4af134def74ba8e8cac7e23c",
    "ms_date": "2026-01-18T00:00:00Z",
    "updated_at": "2026-04-08T22:08:00Z",
    "observed_utc": "2026-10-11T11:52:12.838975+00:00",
    "locations": [
      [
        59,
        61,
        62,
        64,
        65,
        68,
        69,
        70
      ],
      [
        128,
        131,
        159,
        160,
        161
      ],
      [
        209,
        211,
        212,
        214,
        215,
        217,
        218
      ],
      [
        410,
        412,
        413
      ],
      [
        295,
        307
      ],
      [
        377,
        380
      ],
      [
        415,
        419
      ]
    ]
  }
}
```

## Full fixed operand-case contract

Assigned now once by original33 literal ->24 none ->23 refusal order; IDs did not preexist and do not encode corrected outcome.

Zero-based complete cleaned argv including executable at0. No80 input has discarded empty/non-string values. For literal boundary_index identifies boundary-setting switch; none identifies file/stdin operand, final understood token on reject or exit switch. option_index identifies unsupported active token/value.

The exact `SCRIPT` sentinel becomes the inert literal string `gh pr merge 1`; retain every other argument, including `gh pr merge 2`. These are data, never commands to execute. `operand_index` and `boundary_index` are zero-based in complete cleaned argv, with executable at index 0; none of these 80 inputs loses an empty/nonstring argument. Integer indices reject booleans. Literal text is exact; modes are `one_operand` or `joined_remainder`. A nonliteral input records file/stdin/exit/proved-reject kind. Unknown or ambiguous options produce typed refusal with option index, stable reason and exit status 2, never guessed text or `None`.


```json
{
  "public_outcomes": {
    "literal": "str exactly expected.text",
    "none": "None with established file/stdin/exit/reject kind",
    "refusal": "SystemExit(2), stable diagnostic and no command text; never None/guessed string"
  },
  "corrections": [
    {
      "id": "shell-case-011",
      "matrix": "literalMatrix",
      "matrix_ordinal": 11,
      "argv_retained": true,
      "old_outcome": "literal",
      "new_outcome": "refusal",
      "justification": "Exact privileged name/strcmp; priv is not an alias."
    },
    {
      "id": "shell-case-068",
      "matrix": "refusalMatrix",
      "matrix_ordinal": 11,
      "old_argv": [
        "dash",
        "-o",
        "future_option",
        "-c",
        "SCRIPT"
      ],
      "new_argv": [
        "dash",
        "-o",
        "privileged",
        "-c",
        "gh pr merge 1"
      ],
      "old_outcome": "refusal",
      "new_outcome": "literal",
      "justification": "Exact source-known privileged; c script index4."
    }
  ],
  "source_rules": {
    "bash-grammar": {
      "sources": [
        "gnu-bash-5.2.37-shell",
        "gnu-bash-5.2.37-flags",
        "gnu-bash-5.2.37-set",
        "gnu-bash-5.2.37-shopt"
      ],
      "location": "shell.c parse_long_options/parse_shell_options; flags.c; set.def o_options; shopt.def"
    },
    "dash-grammar": {
      "sources": [
        "dash-0.5.13.5-options",
        "debian-dash-0.5.12-2"
      ],
      "location": "options/processargs; exact optnames; Debian privileged and mystring strcmp"
    },
    "zsh-grammar": {
      "sources": [
        "zsh-5.9-init",
        "zsh-5.9-options"
      ],
      "location": "parseopts; optlookupc/optlookup/emulate; signed native/sh/ksh maps"
    },
    "sh-reduction": {
      "sources": [
        "gnu-bash-5.2.37-shell",
        "dash-0.5.13.5-options",
        "debian-dash-0.5.12-2",
        "zsh-5.9-init",
        "zsh-5.9-options"
      ],
      "location": "accepted declared-family reduction plus each primary option grammar"
    },
    "pwsh-grammar": {
      "sources": [
        "pwsh-7.6.0-parser",
        "pwsh-7.5-cli-doc"
      ],
      "location": "ordered MatchSwitch/GetSwitchKey/ParseCommand/ParseFile and dated CLI documentation"
    },
    "windows-grammar": {
      "sources": [
        "windows-powershell-5.1-cli-doc",
        "pwsh-7.6.0-parser"
      ],
      "location": "documented5.1 File/Command/Version; common prefixes only accepted compatibility inference"
    }
  },
  "case_semantics": {
    "shell-case-001": "Plus always starts short groups; +help is h/e/l/p, not help exit.",
    "shell-case-002": "Plus ordinary e permits later c.",
    "shell-case-003": "c persists while subsequent e remains active.",
    "shell-case-004": "After c/-- select one script; trailing operands are positional.",
    "shell-case-005": "Group o consumes separate posix, then c selects script.",
    "shell-case-006": "Group O consumes separate extglob, then c selects script.",
    "shell-case-007": "Each o consumes its successive separate name; finish e/c.",
    "shell-case-008": "rcfile consumes -c as value; later actual -c requests command.",
    "shell-case-009": "noexec does not suppress literal inspection.",
    "shell-case-010": "Debian p is nonconsuming in the declared family.",
    "shell-case-011": "Debian name exactly privileged and strcmp prove no priv alias/prefix; unknown named value refuses.",
    "shell-case-012": "Uppercase I is an ordinary dash letter.",
    "shell-case-013": "Plus o consumes separate errexit, retaining c.",
    "shell-case-014": "c persists while subsequent e remains active.",
    "shell-case-015": "Long no-rcs translates hyphens before named lookup.",
    "shell-case-016": "Native b marks break but finishes c/b group; tail is positional.",
    "shell-case-017": "Native O is a signed mapping, then c selects script.",
    "shell-case-018": "Attached o errexit ends group; persistent c selects script.",
    "shell-case-019": "Long sh-word-split uses long-only hyphen normalization.",
    "shell-case-020": "sh-option-letters enables ksh letters; b is NOTIFY.",
    "shell-case-021": "e initializes sh before b; b is NOTIFY and later c active.",
    "shell-case-022": "Before initialization b marks break but same-group c still processed.",
    "shell-case-023": "All sh profiles agree on index after source-known p.",
    "shell-case-024": "All sh profiles agree after c/--, ignoring positional tails.",
    "shell-case-025": "Intermediate NoProf and Com satisfy minimum-prefix rules.",
    "shell-case-026": "ExecutionPol consumes case-insensitive known Bypass.",
    "shell-case-027": "Slash accepts known PowerShell descriptor prefixes.",
    "shell-case-028": "pwsh removes second identical dash.",
    "shell-case-029": "Windows common prefix support is accepted compatibility inference.",
    "shell-case-030": "Windows Version takes one value and continues.",
    "shell-case-031": "Windows slash V takes value, slash C owns remainder.",
    "shell-case-032": "WorkingDir consumes -c as value; later Command selects script.",
    "shell-case-033": "Exact CWA selects only next operand, ignoring argument tail.",
    "shell-case-034": "Initial --help exits before later c.",
    "shell-case-035": "Initial -help exits before later c.",
    "shell-case-036": "Without c, -- ends options; -c is file.",
    "shell-case-037": "File owns later argv.",
    "shell-case-038": "Known c lacks script.",
    "shell-case-039": "Known c lacks script after --.",
    "shell-case-040": "Known rcfile lacks value.",
    "shell-case-041": "File owns later c.",
    "shell-case-042": "Known c lacks script.",
    "shell-case-043": "Exact zsh help exits.",
    "shell-case-044": "Before sh initialization b sees false SHOPTIONLETTERS and breaks; -c is file.",
    "shell-case-045": "no-sh-option-letters makes b break; -c is file.",
    "shell-case-046": "Known c lacks script.",
    "shell-case-047": "All sh profiles establish file.",
    "shell-case-048": "All sh profiles prove missing script.",
    "shell-case-049": "Explicit File owns all tail.",
    "shell-case-050": "Explicit File owns all tail.",
    "shell-case-051": "pwsh first nonoption defaults File.",
    "shell-case-052": "WorkingDir consumes value; next nonoption File.",
    "shell-case-053": "pwsh Version exits, ignoring tail.",
    "shell-case-054": "Command operand - reads stdin.",
    "shell-case-055": "CWA lacks operand.",
    "shell-case-056": "Windows Version lacks value.",
    "shell-case-057": "ExecutionPol lacks value.",
    "shell-case-058": "Unknown active long option.",
    "shell-case-059": "Unknown short letter.",
    "shell-case-060": "c does not stop prefix before unknown Z.",
    "shell-case-061": "Unknown plus group.",
    "shell-case-062": "Unknown exact Bash o value.",
    "shell-case-063": "Unknown exact Bash O value.",
    "shell-case-064": "o consumes unknown -c value; never rescan.",
    "shell-case-065": "c does not stop prefix before unknown long option.",
    "shell-case-066": "Unknown dash q.",
    "shell-case-067": "Unknown dash long option.",
    "shell-case-068": "Exact source-known privileged continues to actual c script index4.",
    "shell-case-069": "Unknown zsh long name.",
    "shell-case-070": "Separate zsh o has no long hyphen rewrite.",
    "shell-case-071": "Unknown zsh o name.",
    "shell-case-072": "No guessed long NAME=value syntax.",
    "shell-case-073": "Bash index3 and zsh index2 disagree; dash unsupported r after consumed errexit is indeterminate, prioritized by reducer.",
    "shell-case-074": "zsh attached o works; Bash/dash consume -c as unsupported value.",
    "shell-case-075": "Any unresolved sh profile refuses.",
    "shell-case-076": "Unknown pwsh switch never defaults File.",
    "shell-case-077": "CWA/CommandWithArgs exact-only; CommandWithArg unsupported.",
    "shell-case-078": "Windows CWA unsupported extension.",
    "shell-case-079": "Unknown policy enum is indeterminate.",
    "shell-case-080": "Unknown Windows switch refuses before later File."
  }
}
```

The IDs below are assigned once in original matrix order; IDs do not encode the corrected outcome. `shell-case-011` retains exact dash `priv` and becomes refusal. `shell-case-068` uses exact `privileged`, has script index 4 and becomes literal. This source-backed correction preserves the full 33/24/23 partition.

| ID | Complete argv | Exact expected record | Source rule |
|---|---|---|---|

| shell-case-001 | `["bash", "+help", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-002 | `["bash", "+e", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-003 | `["bash", "-c", "-e", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-004 | `["bash", "-c", "--", "gh pr merge 1", "zero", "gh pr merge 2"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-005 | `["bash", "-oc", "posix", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-006 | `["bash", "-Oc", "extglob", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-007 | `["bash", "-ooec", "errexit", "nounset", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-008 | `["bash", "--rcfile", "-c", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "one_operand", "boundary_index": 3, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-009 | `["bash", "-n", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | bash-grammar |

| shell-case-010 | `["dash", "-p", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | dash-grammar |

| shell-case-011 | `["dash", "-o", "priv", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option-value", "exit_status": 2}` | dash-grammar |

| shell-case-012 | `["dash", "-cI", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 2, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | dash-grammar |

| shell-case-013 | `["dash", "+oc", "errexit", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | dash-grammar |

| shell-case-014 | `["dash", "-c", "-e", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | dash-grammar |

| shell-case-015 | `["zsh", "--no-rcs", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | zsh-grammar |

| shell-case-016 | `["zsh", "-cb", "gh pr merge 1", "-Command", "ARG"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 2, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | zsh-grammar |

| shell-case-017 | `["zsh", "-Oc", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 2, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | zsh-grammar |

| shell-case-018 | `["zsh", "-coerrexit", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 2, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | zsh-grammar |

| shell-case-019 | `["zsh", "--sh-word-split", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | zsh-grammar |

| shell-case-020 | `["zsh", "--sh-option-letters", "-b", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "one_operand", "boundary_index": 3, "text": "gh pr merge 1"}` | zsh-grammar |

| shell-case-021 | `["zsh", "--emulate", "sh", "-e", "-b", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 6, "remainder_mode": "one_operand", "boundary_index": 5, "text": "gh pr merge 1"}` | zsh-grammar |

| shell-case-022 | `["zsh", "--emulate", "sh", "-bc", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "one_operand", "boundary_index": 3, "text": "gh pr merge 1"}` | zsh-grammar |

| shell-case-023 | `["sh", "-p", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | sh-reduction |

| shell-case-024 | `["sh", "-c", "--", "gh pr merge 1", "zero", "-UnknownTrailing"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "one_operand", "boundary_index": 2, "text": "gh pr merge 1"}` | sh-reduction |

| shell-case-025 | `["pwsh", "-NoProf", "-Com", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "joined_remainder", "boundary_index": 2, "text": "gh pr merge 1"}` | pwsh-grammar |

| shell-case-026 | `["pwsh", "-ExecutionPol", "Bypass", "-Command", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "joined_remainder", "boundary_index": 3, "text": "gh pr merge 1"}` | pwsh-grammar |

| shell-case-027 | `["pwsh", "/NoProf", "/Com", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "joined_remainder", "boundary_index": 2, "text": "gh pr merge 1"}` | pwsh-grammar |

| shell-case-028 | `["pwsh", "--NoProf", "--Com", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "joined_remainder", "boundary_index": 2, "text": "gh pr merge 1"}` | pwsh-grammar |

| shell-case-029 | `["powershell", "-NoProf", "-Com", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 3, "remainder_mode": "joined_remainder", "boundary_index": 2, "text": "gh pr merge 1"}` | windows-grammar |

| shell-case-030 | `["powershell", "-Version", "5.1", "-Command", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "joined_remainder", "boundary_index": 3, "text": "gh pr merge 1"}` | windows-grammar |

| shell-case-031 | `["powershell", "/V", "5.1", "/C", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "joined_remainder", "boundary_index": 3, "text": "gh pr merge 1"}` | windows-grammar |

| shell-case-032 | `["pwsh", "-WorkingDir", "-c", "-Command", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "joined_remainder", "boundary_index": 3, "text": "gh pr merge 1"}` | pwsh-grammar |

| shell-case-033 | `["pwsh", "-CWA", "gh pr merge 1", "-FutureOption", "gh pr merge 2"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 2, "remainder_mode": "one_operand", "boundary_index": 1, "text": "gh pr merge 1"}` | pwsh-grammar |

| shell-case-034 | `["bash", "--help", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "exit", "boundary_index": 1}` | bash-grammar |

| shell-case-035 | `["bash", "-help", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "exit", "boundary_index": 1}` | bash-grammar |

| shell-case-036 | `["bash", "--", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 2}` | bash-grammar |

| shell-case-037 | `["bash", "script.sh", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 1}` | bash-grammar |

| shell-case-038 | `["bash", "-c"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 1}` | bash-grammar |

| shell-case-039 | `["bash", "-c", "--"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 2}` | bash-grammar |

| shell-case-040 | `["bash", "--rcfile"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 1}` | bash-grammar |

| shell-case-041 | `["dash", "script.sh", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 1}` | dash-grammar |

| shell-case-042 | `["dash", "-c"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 1}` | dash-grammar |

| shell-case-043 | `["zsh", "--help", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "exit", "boundary_index": 1}` | zsh-grammar |

| shell-case-044 | `["zsh", "--emulate", "sh", "-b", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 4}` | zsh-grammar |

| shell-case-045 | `["zsh", "--no-sh-option-letters", "-b", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 3}` | zsh-grammar |

| shell-case-046 | `["zsh", "-c"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 1}` | zsh-grammar |

| shell-case-047 | `["sh", "script.sh", "-c", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 1}` | sh-reduction |

| shell-case-048 | `["sh", "-c"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 1}` | sh-reduction |

| shell-case-049 | `["pwsh", "-File", "harmless.ps1", "-Command", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 2}` | pwsh-grammar |

| shell-case-050 | `["powershell", "-File", "harmless.ps1", "-Command", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 2}` | windows-grammar |

| shell-case-051 | `["pwsh", "harmless.ps1", "-Command", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 1}` | pwsh-grammar |

| shell-case-052 | `["pwsh", "-WorkingDir", "somewhere", "harmless.ps1", "-Command", "gh pr merge 1"]` | `{"outcome": "none", "kind": "file", "boundary_index": 3}` | pwsh-grammar |

| shell-case-053 | `["pwsh", "-Version", "-Command", "gh pr merge 1"]` | `{"outcome": "none", "kind": "exit", "boundary_index": 1}` | pwsh-grammar |

| shell-case-054 | `["pwsh", "-Command", "-"]` | `{"outcome": "none", "kind": "stdin", "boundary_index": 2}` | pwsh-grammar |

| shell-case-055 | `["pwsh", "-CWA"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 1}` | pwsh-grammar |

| shell-case-056 | `["powershell", "-Version"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 1}` | windows-grammar |

| shell-case-057 | `["pwsh", "-ExecutionPol"]` | `{"outcome": "none", "kind": "reject", "boundary_index": 1}` | pwsh-grammar |

| shell-case-058 | `["bash", "--future-vendor-option", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | bash-grammar |

| shell-case-059 | `["bash", "-Z", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | bash-grammar |

| shell-case-060 | `["bash", "-c", "-Z", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option", "exit_status": 2}` | bash-grammar |

| shell-case-061 | `["bash", "+future-vendor-option", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | bash-grammar |

| shell-case-062 | `["bash", "-o", "future_option", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option-value", "exit_status": 2}` | bash-grammar |

| shell-case-063 | `["bash", "-O", "future_shopt", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option-value", "exit_status": 2}` | bash-grammar |

| shell-case-064 | `["bash", "-o", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option-value", "exit_status": 2}` | bash-grammar |

| shell-case-065 | `["bash", "-c", "--future-option", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option", "exit_status": 2}` | bash-grammar |

| shell-case-066 | `["dash", "-q", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | dash-grammar |

| shell-case-067 | `["dash", "--future", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | dash-grammar |

| shell-case-068 | `["dash", "-o", "privileged", "-c", "gh pr merge 1"]` | `{"outcome": "literal", "kind": "literal", "operand_index": 4, "remainder_mode": "one_operand", "boundary_index": 3, "text": "gh pr merge 1"}` | dash-grammar |

| shell-case-069 | `["zsh", "--future-option", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | zsh-grammar |

| shell-case-070 | `["zsh", "-o", "sh-word-split", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option-value", "exit_status": 2}` | zsh-grammar |

| shell-case-071 | `["zsh", "-o", "future_option", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option-value", "exit_status": 2}` | zsh-grammar |

| shell-case-072 | `["zsh", "--future=value", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | zsh-grammar |

| shell-case-073 | `["sh", "-coerrexit", "errexit", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unresolved-profile", "exit_status": 2}` | sh-reduction |

| shell-case-074 | `["sh", "-oerrexit", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unresolved-profile", "exit_status": 2}` | sh-reduction |

| shell-case-075 | `["sh", "--future-option", "-c", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unresolved-profile", "exit_status": 2}` | sh-reduction |

| shell-case-076 | `["pwsh", "-FutureVendorCommand", "-Command", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | pwsh-grammar |

| shell-case-077 | `["pwsh", "-CommandWithArg", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | pwsh-grammar |

| shell-case-078 | `["powershell", "-CWA", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | windows-grammar |

| shell-case-079 | `["pwsh", "-ExecutionPol", "FuturePolicy", "-Command", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 2, "reason": "unsupported-option-value", "exit_status": 2}` | pwsh-grammar |

| shell-case-080 | `["powershell", "-FutureSwitch", "-File", "harmless.ps1", "-Command", "gh pr merge 1"]` | `{"outcome": "refusal", "kind": "indeterminate", "option_index": 1, "reason": "unsupported-option", "exit_status": 2}` | windows-grammar |


The displaced dash `future_option` input remains a supplementary refusal outside the immutable 80 and is authored in 1b.4:

```json
[
  {
    "id": "supplementary-dash-unknown-named-value",
    "argv": [
      "dash",
      "-o",
      "future_option",
      "-c",
      "gh pr merge 1"
    ],
    "expected": {
      "outcome": "refusal",
      "kind": "indeterminate",
      "option_index": 2,
      "reason": "unsupported-option-value",
      "exit_status": 2
    },
    "source_rule": "dash-grammar",
    "outside_immutable80": true,
    "authored_in": "1b.4"
  }
]
```

## Corpus identities and later implementation

Canonical case hashes use UTF-8 JSON with sorted keys and compact separators, without changing readable authored records:

| Published corpus | SHA-256 |
|---|---|

| 1b.1 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

| 1b.2 | `eacfcde596a9d74a88db8871a82bc977f23e0ce580d48971c095d2369bcbcd98` |

| 1b.3 | `3bd571a938cace976777a7d8d3983b3aaf706659c385675dd631fff7b1a71716` |

| 1b.4 | `ae32226036abeaa56600266853763ac12138de2e4a818045d4b01e6dce165c46` |


Phase 2 starts after all four 1b deliveries publish. It atomically updates the extractor and shared credential/body/cleanup consumers, preserves public `str`/`None`/`SystemExit(2)` behavior, exercises all 80 cases and full-profile prefixes, and preserves existing tool/resource/cost mappings. Bare sh requires family consensus over possible shell meanings; reject indeterminate/disagreeing outcomes rather than choose a convenient shell. No backend lookup or network is allowed at runtime. Native wiring follows phase 2 review, exact-head CI and causal publication. Existing native wiring candidate and its review findings remain owned separately; no activation is inferred from these test-only oracles.

## Both-host source coverage


```agent-host-coverage
{
  "schema_version": 1,
  "shared_source": ".agents/hooks/tests/fixtures/shell_profile_oracle.py and offline shell fixtures/tests",
  "hosts": [
    {
      "host": "claude",
      "behavior": "Validate complete source-backed offline shell profiles before the shared extractor change.",
      "source": "The four fixture/helper/test paths in the current 1b.1 lease.",
      "mapping": "Existing .agents/plugins/harness/engineering.json shared claude mapping is preserved.",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "Phase 1a PR #211 and causal main Windows/Linux CI passed. The complete 1b contract is fixed here; 1b.1 implementation and eight focused tests passed; final candidate checks, immutable review and exact-head CI remain pending."
      },
      "exception": {
        "constraint_evidence": "Test-only source publication does not establish installed native activation.",
        "supported_other_host_outcome": "Both hosts consume the same shared oracle and future extractor. No normal profile is installed or claimed active."
      }
    },
    {
      "host": "codex",
      "behavior": "Validate complete source-backed offline shell profiles before the shared extractor change.",
      "source": "The four fixture/helper/test paths in the current 1b.1 lease.",
      "mapping": "Existing .agents/plugins/harness/engineering.json shared codex mapping is preserved.",
      "verification": {
        "level": "source",
        "result": "limited",
        "evidence": "Phase 1a PR #211 and causal main Windows/Linux CI passed. The complete 1b contract is fixed here; 1b.1 implementation and eight focused tests passed; final candidate checks, immutable review and exact-head CI remain pending."
      },
      "exception": {
        "constraint_evidence": "Test-only source publication does not establish installed native activation.",
        "supported_other_host_outcome": "Both hosts consume the same shared oracle and future extractor. No normal profile is installed or claimed active."
      }
    }
  ]
}
```

## Execution readiness and next action

The primary-source recovery and fixed full 80-case/42-descriptor contract are complete. Descriptor-only1b.1 implementation is complete and all Source leases are released. Parent acceptance verified unchanged eleven Unix groups and nine prior provenance records, the exact ordered42 descriptors from this Goal,436 total records,24 Windows projection rows and the corrected Version provenance boundary. Actual eight focused tests passed in the shell-profile-oracle-version-provenance workflow capture. Four Source paths are +934/-30 (964 substantive changed lines), separately from the maintained Goal document (+1017/-39 before this progress reconciliation); the readable full total is reported rather than hidden. The four-slice assessment still applies and no source scope grows here. Required generation/catalog/harness/source checks, commit, one pre-review synchronization, immutable review and exact-head Windows/Linux CI are next. Later cases remain sequential deliveries. Parent continues the original rollout through all remaining phases and records every delivery gate in its canonical plan.
