# Workflow fixture measurement

This compact record supports the final slice in `../routine-review-evidence-and-impact-ci/GOAL.md`.
Required CI run 38902959829 identified workflow-operation tests as an expensive Windows module. Source inspection found nine repeated Git setup operations in every inherited test fixture.

| Local measurement, 12 samples each | Before | After |
| --- | ---: | ---: |
| Median setup/cleanup plus identical branch/HEAD verification | 1.8319s | 0.4293s |
| Sum of those samples | 21.5683s | 5.2075s |
| Once-per-class seed initialization | included per test | 2.3078s |

The median measured operation fell by about 77%. Including the class seed, these twelve after samples took 7.5153s versus 21.5683s before. These local observations do not promise the same whole-job improvement on a shared CI runner.

The after implementation copies a complete initialized repository into a separate writable TemporaryDirectory for each test. A direct actual-Git mutation check changed one copy’s committed file, index, refs, branch and configuration; the second copy and seed retained the baseline file, HEAD, origin/main, branch, configuration and clean status. No hard links, shared mutable checkout, mocked Git or cached success replaces behavior.

All 96 test-method ASTs are identical before and after. All 96 tests passed against the exact prepared source in 455.289s. Source SHA-256: `94b69e58933d45e64c420ee6194ccdb2d06957d05fd5c9bcac3e320132d41210`. The cumulative runtime used for this check is unchanged from reviewed PR #275; its generated refresh changes packaging only. No duplicate local module run is required after applying those exact bytes.

Raw compact evidence remains Git-private under workflow run `validation-efficiency-fixture`, labels `workflow-fixture-before`, `workflow-fixture-proposed-isolation-timing` and `workflow-fixture-proposed-module`. Both Windows and Linux CI and the independent review must pass before delivery.
