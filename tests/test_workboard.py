"""Drive the /workboard Gather script exactly as shipped, under a synthetic HOME.

The script is extracted from the canonical SKILL.md rather than copied, so a test that passes
against a stale paste cannot exist. Nothing here reads or writes the real plan corpus.
"""

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / '.agents/engineering/utility/workboard/SKILL.md'
GATHER = re.search(r"<<'PY'\n(.*?)\nPY\n", SKILL_MD.read_text(encoding='utf-8'), re.S)
ROW = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2} .*$', re.M)


def rows(output):
    return {line.split()[-1] for line in ROW.findall(output)}


class WorkboardHarness(unittest.TestCase):
    """Synthetic home, plan corpus and repo layout. Holds no tests of its own."""

    def setUp(self):
        self.assertIsNotNone(GATHER, 'the Gather block is no longer the only PY heredoc in SKILL.md')
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic workboard ')
        self.addCleanup(self.temp.cleanup)
        # resolve() expands the 8.3 short name mkdtemp returns under C:\Users\TOMMYS~1. The script
        # compares Path.cwd() against a path built from Path.home(); a short name makes every run
        # report "cwd outside source/repos" and silently drops scoping from the test.
        self.home = Path(self.temp.name).resolve()
        self.plans = self.home / '.claude' / 'plans'
        self.repos = self.home / 'source' / 'repos'
        self.plans.mkdir(parents=True)
        self.repos.mkdir(parents=True)
        self.script = self.home / 'workboard.py'
        self.script.write_text(GATHER.group(1), encoding='utf-8')
        self.here = self.repo('demo')

    def repo(self, *parts):
        path = self.repos.joinpath(*parts)
        (path / '.git').mkdir(parents=True)
        return path

    def plan(self, relative, text='# a plan\n'):
        path = self.plans / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def board(self, needle='', limit='20', scope='auto', cwd=None):
        environment = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home))
        result = subprocess.run(
            [sys.executable, '-B', str(self.script), needle, limit, scope],
            cwd=str(cwd or self.here), capture_output=True, text=True, env=environment)
        self.assertEqual('', result.stderr)
        self.assertEqual(0, result.returncode)
        return result.stdout

    def listed(self, *arguments, **keywords):
        return rows(self.board(*arguments, **keywords))


class NeedleMatchingTests(WorkboardHarness):
    def test_punctuated_needle_finds_its_plan(self):
        self.plan('demo/AB-28884-country-risk-domain-split.md')
        self.assertIn('AB-28884-country-risk-domain-split.md', self.listed('AB-28884'))

    def test_leading_space_in_the_needle_is_tokenized_away(self):
        self.plan('demo/AB-28884-country-risk-domain-split.md')
        self.assertIn('AB-28884-country-risk-domain-split.md', self.listed(' AB-28884'))

    def test_a_pr_number_is_a_needle(self):
        self.plan('demo/PR-633-FOLLOWUP.md')
        self.assertIn('PR-633-FOLLOWUP.md', self.listed('pr-633'))

    def test_every_typed_word_must_match(self):
        self.plan('demo/B2B_ACCEPT_UNION_HANDOFF.md')
        self.plan('demo/B2B_TENANCY_SWEEP.md')
        self.assertEqual({'B2B_ACCEPT_UNION_HANDOFF.md'}, self.listed('b2b accept'))

    def test_the_word_may_start_with_the_needle(self):
        self.plan('demo/AUTHORIZATION_MODEL.md')
        self.assertIn('AUTHORIZATION_MODEL.md', self.listed('auth'))

    def test_a_word_never_stands_in_for_a_longer_needle(self):
        """authz is authorization; the auth service is a different subject."""
        self.plan('demo/AUTH_SERVICE_CARVE.md')
        self.assertEqual(set(), self.listed('authz'))

    def test_a_five_letter_stem_matches_a_short_ending(self):
        self.plan('demo/TENANCY_SWEEP.md')
        self.assertIn('TENANCY_SWEEP.md', self.listed('tenant'))

    def test_a_stem_match_rejects_a_long_remainder(self):
        """authorization and authored share five letters and nothing else."""
        self.plan('demo/PROMPT_AUTHORED_NOTES.md')
        self.plan('demo/AUTHORING_CI_FROM_SCRATCH.md')
        self.assertEqual(set(), self.listed('authorization'))

    def test_the_floors_that_stop_noise(self):
        self.plan('demo/AUTHORED_NOTES.md')
        self.plan('demo/POS_TERMINAL.md')
        self.assertEqual(set(), self.listed('authz'))
        self.assertEqual(set(), self.listed('postgres'))

    def test_an_empty_needle_lists_the_whole_board(self):
        self.plan('demo/ONE.md')
        self.plan('demo/TWO.md')
        self.assertEqual({'ONE.md', 'TWO.md'}, self.listed(''))


class ReportingTests(WorkboardHarness):
    def test_a_title_hit_is_a_name_hit(self):
        self.plan('demo/OPAQUE_FILENAME.md', '# the payments split\n')
        self.assertIn('OPAQUE_FILENAME.md', self.listed('payments'))

    def test_a_body_mention_is_counted_not_listed(self):
        self.plan('demo/PAYMENTS_SPLIT.md')
        self.plan('demo/UNRELATED_WORK.md', '# unrelated\n\nblocked behind payments.\n')
        output = self.board('payments')
        self.assertEqual({'PAYMENTS_SPLIT.md'}, rows(output))
        self.assertIn("1 more mention 'payments' only in their text", output)

    def test_text_only_rows_list_only_when_nothing_is_named(self):
        self.plan('demo/UNRELATED_WORK.md', '# unrelated\n\nblocked behind payments.\n')
        output = self.board('payments')
        self.assertEqual({'UNRELATED_WORK.md'}, rows(output))
        self.assertIn("no plan is named for 'payments'", output)

    def test_a_named_plan_marked_done_says_so(self):
        self.plan('demo/PAYMENTS_SPLIT.md', '# payments split\n\nStatus: complete\n')
        output = self.board('payments')
        self.assertIn("every plan named for 'payments' is marked done", output)
        self.assertNotIn("no plan is named for 'payments'", output)

    def test_a_needle_that_matches_nothing_names_the_corpus_it_searched(self):
        self.plan('demo/SOMETHING_ELSE.md')
        output = self.board('payments')
        self.assertIn("nothing in ~/.claude/plans is named for 'payments'", output)
        self.assertIn('outside this corpus', output)

    def test_a_non_numeric_limit_falls_back_to_twenty(self):
        for index in range(25):
            self.plan('demo/PLAN_%02d.md' % index)
        for limit in ('all', '-5', ''):
            output = self.board('', limit)
            self.assertIn('25 open, showing 20', output, limit)


class CorpusSelectionTests(WorkboardHarness):
    def test_a_flat_subfolder_is_read(self):
        self.plan('demo/Post Launch Scalability/SHARDING.md')
        self.assertIn('SHARDING.md', self.listed(''))

    def test_a_subfolder_with_directories_is_skipped_whole(self):
        """A copied repository tree, including any .md sitting directly inside it. The plan
        buried in a mirror is a known, documented blind spot, not a defect to fix here."""
        self.plan('demo/mirror/DEAL_VOCABULARY_PORT.md')
        self.plan('demo/mirror/docs/NOTES.md')
        self.plan('demo/KEPT.md')
        self.assertEqual({'KEPT.md'}, self.listed(''))

    def test_dotted_and_vendored_directories_are_skipped(self):
        """Path.glob matches a dotted directory, so .git only stays out because SKIP names it."""
        self.plan('.git/HIDDEN.md')
        self.plan('demo/node_modules/VENDORED.md')
        self.plan('demo/KEPT.md')
        self.assertEqual({'KEPT.md'}, self.listed(''))


class ScopingTests(WorkboardHarness):
    def setUp(self):
        super().setUp()
        self.repo('other-group', 'other-repo')

    def test_another_group_is_counted_in_one_line_and_never_listed(self):
        self.plan('demo/PAYMENTS_SPLIT.md')
        self.plan('other-repo/PAYMENTS_ELSEWHERE.md')
        output = self.board('payments')
        self.assertEqual({'PAYMENTS_SPLIT.md'}, rows(output))
        self.assertIn('out of scope: 1 in other-group', output)

    def test_scope_all_lists_the_other_group(self):
        self.plan('demo/PAYMENTS_SPLIT.md')
        self.plan('other-repo/PAYMENTS_ELSEWHERE.md')
        self.assertEqual({'PAYMENTS_SPLIT.md', 'PAYMENTS_ELSEWHERE.md'},
                         self.listed('payments', scope='all'))

    def test_an_out_of_group_file_is_never_read(self):
        """Matched on directory and filename alone, so another company's prose never enters."""
        self.plan('other-repo/OPAQUE.md', '# opaque\n\nall about payments.\n')
        output = self.board('payments')
        self.assertEqual(set(), rows(output))
        self.assertNotIn('out of scope', output)

    def test_a_loose_root_plan_is_unfiled(self):
        self.plan('LOOSE_PAYMENTS.md')
        output = self.board('payments')
        self.assertEqual(set(), rows(output))
        self.assertIn('out of scope: 1 in unfiled', output)
        self.assertIn('LOOSE_PAYMENTS.md', self.listed('payments', scope='all'))


if __name__ == '__main__':
    unittest.main()
