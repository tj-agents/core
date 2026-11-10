# Python standards baseline

Existing violations at `03f99b363e11943cf8918a99b6a7654f5b770edb` are baselined by exact authored file and rule. New files receive all enabled checks. Remove an exception when repairing its source. The tool configuration owns enforcement; this document records the rollout evidence and rationale.

## Ruff

Reason: preserve existing implementations during the standards rollout. Each row records the existing count and a representative required repair. No wildcard path or whole-rule ignores were added.

| File | Rule | Existing count | Required repair |
| --- | --- | ---: | --- |
| `.agents/engineering/utility/guide-build/scripts/scaffold.py` | `E501` | 1 | Line too long (104 > 88) |
| `.agents/engineering/utility/guide-build/template/build.py` | `B023` | 1 | Function definition does not bind loop variable `path` |
| `.agents/engineering/utility/guide-build/template/build.py` | `B904` | 2 | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling |
| `.agents/engineering/utility/guide-build/template/build.py` | `E501` | 37 | Line too long (92 > 88) |
| `.agents/engineering/utility/guide-build/template/build.py` | `E741` | 3 | Ambiguous variable name: `l` |
| `.agents/engineering/utility/guide-build/template/build.py` | `RUF001` | 2 | String contains ambiguous `ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“` (EN DASH). Did you mean `-` (HYPHEN-MINUS)? |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `E501` | 14 | Line too long (89 > 88) |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `UP036` | 1 | Version block is outdated for minimum Python version |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `E501` | 30 | Line too long (97 > 88) |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `N818` | 1 | Exception name `Preserve` should be named with an Error suffix |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `PTH105` | 1 | `os.replace()` should be replaced by `Path.replace()` |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `PTH108` | 1 | `os.unlink()` should be replaced by `Path.unlink()` |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `PTH110` | 1 | `os.path.exists()` should be replaced by `Path.exists()` |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `C420` | 1 | Unnecessary dict comprehension for iterable; use `dict.fromkeys` instead |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `E501` | 37 | Line too long (90 > 88) |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `N818` | 1 | Exception name `UnreadableLaunches` should be named with an Error suffix |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `RUF005` | 1 | Consider `[*porcelain.splitlines(), ""]` instead of concatenation |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/check_tier_payload.py` | `E501` | 42 | Line too long (95 > 88) |
| `.agents/hooks/check_tier_payload.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/check_tier_payload.py` | `SIM102` | 1 | Use a single `if` statement instead of nested `if` statements |
| `.agents/hooks/docs_reachability.py` | `E501` | 19 | Line too long (94 > 88) |
| `.agents/hooks/docs_reachability.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/hook_runtime.py` | `E501` | 9 | Line too long (91 > 88) |
| `.agents/hooks/hook_runtime.py` | `SIM105` | 2 | Use `contextlib.suppress(OSError)` instead of `try`-`except`-`pass` |
| `.agents/hooks/installed_skills.py` | `E501` | 7 | Line too long (107 > 88) |
| `.agents/hooks/installed_skills.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/merge_review_gate.py` | `E501` | 25 | Line too long (90 > 88) |
| `.agents/hooks/merge_review_gate.py` | `N818` | 1 | Exception name `ConfigUnusable` should be named with an Error suffix |
| `.agents/hooks/merge_review_gate.py` | `SIM102` | 1 | Use a single `if` statement instead of nested `if` statements |
| `.agents/hooks/plan_graph.py` | `B905` | 1 | `zip()` without an explicit `strict=` parameter |
| `.agents/hooks/plan_graph.py` | `E501` | 25 | Line too long (89 > 88) |
| `.agents/hooks/plan_graph.py` | `F841` | 1 | Local variable `error` is assigned to but never used |
| `.agents/hooks/plan_graph.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/plan_graph.py` | `PIE810` | 1 | Call `startswith` once with a `tuple` |
| `.agents/hooks/problem_records.py` | `E501` | 15 | Line too long (93 > 88) |
| `.agents/hooks/problem_records.py` | `UP036` | 1 | Version block is outdated for minimum Python version |
| `.agents/hooks/project_facts.py` | `E501` | 47 | Line too long (121 > 88) |
| `.agents/hooks/project_facts.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/project_facts.py` | `RUF005` | 2 | Consider `[*sorted(set(members)), workspace.id]` instead of concatenation |
| `.agents/hooks/standards_context.py` | `E501` | 20 | Line too long (109 > 88) |
| `.agents/hooks/standards_context.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/fixtures/continuation_fixture.py` | `E501` | 9 | Line too long (99 > 88) |
| `.agents/hooks/tests/fixtures/continuation_fixture.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/fixtures/continuation_fixture.py` | `PLW1514` | 1 | `pathlib.Path(...).write_text` without explicit `encoding` argument |
| `.agents/hooks/tests/fixtures/continuation_runtime_fixture.py` | `E402` | 1 | Module level import not at top of file |
| `.agents/hooks/tests/fixtures/continuation_runtime_fixture.py` | `E501` | 2 | Line too long (104 > 88) |
| `.agents/hooks/tests/fixtures/continuation_runtime_fixture.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/fixtures/continuation_runtime_fixture.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/fixtures/fake_cli.py` | `E501` | 4 | Line too long (104 > 88) |
| `.agents/hooks/tests/fixtures/lane_expectations.py` | `E501` | 7 | Line too long (102 > 88) |
| `.agents/hooks/tests/fixtures/lane_expectations.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/fixtures/plan_authoring_harness.py` | `E501` | 8 | Line too long (103 > 88) |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `E501` | 7 | Line too long (93 > 88) |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `PLR6301` | 1 | Method `trust_continuation` could be a function, class method, or static method |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `RUF012` | 1 | Mutable default value for class attribute |
| `.agents/hooks/tests/fixtures/review_workflow_harness.py` | `B023` | 9 | Function definition does not bind loop variable `ready` |
| `.agents/hooks/tests/fixtures/review_workflow_harness.py` | `E501` | 11 | Line too long (100 > 88) |
| `.agents/hooks/tests/fixtures/review_workflow_harness.py` | `PLR6301` | 7 | Method `capture` could be a function, class method, or static method |
| `.agents/hooks/tests/fixtures/review_workflow_harness.py` | `RUF005` | 1 | Consider iterable unpacking instead of concatenation |
| `.agents/hooks/tests/fixtures/shell_profile_oracle.py` | `B905` | 1 | `zip()` without an explicit `strict=` parameter |
| `.agents/hooks/tests/fixtures/shell_profile_oracle.py` | `C420` | 1 | Unnecessary dict comprehension for iterable; use `dict.fromkeys` instead |
| `.agents/hooks/tests/fixtures/shell_profile_oracle.py` | `E501` | 25 | Line too long (99 > 88) |
| `.agents/hooks/tests/fixtures/shell_profile_oracle.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/fixtures/task_workflow_harness.py` | `E501` | 13 | Line too long (89 > 88) |
| `.agents/hooks/tests/fixtures/task_workflow_harness.py` | `F401` | 1 | `json` imported but unused |
| `.agents/hooks/tests/fixtures/task_workflow_harness.py` | `PLR6301` | 3 | Method `capture` could be a function, class method, or static method |
| `.agents/hooks/tests/fixtures/task_workflow_harness.py` | `RUF012` | 1 | Mutable default value for class attribute |
| `.agents/hooks/tests/fixtures/workflow_writer_lease_worker.py` | `E402` | 2 | Module level import not at top of file |
| `.agents/hooks/tests/fixtures/workflow_writer_lease_worker.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/fixtures/workflow_writer_lease_worker.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_auto_merge.py` | `E501` | 67 | Line too long (101 > 88) |
| `.agents/hooks/tests/test_auto_merge.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_auto_merge.py` | `PLR6301` | 1 | Method `binding` could be a function, class method, or static method |
| `.agents/hooks/tests/test_auto_merge.py` | `PT009` | 10 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_auto_merge.py` | `SIM117` | 6 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_auto_merge.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_completion.py` | `B023` | 1 | Function definition does not bind loop variable `body` |
| `.agents/hooks/tests/test_completion.py` | `E501` | 40 | Line too long (95 > 88) |
| `.agents/hooks/tests/test_completion.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_completion.py` | `PLR6301` | 1 | Method `publisher_follow_up` could be a function, class method, or static method |
| `.agents/hooks/tests/test_completion.py` | `PT009` | 51 | Use a regular `assert` instead of unittest-style `assertTrue` |
| `.agents/hooks/tests/test_completion.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_continuation_runtime.py` | `BLE001` | 1 | Do not catch blind exception: `BaseException` |
| `.agents/hooks/tests/test_continuation_runtime.py` | `E501` | 87 | Line too long (107 > 88) |
| `.agents/hooks/tests/test_continuation_runtime.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_continuation_runtime.py` | `PT009` | 164 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_continuation_runtime.py` | `SIM117` | 4 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_continuation_runtime.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_delivery_runtime.py` | `E402` | 1 | Module level import not at top of file |
| `.agents/hooks/tests/test_delivery_runtime.py` | `E501` | 14 | Line too long (108 > 88) |
| `.agents/hooks/tests/test_delivery_runtime.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_delivery_runtime.py` | `PLR6301` | 2 | Method `policy` could be a function, class method, or static method |
| `.agents/hooks/tests/test_delivery_runtime.py` | `PT009` | 70 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_delivery_runtime.py` | `RUF012` | 1 | Mutable default value for class attribute |
| `.agents/hooks/tests/test_delivery_runtime.py` | `SIM117` | 2 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_delivery_runtime.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_docs_reachability.py` | `E501` | 9 | Line too long (95 > 88) |
| `.agents/hooks/tests/test_docs_reachability.py` | `PT009` | 23 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_docs_reachability.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_goal_preflight.py` | `E501` | 10 | Line too long (101 > 88) |
| `.agents/hooks/tests/test_goal_preflight.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_goal_preflight.py` | `PT009` | 21 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_goal_preflight.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_handoff_transfer.py` | `E501` | 32 | Line too long (94 > 88) |
| `.agents/hooks/tests/test_handoff_transfer.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_handoff_transfer.py` | `PT009` | 20 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_handoff_transfer.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `.agents/hooks/tests/test_hook_runtime.py` | `E402` | 1 | Module level import not at top of file |
| `.agents/hooks/tests/test_hook_runtime.py` | `E501` | 10 | Line too long (89 > 88) |
| `.agents/hooks/tests/test_hook_runtime.py` | `PLR6301` | 1 | Method `payload` could be a function, class method, or static method |
| `.agents/hooks/tests/test_hook_runtime.py` | `PT009` | 30 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_hook_runtime.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_host_cli.py` | `E402` | 2 | Module level import not at top of file |
| `.agents/hooks/tests/test_host_cli.py` | `E501` | 6 | Line too long (104 > 88) |
| `.agents/hooks/tests/test_host_cli.py` | `PT009` | 5 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_host_cli.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_lane_tables.py` | `E501` | 65 | Line too long (103 > 88) |
| `.agents/hooks/tests/test_lane_tables.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_lane_tables.py` | `PLR6301` | 2 | Method `skills` could be a function, class method, or static method |
| `.agents/hooks/tests/test_lane_tables.py` | `PT009` | 82 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_lane_tables.py` | `TID251` | 6 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `E501` | 39 | Line too long (100 > 88) |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `PT009` | 87 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `RUF059` | 19 | Unpacked variable `bare` is never used |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `SIM117` | 2 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `.agents/hooks/tests/test_merge_review_gate.py` | `E501` | 27 | Line too long (108 > 88) |
| `.agents/hooks/tests/test_merge_review_gate.py` | `PT009` | 42 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_merge_review_gate.py` | `SIM117` | 1 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_merge_review_gate.py` | `TID251` | 6 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_plan_graph.py` | `E501` | 17 | Line too long (95 > 88) |
| `.agents/hooks/tests/test_plan_graph.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_plan_graph.py` | `PT009` | 50 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_plan_graph.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_plan_workflows.py` | `E402` | 4 | Module level import not at top of file |
| `.agents/hooks/tests/test_plan_workflows.py` | `E501` | 19 | Line too long (94 > 88) |
| `.agents/hooks/tests/test_plan_workflows.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_plan_workflows.py` | `PT009` | 101 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_plan_workflows.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_pr_body.py` | `E501` | 9 | Line too long (111 > 88) |
| `.agents/hooks/tests/test_pr_body.py` | `F401` | 2 | `io` imported but unused |
| `.agents/hooks/tests/test_pr_body.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_pr_body.py` | `PT009` | 16 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_pr_body.py` | `PTH201` | 4 | Do not pass the current directory explicitly to `Path` |
| `.agents/hooks/tests/test_pr_body.py` | `SIM117` | 1 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_pr_body.py` | `TID251` | 4 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_problem_records.py` | `E501` | 34 | Line too long (126 > 88) |
| `.agents/hooks/tests/test_problem_records.py` | `PT009` | 16 | Use a regular `assert` instead of unittest-style `assertIsNone` |
| `.agents/hooks/tests/test_problem_records.py` | `PTH109` | 2 | `os.getcwd()` should be replaced by `Path.cwd()` |
| `.agents/hooks/tests/test_problem_records.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_process_standards.py` | `E501` | 28 | Line too long (90 > 88) |
| `.agents/hooks/tests/test_process_standards.py` | `F841` | 1 | Local variable `workflow` is assigned to but never used |
| `.agents/hooks/tests/test_process_standards.py` | `PT009` | 79 | Use a regular `assert` instead of unittest-style `assertNotIn` |
| `.agents/hooks/tests/test_process_standards.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `.agents/hooks/tests/test_repository_configuration.py` | `E402` | 1 | Module level import not at top of file |
| `.agents/hooks/tests/test_repository_configuration.py` | `E501` | 10 | Line too long (114 > 88) |
| `.agents/hooks/tests/test_repository_configuration.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_repository_configuration.py` | `PT009` | 28 | Use a regular `assert` instead of unittest-style `assertFalse` |
| `.agents/hooks/tests/test_repository_configuration.py` | `PTH211` | 2 | `os.symlink` should be replaced by `Path.symlink_to` |
| `.agents/hooks/tests/test_repository_configuration.py` | `SIM117` | 1 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_repository_configuration.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_review_evidence.py` | `B023` | 3 | Function definition does not bind loop variable `branch` |
| `.agents/hooks/tests/test_review_evidence.py` | `E402` | 4 | Module level import not at top of file |
| `.agents/hooks/tests/test_review_evidence.py` | `E501` | 41 | Line too long (106 > 88) |
| `.agents/hooks/tests/test_review_evidence.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_review_evidence.py` | `PT009` | 28 | Use a regular `assert` instead of unittest-style `assertIn` |
| `.agents/hooks/tests/test_review_evidence.py` | `SIM117` | 2 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_review_evidence.py` | `TID251` | 4 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_review_workflows.py` | `E402` | 3 | Module level import not at top of file |
| `.agents/hooks/tests/test_review_workflows.py` | `E501` | 20 | Line too long (99 > 88) |
| `.agents/hooks/tests/test_review_workflows.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_review_workflows.py` | `PLR6301` | 1 | Method `harness_artifacts` could be a function, class method, or static method |
| `.agents/hooks/tests/test_review_workflows.py` | `PT009` | 130 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_review_workflows.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_review_workflows.py` | `UP012` | 1 | Unnecessary UTF-8 `encoding` argument to `encode` |
| `.agents/hooks/tests/test_shell_profile_oracle.py` | `E501` | 33 | Line too long (104 > 88) |
| `.agents/hooks/tests/test_shell_profile_oracle.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_shell_profile_oracle.py` | `PT009` | 31 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_shell_profile_oracle.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_task_workflows.py` | `E402` | 4 | Module level import not at top of file |
| `.agents/hooks/tests/test_task_workflows.py` | `E501` | 12 | Line too long (89 > 88) |
| `.agents/hooks/tests/test_task_workflows.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_task_workflows.py` | `PLR6301` | 1 | Method `harness` could be a function, class method, or static method |
| `.agents/hooks/tests/test_task_workflows.py` | `PT009` | 41 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_task_workflows.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_workflow_adoption.py` | `C401` | 1 | Unnecessary generator (rewrite as a set comprehension) |
| `.agents/hooks/tests/test_workflow_adoption.py` | `E402` | 1 | Module level import not at top of file |
| `.agents/hooks/tests/test_workflow_adoption.py` | `E501` | 1 | Line too long (90 > 88) |
| `.agents/hooks/tests/test_workflow_adoption.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_workflow_adoption.py` | `PT009` | 13 | Use a regular `assert` instead of unittest-style `assertIn` |
| `.agents/hooks/tests/test_workflow_adoption.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_workflow_contracts.py` | `B905` | 3 | `zip()` without an explicit `strict=` parameter |
| `.agents/hooks/tests/test_workflow_contracts.py` | `C416` | 1 | Unnecessary dict comprehension (rewrite using `dict()`) |
| `.agents/hooks/tests/test_workflow_contracts.py` | `E402` | 5 | Module level import not at top of file |
| `.agents/hooks/tests/test_workflow_contracts.py` | `E501` | 165 | Line too long (93 > 88) |
| `.agents/hooks/tests/test_workflow_contracts.py` | `E731` | 1 | Do not assign a `lambda` expression, use a `def` |
| `.agents/hooks/tests/test_workflow_contracts.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_workflow_contracts.py` | `PLR6301` | 3 | Method `normalized` could be a function, class method, or static method |
| `.agents/hooks/tests/test_workflow_contracts.py` | `PT009` | 283 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_workflow_contracts.py` | `SIM117` | 10 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_workflow_contracts.py` | `TID251` | 5 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tests/test_workflow_ops.py` | `B023` | 1 | Function definition does not bind loop variable `redirected` |
| `.agents/hooks/tests/test_workflow_ops.py` | `E501` | 167 | Line too long (95 > 88) |
| `.agents/hooks/tests/test_workflow_ops.py` | `F811` | 1 | Redefinition of unused `test_cleanup_validates_redirected_cache_ancestor_before_absent_bundle_probe` from line 778: `test_cleanup_validates_redirected_cache_ancestor_before_absent_bundle_probe` redefined here |
| `.agents/hooks/tests/test_workflow_ops.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_workflow_ops.py` | `PLR6301` | 4 | Method `pr` could be a function, class method, or static method |
| `.agents/hooks/tests/test_workflow_ops.py` | `PT009` | 225 | Use a regular `assert` instead of unittest-style `assertIs` |
| `.agents/hooks/tests/test_workflow_ops.py` | `SIM117` | 12 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `.agents/hooks/tests/test_workflow_ops.py` | `TID251` | 4 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `.agents/hooks/tests/test_worktree_sweep.py` | `E402` | 1 | Module level import not at top of file |
| `.agents/hooks/tests/test_worktree_sweep.py` | `E501` | 33 | Line too long (103 > 88) |
| `.agents/hooks/tests/test_worktree_sweep.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/hooks/tests/test_worktree_sweep.py` | `PLR6301` | 1 | Method `head` could be a function, class method, or static method |
| `.agents/hooks/tests/test_worktree_sweep.py` | `PT009` | 34 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `.agents/hooks/tests/test_worktree_sweep.py` | `PTH104` | 1 | `os.rename()` should be replaced by `Path.rename()` |
| `.agents/hooks/tests/test_worktree_sweep.py` | `TID251` | 4 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tier_gate.py` | `B904` | 1 | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling |
| `.agents/hooks/tier_gate.py` | `BLE001` | 1 | Do not catch blind exception: `Exception` |
| `.agents/hooks/tier_gate.py` | `C401` | 1 | Unnecessary generator (rewrite as a set comprehension) |
| `.agents/hooks/tier_gate.py` | `E501` | 219 | Line too long (97 > 88) |
| `.agents/hooks/tier_gate.py` | `E731` | 1 | Do not assign a `lambda` expression, use a `def` |
| `.agents/hooks/tier_gate.py` | `RUF005` | 3 | Consider `(*active, name)` instead of concatenation |
| `.agents/hooks/tier_gate.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/hooks/tier_gate.py` | `TRY300` | 2 | Consider moving this statement to an `else` block |
| `.agents/hooks/tier_gate.py` | `UP036` | 1 | Version block is outdated for minimum Python version |
| `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py` | `E501` | 15 | Line too long (89 > 88) |
| `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py` | `RUF005` | 1 | Consider iterable unpacking instead of concatenation |
| `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py` | `UP031` | 14 | Use format specifiers instead of percent format |
| `.agents/workflow/utility/catch-up/scripts/catch_up.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/workflow/utility/status/scripts/status.py` | `B904` | 1 | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling |
| `.agents/workflow/utility/status/scripts/status.py` | `E501` | 25 | Line too long (95 > 88) |
| `.agents/workflow/utility/status/scripts/status.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflow/utility/status/scripts/status.py` | `TID251` | 3 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/workflow/utility/status/scripts/status.py` | `UP031` | 16 | Use format specifiers instead of percent format |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `B904` | 4 | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `E501` | 13 | Line too long (99 > 88) |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `PTH105` | 1 | `os.replace()` should be replaced by `Path.replace()` |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `PTH108` | 1 | `os.unlink()` should be replaced by `Path.unlink()` |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `PTH110` | 1 | `os.path.exists()` should be replaced by `Path.exists()` |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `PTH123` | 1 | `open()` should be replaced by `Path.open()` |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `TRY300` | 1 | Consider moving this statement to an `else` block |
| `.agents/workflows/auto_merge.py` | `E402` | 3 | Module level import not at top of file |
| `.agents/workflows/auto_merge.py` | `E501` | 12 | Line too long (97 > 88) |
| `.agents/workflows/auto_merge.py` | `RUF021` | 2 | Parenthesize `a and b` expressions when chaining `and` and `or` together, to make the precedence clear |
| `.agents/workflows/auto_merge.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/workflows/completion.py` | `B904` | 1 | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling |
| `.agents/workflows/completion.py` | `E501` | 30 | Line too long (94 > 88) |
| `.agents/workflows/completion.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflows/completion.py` | `RUF059` | 1 | Unpacked variable `acceptance` is never used |
| `.agents/workflows/delivery_policy.py` | `E501` | 11 | Line too long (94 > 88) |
| `.agents/workflows/delivery_policy.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflows/delivery_policy.py` | `N818` | 1 | Exception name `PolicyViolation` should be named with an Error suffix |
| `.agents/workflows/delivery_policy.py` | `TID251` | 1 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `.agents/workflows/delivery_runtime.py` | `E501` | 65 | Line too long (101 > 88) |
| `.agents/workflows/delivery_runtime.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflows/delivery_runtime.py` | `N818` | 1 | Exception name `DeliveryContractViolation` should be named with an Error suffix |
| `.agents/workflows/delivery_runtime.py` | `PLR6301` | 8 | Method `validate_policy` could be a function, class method, or static method |
| `.agents/workflows/host_runtime.py` | `E501` | 29 | Line too long (98 > 88) |
| `.agents/workflows/host_runtime.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflows/host_runtime.py` | `PLC2701` | 2 | Private name import `_load_json` from external module `workflow_runtime` |
| `.agents/workflows/host_runtime.py` | `PLR6301` | 1 | Method `_model_route_key` could be a function, class method, or static method |
| `.agents/workflows/host_runtime.py` | `PTH115` | 1 | `os.readlink()` should be replaced by `Path.readlink()` |
| `.agents/workflows/host_runtime.py` | `RUF012` | 1 | Mutable default value for class attribute |
| `.agents/workflows/hosts/smoke.py` | `E402` | 1 | Module level import not at top of file |
| `.agents/workflows/hosts/smoke.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/workflows/pr_body.py` | `E501` | 6 | Line too long (92 > 88) |
| `.agents/workflows/pr_body.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflows/process_runtime.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/workflows/review_evidence.py` | `E501` | 14 | Line too long (97 > 88) |
| `.agents/workflows/review_evidence.py` | `PTH105` | 1 | `os.replace()` should be replaced by `Path.replace()` |
| `.agents/workflows/verify.py` | `E402` | 1 | Module level import not at top of file |
| `.agents/workflows/workflow_ops.py` | `B904` | 1 | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling |
| `.agents/workflows/workflow_ops.py` | `BLE001` | 1 | Do not catch blind exception: `Exception` |
| `.agents/workflows/workflow_ops.py` | `E402` | 6 | Module level import not at top of file |
| `.agents/workflows/workflow_ops.py` | `E501` | 268 | Line too long (92 > 88) |
| `.agents/workflows/workflow_ops.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflows/workflow_ops.py` | `PTH105` | 1 | `os.replace()` should be replaced by `Path.replace()` |
| `.agents/workflows/workflow_ops.py` | `PTH111` | 1 | `os.path.expanduser()` should be replaced by `Path.expanduser()` |
| `.agents/workflows/workflow_ops.py` | `PTH115` | 1 | `os.readlink()` should be replaced by `Path.readlink()` |
| `.agents/workflows/workflow_ops.py` | `PTH121` | 1 | `os.path.samefile()` should be replaced by `Path.samefile()` |
| `.agents/workflows/workflow_ops.py` | `RUF021` | 2 | Parenthesize `a and b` expressions when chaining `and` and `or` together, to make the precedence clear |
| `.agents/workflows/workflow_ops.py` | `SIM102` | 1 | Use a single `if` statement instead of nested `if` statements |
| `.agents/workflows/workflow_ops.py` | `SIM105` | 2 | Use `contextlib.suppress(OSError)` instead of `try`-`except`-`pass` |
| `.agents/workflows/workflow_ops.py` | `TID251` | 6 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.agents/workflows/workflow_ops.py` | `UP017` | 3 | Use `datetime.UTC` alias |
| `.agents/workflows/workflow_runtime.py` | `E501` | 109 | Line too long (99 > 88) |
| `.agents/workflows/workflow_runtime.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.agents/workflows/workflow_runtime.py` | `N818` | 1 | Exception name `ContractViolation` should be named with an Error suffix |
| `.agents/workflows/workflow_runtime.py` | `PIE810` | 2 | Call `startswith` once with a `tuple` |
| `.agents/workflows/workflow_runtime.py` | `SIM102` | 1 | Use a single `if` statement instead of nested `if` statements |
| `.agents/workflows/workflow_runtime.py` | `TID251` | 1 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `.agents/workflows/workflow_runtime.py` | `TRY300` | 1 | Consider moving this statement to an `else` block |
| `.codex/hooks/bootstrap.py` | `E401` | 1 | Multiple imports on one line |
| `.codex/hooks/bootstrap.py` | `E501` | 6 | Line too long (98 > 88) |
| `.codex/hooks/bootstrap.py` | `F821` | 1 | Undefined name `LOADER_DIGEST` |
| `.codex/hooks/bootstrap.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.codex/hooks/snapshot.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.codex/runtime/continuation/continuation_runtime.py` | `E402` | 4 | Module level import not at top of file |
| `.codex/runtime/continuation/continuation_runtime.py` | `E501` | 77 | Line too long (120 > 88) |
| `.codex/runtime/continuation/continuation_runtime.py` | `I001` | 2 | Import block is un-sorted or un-formatted |
| `.codex/runtime/continuation/continuation_runtime.py` | `N818` | 1 | Exception name `Gate` should be named with an Error suffix |
| `.codex/runtime/continuation/continuation_runtime.py` | `PLW1514` | 1 | `pathlib.Path(...).read_text` without explicit `encoding` argument |
| `.codex/runtime/continuation/continuation_runtime.py` | `SIM105` | 1 | Use `contextlib.suppress(ProcessLookupError)` instead of `try`-`except`-`pass` |
| `.codex/runtime/continuation/continuation_runtime.py` | `TID251` | 1 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.codex/runtime/continuation/continuation_runtime.py` | `TRY300` | 1 | Consider moving this statement to an `else` block |
| `.codex/runtime/continuation/continuation_scheduler.py` | `B007` | 1 | Loop control variable `expected` not used within loop body |
| `.codex/runtime/continuation/continuation_scheduler.py` | `E501` | 90 | Line too long (92 > 88) |
| `.codex/runtime/continuation/continuation_scheduler.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.codex/runtime/continuation/continuation_scheduler.py` | `PLR6301` | 4 | Method `run` could be a function, class method, or static method |
| `.codex/runtime/continuation/continuation_scheduler.py` | `PTH105` | 2 | `os.replace()` should be replaced by `Path.replace()` |
| `.codex/runtime/continuation/continuation_scheduler.py` | `PTH115` | 1 | `os.readlink()` should be replaced by `Path.readlink()` |
| `.codex/runtime/continuation/continuation_scheduler.py` | `SIM102` | 3 | Use a single `if` statement instead of nested `if` statements |
| `.codex/runtime/continuation/continuation_scheduler.py` | `SIM105` | 3 | Use `contextlib.suppress(FileNotFoundError)` instead of `try`-`except`-`pass` |
| `.codex/runtime/continuation/continuation_scheduler.py` | `SIM112` | 1 | Use capitalized environment variable `SYSTEMROOT` instead of `SystemRoot` |
| `.codex/runtime/continuation/delivery_continuation.py` | `B904` | 1 | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling |
| `.codex/runtime/continuation/delivery_continuation.py` | `E402` | 1 | Module level import not at top of file |
| `.codex/runtime/continuation/delivery_continuation.py` | `E501` | 76 | Line too long (101 > 88) |
| `.codex/runtime/continuation/delivery_continuation.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `.codex/runtime/continuation/delivery_continuation.py` | `SIM102` | 1 | Use a single `if` statement instead of nested `if` statements |
| `.codex/runtime/continuation/delivery_continuation.py` | `SIM105` | 2 | Use `contextlib.suppress(FileNotFoundError)` instead of `try`-`except`-`pass` |
| `.codex/runtime/continuation/delivery_continuation.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `.codex/runtime/continuation/delivery_continuation.py` | `TRY300` | 1 | Consider moving this statement to an `else` block |
| `packages/tj-base/tests/test_startup.py` | `PT011` | 3 | `pytest.raises(tj_base.startup.ProtocolError)` is too broad, set the `match` parameter or use a more specific exception |
| `scripts/check_generated_paths.py` | `E501` | 8 | Line too long (95 > 88) |
| `scripts/check_generated_paths.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `scripts/ci_native_acceptance.py` | `E501` | 12 | Line too long (96 > 88) |
| `scripts/ci_native_acceptance.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `scripts/ci_native_acceptance.py` | `UP036` | 1 | Version block is outdated for minimum Python version |
| `scripts/ci_selection.py` | `C420` | 1 | Unnecessary dict comprehension for iterable; use `dict.fromkeys` instead |
| `scripts/ci_selection.py` | `E501` | 21 | Line too long (97 > 88) |
| `scripts/ci_selection.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `scripts/ci_selection.py` | `UP036` | 1 | Version block is outdated for minimum Python version |
| `scripts/native_host_acceptance.py` | `B905` | 1 | `zip()` without an explicit `strict=` parameter |
| `scripts/native_host_acceptance.py` | `E501` | 6 | Line too long (98 > 88) |
| `scripts/native_host_acceptance.py` | `N815` | 1 | Variable `do_GET` in class scope should not be mixedCase |
| `scripts/native_host_acceptance.py` | `SIM105` | 2 | Use `contextlib.suppress(OSError)` instead of `try`-`except`-`pass` |
| `scripts/native_host_acceptance.py` | `TID251` | 3 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `scripts/native_host_acceptance.py` | `TRY300` | 1 | Consider moving this statement to an `else` block |
| `scripts/runtime_sources.py` | `E501` | 22 | Line too long (98 > 88) |
| `scripts/runtime_sources.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `scripts/runtime_sources.py` | `TRY300` | 1 | Consider moving this statement to an `else` block |
| `scripts/sync_harness_manifests.py` | `E501` | 26 | Line too long (89 > 88) |
| `scripts/sync_harness_manifests.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `scripts/sync_harness_manifests.py` | `RUF021` | 1 | Parenthesize `a and b` expressions when chaining `and` and `or` together, to make the precedence clear |
| `scripts/sync_harness_manifests.py` | `TID251` | 1 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `scripts/sync_plugin_packages.py` | `B904` | 1 | Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling |
| `scripts/sync_plugin_packages.py` | `E501` | 103 | Line too long (119 > 88) |
| `scripts/sync_plugin_packages.py` | `SIM102` | 1 | Use a single `if` statement instead of nested `if` statements |
| `scripts/sync_plugin_packages.py` | `SIM105` | 1 | Use `contextlib.suppress(OSError)` instead of `try`-`except`-`pass` |
| `scripts/sync_plugin_packages.py` | `TID251` | 1 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `scripts/update_plugin_digests.py` | `E501` | 8 | Line too long (103 > 88) |
| `scripts/update_plugin_digests.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `scripts/update_plugin_digests.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/fixtures/fake_claude.py` | `E501` | 14 | Line too long (126 > 88) |
| `tests/fixtures/fake_claude.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/fixtures/fake_claude.py` | `PTH109` | 3 | `os.getcwd()` should be replaced by `Path.cwd()` |
| `tests/fixtures/fake_claude.py` | `PTH116` | 1 | `os.stat()` should be replaced by `Path.stat()`, `Path.owner()`, or `Path.group()` |
| `tests/fixtures/fake_claude.py` | `PTH123` | 1 | `open()` should be replaced by `Path.open()` |
| `tests/fixtures/plugin_autoupdate_208cc302.py` | `E501` | 4 | Line too long (93 > 88) |
| `tests/fixtures/plugin_autoupdate_208cc302.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/fixtures/plugin_autoupdate_208cc302.py` | `PTH105` | 1 | `os.replace()` should be replaced by `Path.replace()` |
| `tests/fixtures/plugin_cli.py` | `E501` | 5 | Line too long (93 > 88) |
| `tests/fixtures/plugin_cli.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/fixtures/setup_probe.py` | `E501` | 2 | Line too long (100 > 88) |
| `tests/fixtures/setup_probe.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/native_plugin_inventory.py` | `E501` | 1 | Line too long (91 > 88) |
| `tests/native_plugin_inventory.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_agent_files.py` | `E501` | 5 | Line too long (94 > 88) |
| `tests/test_agent_files.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_agent_files.py` | `PT009` | 4 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_agent_files.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_background_processes.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_catch_up.py` | `PLR6301` | 1 | Method `report` could be a function, class method, or static method |
| `tests/test_catch_up.py` | `PT009` | 6 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_catch_up.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_check_generated_paths.py` | `E501` | 11 | Line too long (96 > 88) |
| `tests/test_check_generated_paths.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_check_generated_paths.py` | `PT009` | 6 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_check_generated_paths.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_check_tier_payload.py` | `E501` | 23 | Line too long (89 > 88) |
| `tests/test_check_tier_payload.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_check_tier_payload.py` | `PT009` | 18 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_check_tier_payload.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_ci_native_acceptance.py` | `E501` | 4 | Line too long (115 > 88) |
| `tests/test_ci_native_acceptance.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_ci_native_acceptance.py` | `PLR6301` | 1 | Method `archive` could be a function, class method, or static method |
| `tests/test_ci_native_acceptance.py` | `PT009` | 4 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_ci_native_acceptance.py` | `SIM117` | 1 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `tests/test_ci_native_acceptance.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_ci_selection.py` | `E501` | 66 | Line too long (95 > 88) |
| `tests/test_ci_selection.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_ci_selection.py` | `PT009` | 59 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_ci_selection.py` | `TID251` | 6 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_codex_hook_snapshot.py` | `E501` | 47 | Line too long (99 > 88) |
| `tests/test_codex_hook_snapshot.py` | `F811` | 1 | Redefinition of unused `test_startup_snapshot_loader_keeps_an_existing_session_callable_after_live_loader_changes` from line 275: `test_startup_snapshot_loader_keeps_an_existing_session_callable_after_live_loader_changes` redefined here |
| `tests/test_codex_hook_snapshot.py` | `PT009` | 58 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_codex_hook_snapshot.py` | `TID251` | 3 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_codex_hook_snapshot.py` | `UP012` | 1 | Unnecessary UTF-8 `encoding` argument to `encode` |
| `tests/test_codex_startup_dispatch.py` | `E501` | 4 | Line too long (95 > 88) |
| `tests/test_codex_startup_dispatch.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_codex_startup_dispatch.py` | `PLR6301` | 1 | Method `manifest` could be a function, class method, or static method |
| `tests/test_codex_startup_dispatch.py` | `PT009` | 7 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_codex_startup_dispatch.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_codex_windows_hook_commands.py` | `E501` | 2 | Line too long (117 > 88) |
| `tests/test_codex_windows_hook_commands.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_codex_windows_hook_commands.py` | `PT009` | 3 | Use a regular `assert` instead of unittest-style `assertIn` |
| `tests/test_codex_windows_hook_commands.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_company_skill_replacement.py` | `E501` | 8 | Line too long (98 > 88) |
| `tests/test_company_skill_replacement.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_company_skill_replacement.py` | `PT009` | 1 | Use a regular `assert` instead of unittest-style `assertIn` |
| `tests/test_company_skill_replacement.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_delivery_continuation.py` | `E501` | 186 | Line too long (112 > 88) |
| `tests/test_delivery_continuation.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_delivery_continuation.py` | `PLR6301` | 2 | Method `put_linux` could be a function, class method, or static method |
| `tests/test_delivery_continuation.py` | `PT009` | 148 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_delivery_continuation.py` | `PTH115` | 1 | `os.readlink()` should be replaced by `Path.readlink()` |
| `tests/test_delivery_continuation.py` | `SIM117` | 4 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `tests/test_delivery_continuation.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_employer_tiers.py` | `E501` | 69 | Line too long (96 > 88) |
| `tests/test_employer_tiers.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_employer_tiers.py` | `PT009` | 70 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_employer_tiers.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_guide_build.py` | `E501` | 14 | Line too long (92 > 88) |
| `tests/test_guide_build.py` | `PT009` | 77 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_guide_build.py` | `RET504` | 1 | Unnecessary assignment to `result` before `return` statement |
| `tests/test_guide_build.py` | `TID251` | 2 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_harness_manifests.py` | `E501` | 28 | Line too long (90 > 88) |
| `tests/test_harness_manifests.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_harness_manifests.py` | `PLR6301` | 2 | Method `requires` could be a function, class method, or static method |
| `tests/test_harness_manifests.py` | `PT009` | 24 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_harness_manifests.py` | `RUF059` | 1 | Unpacked variable `rule` is never used |
| `tests/test_harness_manifests.py` | `TID251` | 7 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_hook_contract.py` | `E501` | 10 | Line too long (111 > 88) |
| `tests/test_hook_contract.py` | `PT009` | 7 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_hook_contract.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_hook_launch_budget.py` | `E501` | 22 | Line too long (95 > 88) |
| `tests/test_hook_launch_budget.py` | `PT009` | 7 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_hook_launch_budget.py` | `TID251` | 2 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_hook_launch_budget.py` | `UP017` | 1 | Use `datetime.UTC` alias |
| `tests/test_host_coverage.py` | `E501` | 13 | Line too long (117 > 88) |
| `tests/test_host_coverage.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_host_coverage.py` | `PT009` | 13 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_host_coverage.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_native_host_acceptance.py` | `TID251` | 1 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_plan_artifacts.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_plan_artifacts.py` | `PT009` | 5 | Use a regular `assert` instead of unittest-style `assertTrue` |
| `tests/test_plan_artifacts.py` | `TID251` | 2 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_plugin_update.py` | `E501` | 3 | Line too long (105 > 88) |
| `tests/test_plugin_update.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_plugin_update.py` | `PT009` | 2 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_plugin_update.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_project_facts.py` | `E501` | 135 | Line too long (94 > 88) |
| `tests/test_project_facts.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_project_facts.py` | `PLR6301` | 1 | Method `dependency` could be a function, class method, or static method |
| `tests/test_project_facts.py` | `PT009` | 90 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_project_facts.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_publisher_dependencies.py` | `E501` | 7 | Line too long (109 > 88) |
| `tests/test_publisher_dependencies.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_publisher_dependencies.py` | `PLR6301` | 1 | Method `roster` could be a function, class method, or static method |
| `tests/test_publisher_dependencies.py` | `PT009` | 1 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_publisher_dependencies.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_remote_host_tiers.py` | `E501` | 15 | Line too long (107 > 88) |
| `tests/test_remote_host_tiers.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_remote_host_tiers.py` | `PT009` | 27 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_remote_host_tiers.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_repository_permissions.py` | `E501` | 9 | Line too long (112 > 88) |
| `tests/test_repository_permissions.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_repository_permissions.py` | `PT009` | 18 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_repository_permissions.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_review_native_layer.py` | `E501` | 26 | Line too long (107 > 88) |
| `tests/test_review_native_layer.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_review_native_layer.py` | `PLR6301` | 1 | Method `host_entry` could be a function, class method, or static method |
| `tests/test_review_native_layer.py` | `PT009` | 34 | Use a regular `assert` instead of unittest-style `assertNotIn` |
| `tests/test_review_native_layer.py` | `TID251` | 3 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_review_rules.py` | `E501` | 34 | Line too long (94 > 88) |
| `tests/test_review_rules.py` | `PT009` | 19 | Use a regular `assert` instead of unittest-style `assertFalse` |
| `tests/test_review_rules.py` | `SIM117` | 1 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `tests/test_review_rules.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_runtime_sources.py` | `E501` | 8 | Line too long (132 > 88) |
| `tests/test_runtime_sources.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_runtime_sources.py` | `PLR6301` | 1 | Method `fake_remote_git` could be a function, class method, or static method |
| `tests/test_runtime_sources.py` | `PT009` | 13 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_runtime_sources.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_selected_standards.py` | `PLW1514` | 1 | `io.TextIOWrapper` without explicit `encoding` argument |
| `tests/test_selected_standards.py` | `TID251` | 1 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_source_layout.py` | `E501` | 56 | Line too long (101 > 88) |
| `tests/test_source_layout.py` | `F401` | 1 | `sys` imported but unused |
| `tests/test_source_layout.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_source_layout.py` | `PLR6301` | 1 | Method `body` could be a function, class method, or static method |
| `tests/test_source_layout.py` | `PT009` | 63 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_source_layout.py` | `RUF059` | 1 | Unpacked variable `config` is never used |
| `tests/test_source_layout.py` | `SIM117` | 2 | Use a single `with` statement with multiple contexts instead of nested `with` statements |
| `tests/test_source_layout.py` | `TID251` | 3 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_stack_tiers.py` | `C420` | 2 | Unnecessary dict comprehension for iterable; use `dict.fromkeys` instead |
| `tests/test_stack_tiers.py` | `E501` | 35 | Line too long (101 > 88) |
| `tests/test_stack_tiers.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_stack_tiers.py` | `PT009` | 62 | Use a regular `assert` instead of unittest-style `assertNotIn` |
| `tests/test_stack_tiers.py` | `TID251` | 5 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_standards_context.py` | `E501` | 35 | Line too long (150 > 88) |
| `tests/test_standards_context.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_standards_context.py` | `PLR6301` | 1 | Method `assertion` could be a function, class method, or static method |
| `tests/test_standards_context.py` | `PT009` | 29 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_standards_context.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_task_routing.py` | `E501` | 9 | Line too long (108 > 88) |
| `tests/test_task_routing.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_task_routing.py` | `PT009` | 12 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_task_routing.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_tier_predicates.py` | `E501` | 32 | Line too long (100 > 88) |
| `tests/test_tier_predicates.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_tier_predicates.py` | `PT009` | 44 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_tier_predicates.py` | `RUF059` | 1 | Unpacked variable `payload` is never used |
| `tests/test_tier_predicates.py` | `TID251` | 2 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_tier_tool_context.py` | `E501` | 2 | Line too long (89 > 88) |
| `tests/test_tier_tool_context.py` | `TID251` | 1 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |
| `tests/test_workflow_session_hooks.py` | `E501` | 2 | Line too long (91 > 88) |
| `tests/test_workflow_session_hooks.py` | `I001` | 1 | Import block is un-sorted or un-formatted |
| `tests/test_workflow_session_hooks.py` | `PLR6301` | 1 | Method `manifest` could be a function, class method, or static method |
| `tests/test_workflow_session_hooks.py` | `PT009` | 4 | Use a regular `assert` instead of unittest-style `assertNotIn` |
| `tests/test_workflow_session_hooks.py` | `TID251` | 1 | `unittest.TestCase` is banned: Use plain pytest functions and bare assertions. |
| `tests/test_workflow_status.py` | `E501` | 39 | Line too long (98 > 88) |
| `tests/test_workflow_status.py` | `PLR6301` | 1 | Method `select` could be a function, class method, or static method |
| `tests/test_workflow_status.py` | `PT009` | 95 | Use a regular `assert` instead of unittest-style `assertEqual` |
| `tests/test_workflow_status.py` | `TID251` | 2 | `sys.path` is banned: Install the declared dependency; do not modify the import search path. |
| `tests/test_workflow_status.py` | `UP031` | 7 | Use format specifiers instead of percent format |
| `tests/test_workspace_tiers.py` | `TID251` | 1 | `importlib.util.spec_from_file_location` is banned: Import the installed public API; do not load another checkout by path. |

## Ruff formatter

Exact existing files requiring formatting are excluded from the formatter during this rollout. Regenerate payloads after formatting authored source and then remove its exception. New files are checked.

- `.agents/engineering/utility/guide-build/scripts/scaffold.py`
- `.agents/engineering/utility/guide-build/template/build.py`
- `.agents/engineering/utility/review/scripts/review_rules.py`
- `.agents/engineering/workflow/merge/scripts/cleanup_proof.py`
- `.agents/engineering/workflow/merge/scripts/worktree_sweep.py`
- `.agents/hooks/check_tier_payload.py`
- `.agents/hooks/docs_reachability.py`
- `.agents/hooks/hook_runtime.py`
- `.agents/hooks/installed_skills.py`
- `.agents/hooks/merge_review_gate.py`
- `.agents/hooks/plan_graph.py`
- `.agents/hooks/problem_records.py`
- `.agents/hooks/project_facts.py`
- `.agents/hooks/standards_context.py`
- `.agents/hooks/tests/fixtures/continuation_fixture.py`
- `.agents/hooks/tests/fixtures/continuation_runtime_fixture.py`
- `.agents/hooks/tests/fixtures/fake_cli.py`
- `.agents/hooks/tests/fixtures/lane_expectations.py`
- `.agents/hooks/tests/fixtures/plan_authoring_harness.py`
- `.agents/hooks/tests/fixtures/plan_workflow_harness.py`
- `.agents/hooks/tests/fixtures/review_workflow_harness.py`
- `.agents/hooks/tests/fixtures/shell_profile_oracle.py`
- `.agents/hooks/tests/fixtures/task_workflow_harness.py`
- `.agents/hooks/tests/test_auto_merge.py`
- `.agents/hooks/tests/test_completion.py`
- `.agents/hooks/tests/test_continuation_runtime.py`
- `.agents/hooks/tests/test_delivery_runtime.py`
- `.agents/hooks/tests/test_docs_reachability.py`
- `.agents/hooks/tests/test_goal_preflight.py`
- `.agents/hooks/tests/test_handoff_transfer.py`
- `.agents/hooks/tests/test_hook_runtime.py`
- `.agents/hooks/tests/test_host_cli.py`
- `.agents/hooks/tests/test_lane_tables.py`
- `.agents/hooks/tests/test_merge_cleanup_proof.py`
- `.agents/hooks/tests/test_merge_review_gate.py`
- `.agents/hooks/tests/test_plan_graph.py`
- `.agents/hooks/tests/test_plan_workflows.py`
- `.agents/hooks/tests/test_pr_body.py`
- `.agents/hooks/tests/test_problem_records.py`
- `.agents/hooks/tests/test_process_standards.py`
- `.agents/hooks/tests/test_repository_configuration.py`
- `.agents/hooks/tests/test_review_evidence.py`
- `.agents/hooks/tests/test_review_workflows.py`
- `.agents/hooks/tests/test_shell_profile_oracle.py`
- `.agents/hooks/tests/test_task_workflows.py`
- `.agents/hooks/tests/test_workflow_adoption.py`
- `.agents/hooks/tests/test_workflow_contracts.py`
- `.agents/hooks/tests/test_workflow_ops.py`
- `.agents/hooks/tests/test_worktree_sweep.py`
- `.agents/hooks/tier_gate.py`
- `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py`
- `.agents/workflow/utility/status/scripts/status.py`
- `.agents/workflow/workflow/handoff/scripts/transfer.py`
- `.agents/workflows/auto_merge.py`
- `.agents/workflows/completion.py`
- `.agents/workflows/delivery_policy.py`
- `.agents/workflows/delivery_runtime.py`
- `.agents/workflows/host_runtime.py`
- `.agents/workflows/pr_body.py`
- `.agents/workflows/review_evidence.py`
- `.agents/workflows/workflow_ops.py`
- `.agents/workflows/workflow_runtime.py`
- `.codex/hooks/bootstrap.py`
- `.codex/runtime/continuation/continuation_runtime.py`
- `.codex/runtime/continuation/continuation_scheduler.py`
- `.codex/runtime/continuation/delivery_continuation.py`
- `packages/tj-base/src/tj_base/startup.py`
- `plans/delivery-binding-budget/GOAL.md`
- `scripts/check_generated_paths.py`
- `scripts/ci_native_acceptance.py`
- `scripts/ci_selection.py`
- `scripts/native_host_acceptance.py`
- `scripts/runtime_sources.py`
- `scripts/sync_harness_manifests.py`
- `scripts/sync_plugin_packages.py`
- `scripts/update_plugin_digests.py`
- `tests/fixtures/fake_claude.py`
- `tests/fixtures/plugin_autoupdate_208cc302.py`
- `tests/fixtures/plugin_cli.py`
- `tests/fixtures/setup_probe.py`
- `tests/native_plugin_inventory.py`
- `tests/test_agent_files.py`
- `tests/test_check_generated_paths.py`
- `tests/test_check_tier_payload.py`
- `tests/test_ci_native_acceptance.py`
- `tests/test_ci_selection.py`
- `tests/test_codex_hook_snapshot.py`
- `tests/test_codex_startup_dispatch.py`
- `tests/test_codex_windows_hook_commands.py`
- `tests/test_company_skill_replacement.py`
- `tests/test_delivery_continuation.py`
- `tests/test_employer_tiers.py`
- `tests/test_guide_build.py`
- `tests/test_harness_manifests.py`
- `tests/test_hook_contract.py`
- `tests/test_hook_launch_budget.py`
- `tests/test_host_coverage.py`
- `tests/test_plugin_update.py`
- `tests/test_project_facts.py`
- `tests/test_publisher_dependencies.py`
- `tests/test_remote_host_tiers.py`
- `tests/test_repository_permissions.py`
- `tests/test_review_native_layer.py`
- `tests/test_review_rules.py`
- `tests/test_runtime_sources.py`
- `tests/test_source_layout.py`
- `tests/test_stack_tiers.py`
- `tests/test_standards_context.py`
- `tests/test_task_routing.py`
- `tests/test_tier_predicates.py`
- `tests/test_tier_tool_context.py`
- `tests/test_workflow_session_hooks.py`
- `tests/test_workflow_status.py`

## Mypy

The previous target named a removed `.codex/adapters` directory. Targets cover authored source roots, with an explicit hook-test import root so fixtures have one module identity. Existing typing debt is baselined by exact module and diagnostic code. Annotate or repair each listed source, then remove its override. New modules receive all strict checks.

| File | Module | Rule | Existing count | Required repair |
| --- | --- | --- | ---: | --- |
| `.agents/engineering/utility/guide-build/scripts/scaffold.py` | `scaffold` | `no-untyped-call` | 9 | Call to untyped function "template_bytes_for" in typed context |
| `.agents/engineering/utility/guide-build/scripts/scaffold.py` | `scaffold` | `no-untyped-def` | 7 | Function is missing a type annotation |
| `.agents/engineering/utility/guide-build/template/build.py` | `build` | `no-untyped-call` | 17 | Call to untyped function "find" in typed context |
| `.agents/engineering/utility/guide-build/template/build.py` | `build` | `no-untyped-def` | 15 | Function is missing a type annotation |
| `.agents/engineering/utility/guide-build/template/build.py` | `build` | `union-attr` | 1 | Item "None" of "Match[str] \| None" has no attribute "groups" |
| `.agents/engineering/utility/guide-build/template/build.py` | `build` | `var-annotated` | 4 | Need type annotation for "by_line" (hint: "by_line: dict[<type>, <type>] = ...") |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `review_rules` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `review_rules` | `no-untyped-call` | 5 | Call to untyped function "effective_claude_entries" in typed context |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `review_rules` | `no-untyped-def` | 5 | Function is missing a return type annotation |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `review_rules` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `review_rules` | `var-annotated` | 1 | Need type annotation for "effective" (hint: "effective: dict[<type>, <type>] = ...") |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `cleanup_proof` | `no-untyped-call` | 92 | Call to untyped function "state_directory" in typed context |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `cleanup_proof` | `no-untyped-def` | 29 | Function is missing a type annotation |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `worktree_sweep` | `no-untyped-call` | 3 | Call to untyped function "default_branch" in typed context |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `worktree_sweep` | `no-untyped-def` | 1 | Function is missing a type annotation for one or more parameters |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `worktree_sweep` | `type-arg` | 8 | Missing type arguments for generic type "CompletedProcess" |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `worktree_sweep` | `var-annotated` | 1 | Need type annotation for "current" (hint: "current: dict[<type>, <type>] = ...") |
| `.agents/hooks/check_tier_payload.py` | `check_tier_payload` | `no-untyped-call` | 11 | Call to untyped function "front_matter" in typed context |
| `.agents/hooks/check_tier_payload.py` | `check_tier_payload` | `no-untyped-def` | 10 | Function is missing a type annotation |
| `.agents/hooks/check_tier_payload.py` | `check_tier_payload` | `var-annotated` | 2 | Need type annotation for "names" (hint: "names: list[<type>] = ...") |
| `.agents/hooks/docs_reachability.py` | `docs_reachability` | `no-untyped-call` | 33 | Call to untyped function "ignored" in typed context |
| `.agents/hooks/docs_reachability.py` | `docs_reachability` | `no-untyped-def` | 19 | Function is missing a type annotation |
| `.agents/hooks/docs_reachability.py` | `docs_reachability` | `var-annotated` | 3 | Need type annotation for "docs" (hint: "docs: list[<type>] = ...") |
| `.agents/hooks/hook_runtime.py` | `hook_runtime` | `attr-defined` | 5 | Module has no attribute "flock" |
| `.agents/hooks/hook_runtime.py` | `hook_runtime` | `no-untyped-call` | 8 | Call to untyped function "declared_plugin_root" in typed context |
| `.agents/hooks/hook_runtime.py` | `hook_runtime` | `no-untyped-def` | 9 | Function is missing a type annotation |
| `.agents/hooks/host_cli.py` | `host_cli` | `no-untyped-def` | 1 | Function is missing a type annotation |
| `.agents/hooks/installed_skills.py` | `installed_skills` | `no-untyped-call` | 11 | Call to untyped function "NativePluginDiscoveryError" in typed context |
| `.agents/hooks/installed_skills.py` | `installed_skills` | `no-untyped-def` | 7 | Function is missing a type annotation |
| `.agents/hooks/installed_skills.py` | `installed_skills` | `operator` | 1 | Unsupported operand types for / ("Path" and "None") |
| `.agents/hooks/merge_review_gate.py` | `merge_review_gate` | `no-untyped-call` | 13 | Call to untyped function "git" in typed context |
| `.agents/hooks/merge_review_gate.py` | `merge_review_gate` | `no-untyped-def` | 17 | Function is missing a type annotation |
| `.agents/hooks/plan_graph.py` | `plan_graph` | `no-untyped-call` | 54 | Call to untyped function "section" in typed context |
| `.agents/hooks/plan_graph.py` | `plan_graph` | `no-untyped-def` | 26 | Function is missing a type annotation |
| `.agents/hooks/plan_graph.py` | `plan_graph` | `var-annotated` | 1 | Need type annotation for "claims" (hint: "claims: dict[<type>, <type>] = ...") |
| `.agents/hooks/problem_records.py` | `problem_records` | `no-untyped-call` | 8 | Call to untyped function "selects_personal" in typed context |
| `.agents/hooks/problem_records.py` | `problem_records` | `no-untyped-def` | 7 | Function is missing a type annotation |
| `.agents/hooks/project_facts.py` | `project_facts` | `arg-type` | 1 | Argument 1 to "append" of "list" has incompatible type "tuple[Any, tuple[Any]]"; expected "tuple[Any, tuple[()]]" |
| `.agents/hooks/project_facts.py` | `project_facts` | `no-untyped-call` | 38 | Call to untyped function "problem" in typed context |
| `.agents/hooks/project_facts.py` | `project_facts` | `no-untyped-def` | 17 | Function is missing a type annotation |
| `.agents/hooks/project_facts.py` | `project_facts` | `var-annotated` | 2 | Need type annotation for "members" (hint: "members: list[<type>] = ...") |
| `.agents/hooks/standards_context.py` | `standards_context` | `no-untyped-call` | 8 | Call to untyped function "report" in typed context |
| `.agents/hooks/standards_context.py` | `standards_context` | `no-untyped-def` | 6 | Function is missing a type annotation |
| `.agents/hooks/standards_context.py` | `standards_context` | `var-annotated` | 2 | Need type annotation for "values" (hint: "values: dict[<type>, <type>] = ...") |
| `.agents/hooks/tests/fixtures/continuation_fixture.py` | `fixtures.continuation_fixture` | `arg-type` | 1 | Argument 1 to "dict" has incompatible type "str"; expected "Iterable[tuple[str, Any]]" |
| `.agents/hooks/tests/fixtures/continuation_fixture.py` | `fixtures.continuation_fixture` | `assignment` | 1 | Incompatible types in assignment (expression has type "dict[str, dict[str, Any]]", target has type "str") |
| `.agents/hooks/tests/fixtures/continuation_fixture.py` | `fixtures.continuation_fixture` | `index` | 1 | Invalid index type "str" for "str"; expected type "SupportsIndex \| slice[SupportsIndex \| None, SupportsIndex \| None, SupportsIndex \| None]" |
| `.agents/hooks/tests/fixtures/continuation_runtime_fixture.py` | `fixtures.continuation_runtime_fixture` | `no-untyped-def` | 1 | Function is missing a type annotation |
| `.agents/hooks/tests/fixtures/fake_cli.py` | `fixtures.fake_cli` | `no-untyped-call` | 1 | Call to untyped function "main" in typed context |
| `.agents/hooks/tests/fixtures/fake_cli.py` | `fixtures.fake_cli` | `no-untyped-def` | 4 | Function is missing a type annotation |
| `.agents/hooks/tests/fixtures/lane_expectations.py` | `fixtures.lane_expectations` | `no-untyped-call` | 1 | Call to untyped function "_table" in typed context |
| `.agents/hooks/tests/fixtures/lane_expectations.py` | `fixtures.lane_expectations` | `no-untyped-def` | 4 | Function is missing a type annotation |
| `.agents/hooks/tests/fixtures/plan_authoring_harness.py` | `fixtures.plan_authoring_harness` | `no-untyped-call` | 16 | Call to untyped function "initialize_repository" in typed context |
| `.agents/hooks/tests/fixtures/plan_authoring_harness.py` | `fixtures.plan_authoring_harness` | `no-untyped-def` | 10 | Function is missing a type annotation |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `fixtures.plan_workflow_harness` | `assignment` | 1 | Incompatible types in assignment (expression has type "def tracked(instance: Any, *arguments: Any, **keywords: Any) -> Any", variable has type "Callable[[Path, str \| None, str \| None], str]") |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `fixtures.plan_workflow_harness` | `index` | 4 | Value of type "Any \| None" is not indexable |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `fixtures.plan_workflow_harness` | `method-assign` | 2 | Cannot assign to a method |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `fixtures.plan_workflow_harness` | `no-untyped-call` | 53 | Call to untyped function "initialize_repository" in typed context |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `fixtures.plan_workflow_harness` | `no-untyped-def` | 26 | Function is missing a type annotation |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `fixtures.plan_workflow_harness` | `union-attr` | 4 | Item "None" of "Any \| None" has no attribute "resolve" |
| `.agents/hooks/tests/fixtures/plan_workflow_harness.py` | `fixtures.plan_workflow_harness` | `unreachable` | 1 | Statement is unreachable |
| `.agents/hooks/tests/fixtures/review_workflow_harness.py` | `fixtures.review_workflow_harness` | `attr-defined` | 2 | "Collection[Any]" has no attribute "append" |
| `.agents/hooks/tests/fixtures/review_workflow_harness.py` | `fixtures.review_workflow_harness` | `no-untyped-call` | 63 | Call to untyped function "prepare_repository" in typed context |
| `.agents/hooks/tests/fixtures/review_workflow_harness.py` | `fixtures.review_workflow_harness` | `no-untyped-def` | 32 | Function is missing a return type annotation |
| `.agents/hooks/tests/fixtures/review_workflow_harness.py` | `fixtures.review_workflow_harness` | `var-annotated` | 2 | Need type annotation for "waves" (hint: "waves: list[<type>] = ...") |
| `.agents/hooks/tests/fixtures/shell_profile_oracle.py` | `fixtures.shell_profile_oracle` | `call-overload` | 1 | No overload variant of "update" of "MutableMapping" matches argument type "object" |
| `.agents/hooks/tests/fixtures/shell_profile_oracle.py` | `fixtures.shell_profile_oracle` | `no-untyped-call` | 8 | Call to untyped function "load_json" in typed context |
| `.agents/hooks/tests/fixtures/shell_profile_oracle.py` | `fixtures.shell_profile_oracle` | `no-untyped-def` | 11 | Function is missing a type annotation |
| `.agents/hooks/tests/fixtures/task_workflow_harness.py` | `fixtures.task_workflow_harness` | `dict-item` | 1 | Dict entry 0 has incompatible type "str": "str"; expected "str": "int" |
| `.agents/hooks/tests/fixtures/task_workflow_harness.py` | `fixtures.task_workflow_harness` | `no-untyped-call` | 9 | Call to untyped function "dispatch" in typed context |
| `.agents/hooks/tests/fixtures/task_workflow_harness.py` | `fixtures.task_workflow_harness` | `no-untyped-def` | 9 | Function is missing a return type annotation |
| `.agents/hooks/tests/fixtures/workflow_writer_lease_worker.py` | `fixtures.workflow_writer_lease_worker` | `no-untyped-call` | 1 | Call to untyped function "for_repository" of "WriterLeaseRegistry" in typed context |
| `.agents/hooks/tests/test_auto_merge.py` | `test_auto_merge` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/hooks/tests/test_auto_merge.py` | `test_auto_merge` | `no-untyped-call` | 8 | Call to untyped function "binding" in typed context |
| `.agents/hooks/tests/test_auto_merge.py` | `test_auto_merge` | `no-untyped-def` | 13 | Function is missing a type annotation |
| `.agents/hooks/tests/test_auto_merge.py` | `test_auto_merge` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/hooks/tests/test_completion.py` | `test_completion` | `no-untyped-call` | 65 | Call to untyped function "publisher_follow_up" in typed context |
| `.agents/hooks/tests/test_completion.py` | `test_completion` | `no-untyped-def` | 28 | Function is missing a type annotation |
| `.agents/hooks/tests/test_continuation_runtime.py` | `test_continuation_runtime` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/hooks/tests/test_continuation_runtime.py` | `test_continuation_runtime` | `no-untyped-call` | 194 | Call to untyped function "git" in typed context |
| `.agents/hooks/tests/test_continuation_runtime.py` | `test_continuation_runtime` | `no-untyped-def` | 67 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_continuation_runtime.py` | `test_continuation_runtime` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/hooks/tests/test_delivery_runtime.py` | `test_delivery_runtime` | `dict-item` | 2 | Unpacked dict entry 0 has incompatible type "object"; expected "SupportsKeysAndGetItem[str, str]" |
| `.agents/hooks/tests/test_delivery_runtime.py` | `test_delivery_runtime` | `index` | 5 | Value of type "object" is not indexable |
| `.agents/hooks/tests/test_delivery_runtime.py` | `test_delivery_runtime` | `no-untyped-call` | 71 | Call to untyped function "resolve" in typed context |
| `.agents/hooks/tests/test_delivery_runtime.py` | `test_delivery_runtime` | `no-untyped-def` | 40 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_delivery_runtime.py` | `test_delivery_runtime` | `var-annotated` | 1 | Need type annotation for "configured" |
| `.agents/hooks/tests/test_docs_reachability.py` | `test_docs_reachability` | `no-untyped-call` | 91 | Call to untyped function "write" in typed context |
| `.agents/hooks/tests/test_docs_reachability.py` | `test_docs_reachability` | `no-untyped-def` | 24 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_goal_preflight.py` | `test_goal_preflight` | `no-untyped-call` | 13 | Call to untyped function "goal_evaluator_scopes" in typed context |
| `.agents/hooks/tests/test_goal_preflight.py` | `test_goal_preflight` | `no-untyped-def` | 15 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_handoff_transfer.py` | `test_handoff_transfer` | `assignment` | 1 | Incompatible types in assignment (expression has type "tuple[str, str, ... <12 more items>]", variable has type "tuple[str, str, ... <10 more items>]") |
| `.agents/hooks/tests/test_handoff_transfer.py` | `test_handoff_transfer` | `no-untyped-call` | 76 | Call to untyped function "write_goal" in typed context |
| `.agents/hooks/tests/test_handoff_transfer.py` | `test_handoff_transfer` | `no-untyped-def` | 24 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_hook_runtime.py` | `test_hook_runtime` | `attr-defined` | 1 | Module "hook_runtime" does not explicitly export attribute "tempfile" |
| `.agents/hooks/tests/test_hook_runtime.py` | `test_hook_runtime` | `no-untyped-call` | 25 | Call to untyped function "declared_plugin_root" in typed context |
| `.agents/hooks/tests/test_hook_runtime.py` | `test_hook_runtime` | `no-untyped-def` | 13 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_host_cli.py` | `test_host_cli` | `attr-defined` | 2 | Module "host_cli" does not explicitly export attribute "sys" |
| `.agents/hooks/tests/test_host_cli.py` | `test_host_cli` | `no-untyped-call` | 3 | Call to untyped function "plugin_inventory_command" in typed context |
| `.agents/hooks/tests/test_host_cli.py` | `test_host_cli` | `no-untyped-def` | 3 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_lane_tables.py` | `test_lane_tables` | `no-untyped-call` | 38 | Call to untyped function "table" in typed context |
| `.agents/hooks/tests/test_lane_tables.py` | `test_lane_tables` | `no-untyped-def` | 31 | Function is missing a type annotation |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `test_merge_cleanup_proof` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `test_merge_cleanup_proof` | `no-untyped-call` | 181 | Call to untyped function "git" in typed context |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `test_merge_cleanup_proof` | `no-untyped-def` | 34 | Function is missing a type annotation |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `test_merge_cleanup_proof` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/hooks/tests/test_merge_review_gate.py` | `test_merge_review_gate` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/hooks/tests/test_merge_review_gate.py` | `test_merge_review_gate` | `no-untyped-call` | 28 | Call to untyped function "load_gate" in typed context |
| `.agents/hooks/tests/test_merge_review_gate.py` | `test_merge_review_gate` | `no-untyped-def` | 37 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_merge_review_gate.py` | `test_merge_review_gate` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/hooks/tests/test_plan_graph.py` | `test_plan_graph` | `no-untyped-call` | 60 | Call to untyped function "write_ledger" in typed context |
| `.agents/hooks/tests/test_plan_graph.py` | `test_plan_graph` | `no-untyped-def` | 31 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_plan_workflows.py` | `test_plan_workflows` | `attr-defined` | 14 | "type[PlanWorkflowAcceptanceTests]" has no attribute "fixture" |
| `.agents/hooks/tests/test_plan_workflows.py` | `test_plan_workflows` | `no-untyped-call` | 24 | Call to untyped function "PlanWorkflowHarness" in typed context |
| `.agents/hooks/tests/test_plan_workflows.py` | `test_plan_workflows` | `no-untyped-def` | 21 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_pr_body.py` | `test_pr_body` | `attr-defined` | 1 | Module "workflow_ops" does not explicitly export attribute "delivery_runtime" |
| `.agents/hooks/tests/test_pr_body.py` | `test_pr_body` | `no-untyped-call` | 13 | Call to untyped function "unchecked_tasks" in typed context |
| `.agents/hooks/tests/test_pr_body.py` | `test_pr_body` | `no-untyped-def` | 8 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_problem_records.py` | `test_problem_records` | `no-untyped-call` | 29 | Call to untyped function "declaration" in typed context |
| `.agents/hooks/tests/test_problem_records.py` | `test_problem_records` | `no-untyped-def` | 11 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_process_standards.py` | `test_process_standards` | `attr-defined` | 7 | "type[ProcessStandardsTests]" has no attribute "root" |
| `.agents/hooks/tests/test_process_standards.py` | `test_process_standards` | `no-untyped-call` | 26 | Call to untyped function "corpus" in typed context |
| `.agents/hooks/tests/test_process_standards.py` | `test_process_standards` | `no-untyped-def` | 20 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_repository_configuration.py` | `test_repository_configuration` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/hooks/tests/test_repository_configuration.py` | `test_repository_configuration` | `no-untyped-call` | 24 | Call to untyped function "auto_merge_preference" in typed context |
| `.agents/hooks/tests/test_repository_configuration.py` | `test_repository_configuration` | `no-untyped-def` | 18 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_repository_configuration.py` | `test_repository_configuration` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/hooks/tests/test_repository_configuration.py` | `test_repository_configuration` | `var-annotated` | 2 | Need type annotation for "cases" |
| `.agents/hooks/tests/test_review_evidence.py` | `test_review_evidence` | `attr-defined` | 2 | Module "workflow_ops" does not explicitly export attribute "workflow_runtime" |
| `.agents/hooks/tests/test_review_evidence.py` | `test_review_evidence` | `no-untyped-call` | 63 | Call to untyped function "prepare_path" in typed context |
| `.agents/hooks/tests/test_review_evidence.py` | `test_review_evidence` | `no-untyped-def` | 21 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_review_evidence.py` | `test_review_evidence` | `var-annotated` | 1 | Need type annotation for "value" |
| `.agents/hooks/tests/test_review_workflows.py` | `test_review_workflows` | `attr-defined` | 5 | "type[ReviewWorkflowAcceptanceTests]" has no attribute "fixture" |
| `.agents/hooks/tests/test_review_workflows.py` | `test_review_workflows` | `no-untyped-call` | 25 | Call to untyped function "ReviewWorkflowHarness" in typed context |
| `.agents/hooks/tests/test_review_workflows.py` | `test_review_workflows` | `no-untyped-def` | 17 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_shell_profile_oracle.py` | `test_shell_profile_oracle` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/hooks/tests/test_shell_profile_oracle.py` | `test_shell_profile_oracle` | `no-untyped-call` | 2 | Call to untyped function "load_oracle" in typed context |
| `.agents/hooks/tests/test_shell_profile_oracle.py` | `test_shell_profile_oracle` | `no-untyped-def` | 8 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_shell_profile_oracle.py` | `test_shell_profile_oracle` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/hooks/tests/test_task_workflows.py` | `test_task_workflows` | `attr-defined` | 9 | "type[TaskWorkflowAcceptanceTests]" has no attribute "fixture" |
| `.agents/hooks/tests/test_task_workflows.py` | `test_task_workflows` | `no-untyped-call` | 20 | Call to untyped function "WorkflowContract" in typed context |
| `.agents/hooks/tests/test_task_workflows.py` | `test_task_workflows` | `no-untyped-def` | 14 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_workflow_adoption.py` | `test_workflow_adoption` | `attr-defined` | 15 | "type[WorkflowAdoptionTests]" has no attribute "contract" |
| `.agents/hooks/tests/test_workflow_adoption.py` | `test_workflow_adoption` | `no-untyped-call` | 2 | Call to untyped function "WorkflowContract" in typed context |
| `.agents/hooks/tests/test_workflow_adoption.py` | `test_workflow_adoption` | `no-untyped-def` | 7 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_workflow_contracts.py` | `test_workflow_contracts` | `arg-type` | 1 | Argument after ** must be a mapping, not "object" |
| `.agents/hooks/tests/test_workflow_contracts.py` | `test_workflow_contracts` | `attr-defined` | 39 | "type[WorkflowContractTests]" has no attribute "contract" |
| `.agents/hooks/tests/test_workflow_contracts.py` | `test_workflow_contracts` | `no-untyped-call` | 177 | Call to untyped function "WorkflowContract" in typed context |
| `.agents/hooks/tests/test_workflow_contracts.py` | `test_workflow_contracts` | `no-untyped-def` | 92 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_workflow_contracts.py` | `test_workflow_contracts` | `var-annotated` | 1 | Need type annotation for "observed_changes" (hint: "observed_changes: set[<type>] = ...") |
| `.agents/hooks/tests/test_workflow_ops.py` | `test_workflow_ops` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/hooks/tests/test_workflow_ops.py` | `test_workflow_ops` | `attr-defined` | 7 | "type[RepositoryFixture]" has no attribute "_baseline_temp" |
| `.agents/hooks/tests/test_workflow_ops.py` | `test_workflow_ops` | `import-not-found` | 1 | Cannot find implementation or library stub for module named "fake_cli" |
| `.agents/hooks/tests/test_workflow_ops.py` | `test_workflow_ops` | `no-redef` | 1 | Name "test_cleanup_validates_redirected_cache_ancestor_before_absent_bundle_probe" already defined on line 778 |
| `.agents/hooks/tests/test_workflow_ops.py` | `test_workflow_ops` | `no-untyped-call` | 106 | Call to untyped function "load_operations" in typed context |
| `.agents/hooks/tests/test_workflow_ops.py` | `test_workflow_ops` | `no-untyped-def` | 125 | Function is missing a return type annotation |
| `.agents/hooks/tests/test_workflow_ops.py` | `test_workflow_ops` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/hooks/tests/test_workflow_ops.py` | `test_workflow_ops` | `var-annotated` | 4 | Need type annotation for "emitted" (hint: "emitted: list[<type>] = ...") |
| `.agents/hooks/tests/test_worktree_sweep.py` | `test_worktree_sweep` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.agents/hooks/tests/test_worktree_sweep.py` | `test_worktree_sweep` | `import-not-found` | 1 | Cannot find implementation or library stub for module named "fake_cli" |
| `.agents/hooks/tests/test_worktree_sweep.py` | `test_worktree_sweep` | `no-untyped-call` | 16 | Call to untyped function "git" in typed context |
| `.agents/hooks/tests/test_worktree_sweep.py` | `test_worktree_sweep` | `no-untyped-def` | 26 | Function is missing a type annotation |
| `.agents/hooks/tests/test_worktree_sweep.py` | `test_worktree_sweep` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `arg-type` | 5 | Argument 1 to "Path" has incompatible type "Any \| None"; expected "str \| PathLike[str]" |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `assignment` | 1 | Incompatible types in assignment (expression has type "Declaration \| None", variable has type "tuple[Any, Declaration] \| None") |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `attr-defined` | 1 | "tuple[Any, Declaration]" has no attribute "orphaned" |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `misc` | 1 | Assignment to variable "error" outside except: block |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `no-any-return` | 1 | Returning Any from function declared to return "SelectionResult" |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `no-untyped-call` | 231 | Call to untyped function "_text" in typed context |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `no-untyped-def` | 64 | Function is missing a type annotation |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `type-arg` | 1 | Missing type arguments for generic type "list" |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `unreachable` | 9 | Right operand of "and" is never evaluated |
| `.agents/hooks/tier_gate.py` | `tier_gate` | `var-annotated` | 9 | Need type annotation for "definitions" (hint: "definitions: dict[<type>, <type>] = ...") |
| `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py` | `host_coverage` | `no-untyped-call` | 8 | Call to untyped function "is_text" in typed context |
| `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py` | `host_coverage` | `no-untyped-def` | 7 | Function is missing a type annotation |
| `.agents/workflow/contract/plan-artifacts/scripts/host_coverage.py` | `host_coverage` | `var-annotated` | 1 | Need type annotation for "records" (hint: "records: list[<type>] = ...") |
| `.agents/workflow/utility/status/scripts/status.py` | `status` | `no-untyped-call` | 19 | Call to untyped function "words" in typed context |
| `.agents/workflow/utility/status/scripts/status.py` | `status` | `no-untyped-def` | 13 | Function is missing a type annotation |
| `.agents/workflow/utility/status/scripts/status.py` | `status` | `var-annotated` | 4 | Need type annotation for "skipped" (hint: "skipped: list[<type>] = ...") |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `transfer` | `attr-defined` | 5 | Module has no attribute "flock" |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `transfer` | `no-untyped-call` | 35 | Call to untyped function "absolute" in typed context |
| `.agents/workflow/workflow/handoff/scripts/transfer.py` | `transfer` | `no-untyped-def` | 17 | Function is missing a type annotation |
| `.agents/workflows/auto_merge.py` | `auto_merge` | `attr-defined` | 2 | Module "workflow_ops" does not explicitly export attribute "review_evidence" |
| `.agents/workflows/auto_merge.py` | `auto_merge` | `no-untyped-call` | 30 | Call to untyped function "binding_from_artifact" in typed context |
| `.agents/workflows/auto_merge.py` | `auto_merge` | `no-untyped-def` | 8 | Function is missing a type annotation |
| `.agents/workflows/completion.py` | `completion` | `no-untyped-call` | 25 | Call to untyped function "resolve_path" in typed context |
| `.agents/workflows/completion.py` | `completion` | `no-untyped-def` | 15 | Function is missing a type annotation |
| `.agents/workflows/delivery_policy.py` | `delivery_policy` | `no-untyped-call` | 2 | Call to untyped function "validate" in typed context |
| `.agents/workflows/delivery_policy.py` | `delivery_policy` | `no-untyped-def` | 4 | Function is missing a return type annotation |
| `.agents/workflows/delivery_runtime.py` | `delivery_runtime` | `no-untyped-call` | 36 | Call to untyped function "validate" in typed context |
| `.agents/workflows/delivery_runtime.py` | `delivery_runtime` | `no-untyped-def` | 20 | Function is missing a type annotation |
| `.agents/workflows/host_runtime.py` | `host_runtime` | `attr-defined` | 5 | Module has no attribute "flock" |
| `.agents/workflows/host_runtime.py` | `host_runtime` | `no-untyped-call` | 76 | Call to untyped function "RepositoryWriterLock" in typed context |
| `.agents/workflows/host_runtime.py` | `host_runtime` | `no-untyped-def` | 31 | Function is missing a type annotation |
| `.agents/workflows/host_runtime.py` | `host_runtime` | `var-annotated` | 1 | Need type annotation for "repositories" |
| `.agents/workflows/hosts/smoke.py` | `smoke` | `no-untyped-call` | 3 | Call to untyped function "HostAdapterRegistry" in typed context |
| `.agents/workflows/hosts/smoke.py` | `smoke` | `no-untyped-def` | 1 | Function is missing a return type annotation |
| `.agents/workflows/pr_body.py` | `pr_body` | `no-untyped-call` | 2 | Call to untyped function "validate_pr_body" in typed context |
| `.agents/workflows/pr_body.py` | `pr_body` | `no-untyped-def` | 3 | Function is missing a type annotation |
| `.agents/workflows/pr_body.py` | `pr_body` | `union-attr` | 1 | Item "None" of "Match[str] \| None" has no attribute "group" |
| `.agents/workflows/pr_body.py` | `pr_body` | `var-annotated` | 2 | Need type annotation for "list_indents" (hint: "list_indents: list[<type>] = ...") |
| `.agents/workflows/review_evidence.py` | `review_evidence` | `no-untyped-call` | 16 | Call to untyped function "reject_redirects" in typed context |
| `.agents/workflows/review_evidence.py` | `review_evidence` | `no-untyped-def` | 10 | Function is missing a type annotation |
| `.agents/workflows/verify.py` | `verify` | `no-untyped-call` | 4 | Call to untyped function "WorkflowContract" in typed context |
| `.agents/workflows/verify.py` | `verify` | `no-untyped-def` | 1 | Function is missing a return type annotation |
| `.agents/workflows/workflow_ops.py` | `workflow_ops` | `dict-item` | 2 | Dict entry 0 has incompatible type "str": "int \| None"; expected "str": "None" |
| `.agents/workflows/workflow_ops.py` | `workflow_ops` | `index` | 1 | Value of type "dict[str, Any] \| None" is not indexable |
| `.agents/workflows/workflow_ops.py` | `workflow_ops` | `no-untyped-call` | 300 | Call to untyped function "utc_now" in typed context |
| `.agents/workflows/workflow_ops.py` | `workflow_ops` | `no-untyped-def` | 100 | Function is missing a return type annotation |
| `.agents/workflows/workflow_ops.py` | `workflow_ops` | `union-attr` | 1 | Item "None" of "str \| Any \| None" has no attribute "lower" |
| `.agents/workflows/workflow_ops.py` | `workflow_ops` | `unreachable` | 1 | Statement is unreachable |
| `.agents/workflows/workflow_runtime.py` | `workflow_runtime` | `no-untyped-call` | 73 | Call to untyped function "_validate" in typed context |
| `.agents/workflows/workflow_runtime.py` | `workflow_runtime` | `no-untyped-def` | 37 | Function is missing a return type annotation |
| `.agents/workflows/workflow_runtime.py` | `workflow_runtime` | `var-annotated` | 1 | Need type annotation for "loaded" (hint: "loaded: dict[<type>, <type>] = ...") |
| `.codex/runtime/continuation/continuation_runtime.py` | `continuation_runtime` | `attr-defined` | 11 | Module has no attribute "flock" |
| `.codex/runtime/continuation/continuation_runtime.py` | `continuation_runtime` | `no-untyped-call` | 85 | Call to untyped function "runtime_paths" in typed context |
| `.codex/runtime/continuation/continuation_runtime.py` | `continuation_runtime` | `no-untyped-def` | 28 | Function is missing a return type annotation |
| `.codex/runtime/continuation/continuation_scheduler.py` | `continuation_scheduler` | `attr-defined` | 7 | Module has no attribute "_get_candidate_names" |
| `.codex/runtime/continuation/continuation_scheduler.py` | `continuation_scheduler` | `no-untyped-call` | 87 | Call to untyped function "reject_unsafe" in typed context |
| `.codex/runtime/continuation/continuation_scheduler.py` | `continuation_scheduler` | `no-untyped-def` | 48 | Function is missing a type annotation |
| `.codex/runtime/continuation/continuation_scheduler.py` | `continuation_scheduler` | `var-annotated` | 2 | Need type annotation for "expected" (hint: "expected: dict[<type>, <type>] = ...") |
| `.codex/runtime/continuation/delivery_continuation.py` | `delivery_continuation` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `.codex/runtime/continuation/delivery_continuation.py` | `delivery_continuation` | `no-untyped-call` | 32 | Call to untyped function "package_root" in typed context |
| `.codex/runtime/continuation/delivery_continuation.py` | `delivery_continuation` | `no-untyped-def` | 20 | Function is missing a return type annotation |
| `.codex/runtime/continuation/delivery_continuation.py` | `delivery_continuation` | `union-attr` | 3 | Item "None" of "ModuleSpec \| None" has no attribute "name" |
| `scripts/ci_native_acceptance.py` | `scripts.ci_native_acceptance` | `arg-type` | 1 | Argument 1 to "extractfile" of "TarFile" has incompatible type "ZipInfo"; expected "str \| TarInfo" |
| `scripts/ci_native_acceptance.py` | `scripts.ci_native_acceptance` | `import-not-found` | 1 | Cannot find implementation or library stub for module named "native_host_acceptance" |
| `scripts/ci_native_acceptance.py` | `scripts.ci_native_acceptance` | `misc` | 1 | List comprehension has incompatible type List[TarInfo]; expected List[ZipInfo] |
| `scripts/ci_native_acceptance.py` | `scripts.ci_native_acceptance` | `no-untyped-call` | 13 | Call to untyped function "platform_assets" in typed context |
| `scripts/ci_native_acceptance.py` | `scripts.ci_native_acceptance` | `no-untyped-def` | 7 | Function is missing a type annotation |
| `scripts/ci_native_acceptance.py` | `scripts.ci_native_acceptance` | `union-attr` | 2 | Item "None" of "IO[bytes] \| None" has no attribute "__enter__" |
| `scripts/ci_selection.py` | `scripts.ci_selection` | `no-untyped-call` | 24 | Call to untyped function "plan" in typed context |
| `scripts/ci_selection.py` | `scripts.ci_selection` | `no-untyped-def` | 11 | Function is missing a type annotation |
| `scripts/native_host_acceptance.py` | `scripts.native_host_acceptance` | `arg-type` | 1 | Argument 1 to "Path" has incompatible type "Any \| None"; expected "str \| PathLike[str]" |
| `scripts/native_host_acceptance.py` | `scripts.native_host_acceptance` | `no-untyped-call` | 75 | Call to untyped function "installed_identities" in typed context |
| `scripts/native_host_acceptance.py` | `scripts.native_host_acceptance` | `no-untyped-def` | 44 | Function is missing a type annotation |
| `scripts/native_host_acceptance.py` | `scripts.native_host_acceptance` | `type-arg` | 1 | Missing type arguments for generic type "dict" |
| `scripts/native_host_acceptance.py` | `scripts.native_host_acceptance` | `union-attr` | 3 | Item "None" of "IO[str] \| None" has no attribute "write" |
| `scripts/native_host_acceptance.py` | `scripts.native_host_acceptance` | `var-annotated` | 6 | Need type annotation for "messages" |
| `scripts/runtime_sources.py` | `scripts.runtime_sources` | `type-arg` | 3 | Missing type arguments for generic type "dict" |
| `scripts/sync_harness_manifests.py` | `scripts.sync_harness_manifests` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `scripts/sync_harness_manifests.py` | `scripts.sync_harness_manifests` | `no-untyped-def` | 1 | Function is missing a return type annotation |
| `scripts/sync_harness_manifests.py` | `scripts.sync_harness_manifests` | `type-arg` | 4 | Missing type arguments for generic type "dict" |
| `scripts/sync_harness_manifests.py` | `scripts.sync_harness_manifests` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `scripts/sync_plugin_packages.py` | `scripts.sync_plugin_packages` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `scripts/sync_plugin_packages.py` | `scripts.sync_plugin_packages` | `assignment` | 1 | Incompatible types in assignment (expression has type "PurePosixPath", variable has type "str") |
| `scripts/sync_plugin_packages.py` | `scripts.sync_plugin_packages` | `attr-defined` | 1 | "str" has no attribute "parts" |
| `scripts/sync_plugin_packages.py` | `scripts.sync_plugin_packages` | `no-any-return` | 1 | Returning Any from function declared to return "str" |
| `scripts/sync_plugin_packages.py` | `scripts.sync_plugin_packages` | `no-untyped-def` | 10 | Function is missing a return type annotation |
| `scripts/sync_plugin_packages.py` | `scripts.sync_plugin_packages` | `type-arg` | 19 | Missing type arguments for generic type "dict" |
| `scripts/sync_plugin_packages.py` | `scripts.sync_plugin_packages` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `scripts/sync_plugin_packages.py` | `scripts.sync_plugin_packages` | `var-annotated` | 1 | Need type annotation for "EMPTY_EXTERNAL_DEPENDENCIES" |
| `scripts/update_plugin_digests.py` | `scripts.update_plugin_digests` | `arg-type` | 2 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `scripts/update_plugin_digests.py` | `scripts.update_plugin_digests` | `union-attr` | 4 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/fixtures/fake_claude.py` | `tests.fixtures.fake_claude` | `no-untyped-call` | 7 | Call to untyped function "git" in typed context |
| `tests/fixtures/fake_claude.py` | `tests.fixtures.fake_claude` | `no-untyped-def` | 4 | Function is missing a type annotation |
| `tests/fixtures/plugin_autoupdate_208cc302.py` | `tests.fixtures.plugin_autoupdate_208cc302` | `no-untyped-call` | 1 | Call to untyped function "packaged_copies" in typed context |
| `tests/fixtures/plugin_autoupdate_208cc302.py` | `tests.fixtures.plugin_autoupdate_208cc302` | `no-untyped-def` | 1 | Function is missing a type annotation |
| `tests/fixtures/plugin_autoupdate_208cc302.py` | `tests.fixtures.plugin_autoupdate_208cc302` | `type-arg` | 1 | Missing type arguments for generic type "dict" |
| `tests/native_plugin_inventory.py` | `tests.native_plugin_inventory` | `no-untyped-def` | 1 | Function is missing a type annotation |
| `tests/test_agent_files.py` | `tests.test_agent_files` | `no-untyped-def` | 2 | Function is missing a return type annotation |
| `tests/test_background_processes.py` | `tests.test_background_processes` | `var-annotated` | 1 | Need type annotation for "imported" (hint: "imported: set[<type>] = ...") |
| `tests/test_check_generated_paths.py` | `tests.test_check_generated_paths` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_check_generated_paths.py` | `tests.test_check_generated_paths` | `no-untyped-call` | 43 | Call to untyped function "git" in typed context |
| `tests/test_check_generated_paths.py` | `tests.test_check_generated_paths` | `no-untyped-def` | 12 | Function is missing a type annotation |
| `tests/test_check_generated_paths.py` | `tests.test_check_generated_paths` | `union-attr` | 3 | Item "None" of "ModuleSpec \| None" has no attribute "name" |
| `tests/test_check_tier_payload.py` | `tests.test_check_tier_payload` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_check_tier_payload.py` | `tests.test_check_tier_payload` | `no-untyped-call` | 30 | Call to untyped function "load_module" in typed context |
| `tests/test_check_tier_payload.py` | `tests.test_check_tier_payload` | `no-untyped-def` | 19 | Function is missing a return type annotation |
| `tests/test_check_tier_payload.py` | `tests.test_check_tier_payload` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_ci_native_acceptance.py` | `tests.test_ci_native_acceptance` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_ci_native_acceptance.py` | `tests.test_ci_native_acceptance` | `no-untyped-call` | 2 | Call to untyped function "archive" in typed context |
| `tests/test_ci_native_acceptance.py` | `tests.test_ci_native_acceptance` | `no-untyped-def` | 6 | Function is missing a type annotation |
| `tests/test_ci_native_acceptance.py` | `tests.test_ci_native_acceptance` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_ci_selection.py` | `tests.test_ci_selection` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_ci_selection.py` | `tests.test_ci_selection` | `index` | 4 | Unsupported target for indexed assignment ("Collection[str]") |
| `tests/test_ci_selection.py` | `tests.test_ci_selection` | `list-item` | 1 | List item 0 has incompatible type "dict[str, str]"; expected "str" |
| `tests/test_ci_selection.py` | `tests.test_ci_selection` | `no-untyped-call` | 38 | Call to untyped function "results" of "ClassificationTests" in typed context |
| `tests/test_ci_selection.py` | `tests.test_ci_selection` | `no-untyped-def` | 30 | Function is missing a return type annotation |
| `tests/test_ci_selection.py` | `tests.test_ci_selection` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_codex_hook_snapshot.py` | `tests.test_codex_hook_snapshot` | `arg-type` | 2 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_codex_hook_snapshot.py` | `tests.test_codex_hook_snapshot` | `no-redef` | 1 | Name "test_startup_snapshot_loader_keeps_an_existing_session_callable_after_live_loader_changes" already defined on line 275 |
| `tests/test_codex_hook_snapshot.py` | `tests.test_codex_hook_snapshot` | `no-untyped-call` | 1 | Call to untyped function (unknown) in typed context |
| `tests/test_codex_hook_snapshot.py` | `tests.test_codex_hook_snapshot` | `no-untyped-def` | 15 | Function is missing a type annotation |
| `tests/test_codex_hook_snapshot.py` | `tests.test_codex_hook_snapshot` | `union-attr` | 6 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_codex_startup_dispatch.py` | `tests.test_codex_startup_dispatch` | `no-untyped-call` | 1 | Call to untyped function "manifest" in typed context |
| `tests/test_codex_startup_dispatch.py` | `tests.test_codex_startup_dispatch` | `no-untyped-def` | 3 | Function is missing a type annotation |
| `tests/test_codex_windows_hook_commands.py` | `tests.test_codex_windows_hook_commands` | `no-untyped-def` | 1 | Function is missing a return type annotation |
| `tests/test_company_skill_replacement.py` | `tests.test_company_skill_replacement` | `no-untyped-call` | 6 | Call to untyped function "remote" in typed context |
| `tests/test_company_skill_replacement.py` | `tests.test_company_skill_replacement` | `no-untyped-def` | 6 | Function is missing a return type annotation |
| `tests/test_delivery_continuation.py` | `tests.test_delivery_continuation` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_delivery_continuation.py` | `tests.test_delivery_continuation` | `func-returns-value` | 1 | "append" of "list" does not return a value (it only ever returns None) |
| `tests/test_delivery_continuation.py` | `tests.test_delivery_continuation` | `misc` | 2 | Class cannot subclass "SchedulerTransport" (has type "Any") |
| `tests/test_delivery_continuation.py` | `tests.test_delivery_continuation` | `name-defined` | 2 | Name "scheduler.SchedulerTransport" is not defined |
| `tests/test_delivery_continuation.py` | `tests.test_delivery_continuation` | `no-untyped-call` | 153 | Call to untyped function "load" in typed context |
| `tests/test_delivery_continuation.py` | `tests.test_delivery_continuation` | `no-untyped-def` | 62 | Function is missing a type annotation |
| `tests/test_delivery_continuation.py` | `tests.test_delivery_continuation` | `operator` | 1 | Unsupported operand types for + ("str" and "None") |
| `tests/test_delivery_continuation.py` | `tests.test_delivery_continuation` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_employer_tiers.py` | `tests.test_employer_tiers` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_employer_tiers.py` | `tests.test_employer_tiers` | `no-untyped-call` | 47 | Call to untyped function "load" in typed context |
| `tests/test_employer_tiers.py` | `tests.test_employer_tiers` | `no-untyped-def` | 24 | Function is missing a type annotation |
| `tests/test_employer_tiers.py` | `tests.test_employer_tiers` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_employer_tiers.py` | `tests.test_employer_tiers` | `var-annotated` | 4 | Need type annotation for "cases" |
| `tests/test_guide_build.py` | `tests.test_guide_build` | `no-untyped-call` | 32 | Call to untyped function "git" in typed context |
| `tests/test_guide_build.py` | `tests.test_guide_build` | `no-untyped-def` | 42 | Function is missing a type annotation |
| `tests/test_harness_manifests.py` | `tests.test_harness_manifests` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_harness_manifests.py` | `tests.test_harness_manifests` | `import-not-found` | 2 | Cannot find implementation or library stub for module named "harness_permissions" |
| `tests/test_harness_manifests.py` | `tests.test_harness_manifests` | `no-untyped-call` | 13 | Call to untyped function "requires" in typed context |
| `tests/test_harness_manifests.py` | `tests.test_harness_manifests` | `no-untyped-def` | 21 | Function is missing a type annotation |
| `tests/test_harness_manifests.py` | `tests.test_harness_manifests` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_harness_manifests.py` | `tests.test_harness_manifests` | `var-annotated` | 1 | Need type annotation for "checks" (hint: "checks: list[<type>] = ...") |
| `tests/test_hook_contract.py` | `tests.test_hook_contract` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_hook_contract.py` | `tests.test_hook_contract` | `attr-defined` | 17 | "type[HookContractTests]" has no attribute "config" |
| `tests/test_hook_contract.py` | `tests.test_hook_contract` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_hook_launch_budget.py` | `tests.test_hook_launch_budget` | `attr-defined` | 24 | "type[HookBudgetUnderLoad]" has no attribute "temp" |
| `tests/test_hook_launch_budget.py` | `tests.test_hook_launch_budget` | `misc` | 1 | Generator has incompatible item type "int"; expected "bool" |
| `tests/test_hook_launch_budget.py` | `tests.test_hook_launch_budget` | `no-untyped-call` | 7 | Call to untyped function "manifest" in typed context |
| `tests/test_hook_launch_budget.py` | `tests.test_hook_launch_budget` | `no-untyped-def` | 10 | Function is missing a type annotation |
| `tests/test_host_coverage.py` | `tests.test_host_coverage` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_host_coverage.py` | `tests.test_host_coverage` | `attr-defined` | 1 | "object" has no attribute "__iter__"; maybe "__dir__" or "__str__"? (not iterable) |
| `tests/test_host_coverage.py` | `tests.test_host_coverage` | `no-untyped-call` | 6 | Call to untyped function "record" in typed context |
| `tests/test_host_coverage.py` | `tests.test_host_coverage` | `no-untyped-def` | 11 | Function is missing a type annotation |
| `tests/test_host_coverage.py` | `tests.test_host_coverage` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_native_host_acceptance.py` | `tests.test_native_host_acceptance` | `arg-type` | 1 | Argument 1 to "Path" has incompatible type "object"; expected "str \| PathLike[str]" |
| `tests/test_native_host_acceptance.py` | `tests.test_native_host_acceptance` | `type-arg` | 1 | Missing type arguments for generic type "dict" |
| `tests/test_plan_artifacts.py` | `tests.test_plan_artifacts` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_plan_artifacts.py` | `tests.test_plan_artifacts` | `no-untyped-def` | 2 | Function is missing a return type annotation |
| `tests/test_plan_artifacts.py` | `tests.test_plan_artifacts` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_plugin_update.py` | `tests.test_plugin_update` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_plugin_update.py` | `tests.test_plugin_update` | `no-untyped-def` | 1 | Function is missing a return type annotation |
| `tests/test_plugin_update.py` | `tests.test_plugin_update` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_project_facts.py` | `tests.test_project_facts` | `no-untyped-call` | 136 | Call to untyped function "write" in typed context |
| `tests/test_project_facts.py` | `tests.test_project_facts` | `no-untyped-def` | 30 | Function is missing a return type annotation |
| `tests/test_project_facts.py` | `tests.test_project_facts` | `var-annotated` | 2 | Need type annotation for "invalid" |
| `tests/test_publisher_dependencies.py` | `tests.test_publisher_dependencies` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_publisher_dependencies.py` | `tests.test_publisher_dependencies` | `no-untyped-call` | 2 | Call to untyped function "roster" in typed context |
| `tests/test_publisher_dependencies.py` | `tests.test_publisher_dependencies` | `no-untyped-def` | 3 | Function is missing a return type annotation |
| `tests/test_publisher_dependencies.py` | `tests.test_publisher_dependencies` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_remote_host_tiers.py` | `tests.test_remote_host_tiers` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_remote_host_tiers.py` | `tests.test_remote_host_tiers` | `assignment` | 1 | Incompatible types in assignment (expression has type "list[Never] \| dict[Never, Never] \| None", variable has type "str") |
| `tests/test_remote_host_tiers.py` | `tests.test_remote_host_tiers` | `no-untyped-call` | 14 | Call to untyped function "origin" in typed context |
| `tests/test_remote_host_tiers.py` | `tests.test_remote_host_tiers` | `no-untyped-def` | 9 | Function is missing a return type annotation |
| `tests/test_remote_host_tiers.py` | `tests.test_remote_host_tiers` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_repository_permissions.py` | `tests.test_repository_permissions` | `no-untyped-call` | 12 | Call to untyped function "verify_job_block" in typed context |
| `tests/test_repository_permissions.py` | `tests.test_repository_permissions` | `no-untyped-def` | 11 | Function is missing a type annotation |
| `tests/test_review_native_layer.py` | `tests.test_review_native_layer` | `no-untyped-call` | 22 | Call to untyped function "body" in typed context |
| `tests/test_review_native_layer.py` | `tests.test_review_native_layer` | `no-untyped-def` | 17 | Function is missing a type annotation |
| `tests/test_review_rules.py` | `tests.test_review_rules` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_review_rules.py` | `tests.test_review_rules` | `no-untyped-call` | 23 | Call to untyped function "selection" in typed context |
| `tests/test_review_rules.py` | `tests.test_review_rules` | `no-untyped-def` | 17 | Function is missing a return type annotation |
| `tests/test_review_rules.py` | `tests.test_review_rules` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_review_rules.py` | `tests.test_review_rules` | `var-annotated` | 1 | Need type annotation for "document" |
| `tests/test_runtime_sources.py` | `tests.test_runtime_sources` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_runtime_sources.py` | `tests.test_runtime_sources` | `index` | 7 | Value of type "object" is not indexable |
| `tests/test_runtime_sources.py` | `tests.test_runtime_sources` | `no-untyped-call` | 21 | Call to untyped function "save" in typed context |
| `tests/test_runtime_sources.py` | `tests.test_runtime_sources` | `no-untyped-def` | 19 | Function is missing a return type annotation |
| `tests/test_runtime_sources.py` | `tests.test_runtime_sources` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_source_layout.py` | `tests.test_source_layout` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_source_layout.py` | `tests.test_source_layout` | `no-untyped-call` | 7 | Call to untyped function "body" in typed context |
| `tests/test_source_layout.py` | `tests.test_source_layout` | `no-untyped-def` | 27 | Function is missing a type annotation |
| `tests/test_source_layout.py` | `tests.test_source_layout` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_stack_tiers.py` | `tests.test_stack_tiers` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_stack_tiers.py` | `tests.test_stack_tiers` | `no-untyped-call` | 18 | Call to untyped function "load_module" in typed context |
| `tests/test_stack_tiers.py` | `tests.test_stack_tiers` | `no-untyped-def` | 38 | Function is missing a return type annotation |
| `tests/test_stack_tiers.py` | `tests.test_stack_tiers` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_standards_context.py` | `tests.test_standards_context` | `no-untyped-call` | 24 | Call to untyped function "write" in typed context |
| `tests/test_standards_context.py` | `tests.test_standards_context` | `no-untyped-def` | 14 | Function is missing a return type annotation |
| `tests/test_task_routing.py` | `tests.test_task_routing` | `no-untyped-call` | 5 | Call to untyped function "manifest" in typed context |
| `tests/test_task_routing.py` | `tests.test_task_routing` | `no-untyped-def` | 8 | Function is missing a type annotation |
| `tests/test_tier_predicates.py` | `tests.test_tier_predicates` | `arg-type` | 1 | Argument 1 to "module_from_spec" has incompatible type "ModuleSpec \| None"; expected "ModuleSpec" |
| `tests/test_tier_predicates.py` | `tests.test_tier_predicates` | `no-untyped-call` | 7 | Call to untyped function "load" in typed context |
| `tests/test_tier_predicates.py` | `tests.test_tier_predicates` | `no-untyped-def` | 17 | Function is missing a type annotation |
| `tests/test_tier_predicates.py` | `tests.test_tier_predicates` | `union-attr` | 2 | Item "None" of "ModuleSpec \| None" has no attribute "loader" |
| `tests/test_tier_predicates.py` | `tests.test_tier_predicates` | `var-annotated` | 5 | Need type annotation for "invalid" |
| `tests/test_workflow_session_hooks.py` | `tests.test_workflow_session_hooks` | `no-untyped-call` | 1 | Call to untyped function "manifest" in typed context |
| `tests/test_workflow_session_hooks.py` | `tests.test_workflow_session_hooks` | `no-untyped-def` | 3 | Function is missing a type annotation |
| `tests/test_workflow_status.py` | `tests.test_workflow_status` | `arg-type` | 2 | Argument 1 to "Path" has incompatible type "str \| None"; expected "str \| PathLike[str]" |
| `tests/test_workflow_status.py` | `tests.test_workflow_status` | `import-not-found` | 1 | Cannot find implementation or library stub for module named "fake_cli" |
| `tests/test_workflow_status.py` | `tests.test_workflow_status` | `no-untyped-call` | 163 | Call to untyped function "repo" in typed context |
| `tests/test_workflow_status.py` | `tests.test_workflow_status` | `no-untyped-def` | 65 | Function is missing a type annotation |

## Python source checker

Exact legacy file/rule exceptions preserve existing runtime behavior during rollout. Remove each exception after its indicated repair. The checker rejects stale and wildcard exceptions.

| File | Rule | Existing count | Required repair |
| --- | --- | ---: | --- |
| `.agents/engineering/utility/guide-build/template/build.py` | `PY001` | 3 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/engineering/utility/review/scripts/review_rules.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/engineering/workflow/merge/scripts/cleanup_proof.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/engineering/workflow/merge/scripts/worktree_sweep.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/hooks/hook_runtime.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/host_cli.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/installed_skills.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/project_facts.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/hooks/tests/fixtures/continuation_fixture.py` | `PY009` | 9 | Legacy import-time execution or explicit subprocess fixture; move runtime I/O into the entry point and isolate fixture setup. |
| `.agents/hooks/tests/fixtures/continuation_fixture.py` | `PY016` | 4 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/fixtures/continuation_runtime_fixture.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/fixtures/fake_cli.py` | `PY016` | 4 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/fixtures/lane_expectations.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/hooks/tests/fixtures/workflow_writer_lease_worker.py` | `PY009` | 1 | Legacy import-time execution or explicit subprocess fixture; move runtime I/O into the entry point and isolate fixture setup. |
| `.agents/hooks/tests/fixtures/workflow_writer_lease_worker.py` | `PY016` | 4 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/fixtures/workflow_writer_lease_worker.py` | `PY017` | 3 | Legacy direct test clock read; inject a fixed clock. |
| `.agents/hooks/tests/test_completion.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/test_continuation_runtime.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/test_continuation_runtime.py` | `PY017` | 7 | Legacy direct test clock read; inject a fixed clock. |
| `.agents/hooks/tests/test_goal_preflight.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/test_hook_runtime.py` | `PY016` | 5 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/test_hook_runtime.py` | `PY017` | 4 | Legacy direct test clock read; inject a fixed clock. |
| `.agents/hooks/tests/test_lane_tables.py` | `PY001` | 2 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/hooks/tests/test_merge_cleanup_proof.py` | `PY016` | 4 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/test_process_standards.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/hooks/tests/test_workflow_adoption.py` | `PY001` | 2 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/hooks/tests/test_workflow_contracts.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/hooks/tests/test_workflow_contracts.py` | `PY016` | 3 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tests/test_workflow_contracts.py` | `PY017` | 2 | Legacy direct test clock read; inject a fixed clock. |
| `.agents/hooks/tests/test_workflow_ops.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/hooks/tier_gate.py` | `PY001` | 23 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/hooks/tier_gate.py` | `PY016` | 8 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/workflow/utility/status/scripts/status.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/workflow/utility/status/scripts/status.py` | `PY016` | 3 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/workflows/completion.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/workflows/host_runtime.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/workflows/host_runtime.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/workflows/workflow_ops.py` | `PY001` | 2 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.agents/workflows/workflow_ops.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.agents/workflows/workflow_runtime.py` | `PY001` | 3 | Legacy comprehension traversal; split the nested generators into named loops. |
| `.codex/runtime/continuation/continuation_runtime.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.codex/runtime/continuation/continuation_scheduler.py` | `PY016` | 4 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `.codex/runtime/continuation/delivery_continuation.py` | `PY016` | 3 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `packages/tj-base/src/tj_base/startup.py` | `PY011` | 1 | Legacy exception hierarchy; consolidate under the owning package error root. |
| `scripts/check_generated_paths.py` | `PY001` | 2 | Legacy comprehension traversal; split the nested generators into named loops. |
| `scripts/native_host_acceptance.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `scripts/native_host_acceptance.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `scripts/sync_plugin_packages.py` | `PY001` | 5 | Legacy comprehension traversal; split the nested generators into named loops. |
| `tests/fixtures/fake_claude.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/fixtures/fake_claude.py` | `PY017` | 3 | Legacy direct test clock read; inject a fixed clock. |
| `tests/fixtures/plugin_autoupdate_208cc302.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `tests/fixtures/plugin_cli.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `tests/fixtures/plugin_cli.py` | `PY009` | 1 | Legacy import-time execution or explicit subprocess fixture; move runtime I/O into the entry point and isolate fixture setup. |
| `tests/fixtures/plugin_cli.py` | `PY016` | 4 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/fixtures/setup_probe.py` | `PY009` | 1 | Legacy import-time execution or explicit subprocess fixture; move runtime I/O into the entry point and isolate fixture setup. |
| `tests/fixtures/setup_probe.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_agent_files.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_background_processes.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `tests/test_ci_selection.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_codex_hook_snapshot.py` | `PY016` | 5 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_company_skill_replacement.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_delivery_continuation.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `tests/test_delivery_continuation.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_harness_manifests.py` | `PY001` | 2 | Legacy comprehension traversal; split the nested generators into named loops. |
| `tests/test_hook_launch_budget.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_hook_launch_budget.py` | `PY017` | 3 | Legacy direct test clock read; inject a fixed clock. |
| `tests/test_native_host_acceptance.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_review_native_layer.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_review_rules.py` | `PY016` | 2 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_selected_standards.py` | `PY001` | 1 | Legacy comprehension traversal; split the nested generators into named loops. |
| `tests/test_stack_tiers.py` | `PY016` | 5 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_task_routing.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |
| `tests/test_workflow_status.py` | `PY016` | 1 | Legacy environment or argv access in hooks, orchestration and deterministic fixtures; pass process state from the entry point. |

## Expanded authored-source scope

The previous source allowlist skipped authored implementations and tests. Broad directory scopes now cover future sibling files. The following additional findings are unchanged from the recorded base commit and use exact file/module and diagnostic exceptions.

| File | Ruff rule | Existing count | Required repair |
| --- | --- | ---: | --- |
