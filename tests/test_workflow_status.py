"""Drive the Workflow status script exactly as shipped, under a synthetic HOME."""

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/workflow/utility/status/scripts/status.py'
ROW = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2} .*$', re.M)


def rows(output):
    return {line.split()[-1] for line in ROW.findall(output)}


class WorkflowStatusHarness(unittest.TestCase):
    """Synthetic home, plan corpus and repo layout. Holds no tests of its own."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic workflow status ')
        self.addCleanup(self.temp.cleanup)
        # resolve() expands the 8.3 short name mkdtemp returns under C:\Users\TOMMYS~1. The script
        # compares Path.cwd() against a path built from Path.home(); a short name makes every run
        # report "cwd outside source/repos" and silently drops scoping from the test.
        self.home = Path(self.temp.name).resolve()
        self.plans = self.home / '.claude' / 'plans'
        self.repos = self.home / 'source' / 'repos'
        self.plans.mkdir(parents=True)
        self.repos.mkdir(parents=True)
        self.script = SCRIPT
        self.here = self.repo('demo')

    def repo(self, *parts):
        path = self.repos.joinpath(*parts)
        subprocess.run(['git', 'init', '-q', str(path)], check=True, capture_output=True, text=True,
                       env=self.disposable_environment())
        subprocess.run(
            ['git', '-C', str(path), 'remote', 'add', 'origin',
             'https://github.com/example/%s.git' % path.name],
            check=True,
            capture_output=True,
            text=True,
            env=self.disposable_environment(),
        )
        return path

    def plan(self, relative, text='# a plan\n'):
        path = self.plans / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def repo_plan(self, relative, text='# a plan\n', repo=None):
        path = (repo or self.here).joinpath(*relative.split('/'))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def work_item(self, feature='reader-bridge', item='status-reader', repo=None):
        return self.repo_plan(
            'plans/features/%s/work-items/%s/README.md' % (feature, item),
            '# %s\n' % item,
            repo=repo,
        )

    def disposable_environment(self):
        environment = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home))
        for name in tuple(environment):
            if name == 'GIT_CONFIG_COUNT' or re.fullmatch(r'GIT_CONFIG_(?:KEY|VALUE)_\d+', name):
                environment.pop(name)
        if hasattr(self, 'state_directory'):
            environment['AGENT_STATE_DIRECTORY'] = str(self.state_directory)
        return environment

    def board(self, needle='', limit='20', scope='auto', cwd=None, script=None):
        environment = self.disposable_environment()
        result = subprocess.run(
            [sys.executable, '-B', str(script or self.script), needle, limit, scope],
            cwd=str(cwd or self.here), capture_output=True, text=True, env=environment)
        self.assertEqual('', result.stderr)
        self.assertEqual(0, result.returncode)
        return result.stdout

    def listed(self, *arguments, **keywords):
        return rows(self.board(*arguments, **keywords))

    def write_work_item_status(self, feature, item, status, schema=True):
        self.state_directory = self.home / 'state'
        self.state_directory.mkdir(exist_ok=True)
        database = self.state_directory / 'sessions.db'
        if database.exists():
            database.unlink()
        connection = sqlite3.connect(database)
        if schema:
            connection.executescript(
                'CREATE TABLE work_items (key TEXT PRIMARY KEY, repo TEXT NOT NULL, '
                'feature TEXT NOT NULL, item TEXT NOT NULL, status TEXT NOT NULL, '
                'branch TEXT, pr TEXT, title TEXT, plan_path TEXT, updated_at REAL);'
                'CREATE TABLE sessions (handle TEXT PRIMARY KEY, host TEXT NOT NULL, session_id TEXT NOT NULL, '
                'repo TEXT, branch TEXT, cwd TEXT, work_item TEXT, role TEXT, ended_at REAL);'
                'CREATE TABLE work_item_references (provider TEXT NOT NULL, scope TEXT NOT NULL, '
                'native_id TEXT NOT NULL, work_item TEXT NOT NULL, PRIMARY KEY (provider, scope, native_id));'
                'PRAGMA user_version = 4;'
            )
            key = 'github.com/example/demo:%s/%s' % (feature, item)
            connection.execute(
                'INSERT INTO work_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (key, 'github.com/example/demo', feature, item, status, None, None, None, None, 0),
            )
        connection.commit()
        connection.close()
        return database

    def status_skill_directory(self, reader_text=None):
        root = self.home / 'runtime-fixture'
        skill = root / '.agents' / 'workflow' / 'utility' / 'status'
        script = skill / 'scripts' / 'status.py'
        script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, script)
        runtime = root / '.agents' / 'agent-store' / 'runtime'
        runtime.mkdir(parents=True)
        (runtime / 'reader.py').write_text(reader_text or (
            'class StoreReadError(ValueError):\n    pass\n\n'
            'class ReadOnlyWorkItemStore:\n    def work_item(self, key):\n        return {"status": "active"}\n'
        ), encoding='utf-8')
        (runtime / 'repository_identity.py').write_text(
            'def repository_identity(directory, git):\n    return "github.com/example/demo"\n', encoding='utf-8')
        hooks = root / '.agents' / 'hooks'
        hooks.mkdir(parents=True)
        shutil.copy2(ROOT / '.agents/hooks/problem_records.py', hooks / 'problem_records.py')
        return script

    def capability_result(self, script):
        return subprocess.run(
            [sys.executable, '-B', str(script), '', '20', 'auto'],
            cwd=str(self.here),
            capture_output=True,
            text=True,
            env=dict(self.disposable_environment(), PYTHONPATH=''),
        )

    def isolated_capability_result(self, script):
        return subprocess.run(
            [sys.executable, '-I', '-B', str(script), '', '20', 'auto'],
            cwd=str(self.here),
            capture_output=True,
            text=True,
            env=self.disposable_environment(),
        )


class NeedleMatchingTests(WorkflowStatusHarness):
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


class ReportingTests(WorkflowStatusHarness):
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
        self.assertIn("nothing in scope is named for 'payments'", output)
        self.assertIn('~/.claude/plans is the whole corpus', output)

    def test_a_non_numeric_limit_falls_back_to_twenty(self):
        for index in range(25):
            self.plan('demo/PLAN_%02d.md' % index)
        for limit in ('all', '-5', ''):
            output = self.board('', limit)
            self.assertIn('25 open, showing 20', output, limit)


class CorpusSelectionTests(WorkflowStatusHarness):
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


class ScopingTests(WorkflowStatusHarness):
    def setUp(self):
        super().setUp()
        self.repo('other-group', 'other-repo')

    def test_another_group_is_counted_in_one_line_and_never_listed(self):
        self.plan('demo/PAYMENTS_SPLIT.md')
        self.plan('other-repo/PAYMENTS_ELSEWHERE.md')
        output = self.board('payments')
        self.assertEqual({'PAYMENTS_SPLIT.md'}, rows(output))
        self.assertIn('out of scope: 1 in other-group', output)
        self.assertIn('rerun with the scope argument all to include', output)

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

    def test_the_no_match_line_does_not_contradict_the_out_of_scope_tally(self):
        """Those rows reached `elsewhere` by name, so they are plans named for the needle."""
        self.plan('other-repo/PAYMENTS_ELSEWHERE.md')
        output = self.board('payments')
        self.assertIn("nothing in scope is named for 'payments'", output)
        self.assertIn('out of scope: 1 in other-group', output)
        self.assertNotIn('nothing in ~/.claude/plans', output)

    def test_a_loose_root_plan_is_unfiled(self):
        self.plan('LOOSE_PAYMENTS.md')
        output = self.board('payments')
        self.assertEqual(set(), rows(output))
        self.assertIn('out of scope: 1 in unfiled', output)
        self.assertIn('LOOSE_PAYMENTS.md', self.listed('payments', scope='all'))


class RepoResidentPlanTests(WorkflowStatusHarness):
    """A plan filed beside the code it concerns, which is where they are supposed to live."""

    def test_a_plan_in_the_invoking_repo_is_read(self):
        self.repo_plan('plans/payments-split/PAYMENTS_ROADMAP.md')
        self.assertIn('PAYMENTS_ROADMAP.md', self.listed('payments'))

    def test_docs_plans_is_read_as_well_as_plans(self):
        self.repo_plan('docs/plans/payments-split/ROADMAP.md')
        self.assertIn('ROADMAP.md', self.listed('payments'))

    def test_a_sibling_repo_in_the_same_group_is_read(self):
        """Concertable's roadmaps live in its docs repo, not the repo the work happens in."""
        application = self.repo('group', 'app')
        documentation = self.repo('group', 'docs')
        self.repo_plan('docs/plans/payments-split/ROADMAP.md', repo=documentation)
        self.assertIn('ROADMAP.md', self.listed('payments', cwd=application))

    def test_guidance_files_in_a_plan_tree_are_not_plans(self):
        for name in ('AGENTS.md', 'CLAUDE.md', 'README.md', 'TECH_DEBT.md', 'TECHNICAL_DEBT.md'):
            self.repo_plan('plans/%s' % name, '# payments\n')
        self.repo_plan('plans/REAL_PAYMENTS_PLAN.md')
        self.assertEqual({'REAL_PAYMENTS_PLAN.md'}, self.listed('payments'))

    def test_vendored_directories_inside_a_plan_tree_are_skipped(self):
        self.repo_plan('plans/node_modules/PAYMENTS_VENDORED.md')
        self.repo_plan('plans/PAYMENTS_KEPT.md')
        self.assertEqual({'PAYMENTS_KEPT.md'}, self.listed('payments'))

    def test_another_groups_repo_is_never_opened(self):
        """Out-of-group repos are not read at all, so their plans cannot even be counted."""
        stranger = self.repo('other-group', 'other-repo')
        self.repo_plan('plans/PAYMENTS_ELSEWHERE.md', repo=stranger)
        output = self.board('payments')
        self.assertEqual(set(), rows(output))
        self.assertNotIn('out of scope', output)

    def test_the_first_unticked_item_is_the_next_action(self):
        self.repo_plan('plans/payments-split/ROADMAP.md',
                       '# payments roadmap\n\n- [x] split the ledger\n- [ ] carve the reader\n')
        output = self.board('payments')
        self.assertIn('live 1/2', output)
        self.assertIn('carve the reader', output)

    def test_a_wrapped_item_is_reported_past_its_first_line(self):
        """Real roadmap items wrap over several source lines; stopping at the newline reports a
        fragment that ends mid-clause and tells the reader nothing."""
        self.repo_plan('plans/payments-split/ROADMAP.md',
                       '# payments roadmap\n\n'
                       '- [ ] `payments-split/ledger` - carve the ledger reader out of\n'
                       '  the settlement module and give it its own contract\n')
        output = self.board('payments')
        self.assertIn('give it its own contract', output)

    def test_a_sibling_item_is_not_swallowed_into_the_one_above(self):
        self.repo_plan('plans/payments-split/ROADMAP.md',
                       '# payments roadmap\n\n'
                       '- [ ] carve the ledger reader\n'
                       '- [ ] then rewire settlement\n')
        output = self.board('payments')
        self.assertIn('carve the ledger reader', output)
        self.assertNotIn('then rewire settlement', output)

    def test_a_repo_with_no_plan_tree_contributes_nothing(self):
        self.plan('demo/LOCAL_PAYMENTS.md')
        self.assertEqual({'LOCAL_PAYMENTS.md'}, self.listed('payments'))


class WorkItemStatusTests(WorkflowStatusHarness):
    def test_all_sqlite_statuses_are_reported_and_done_is_hidden(self):
        for status in ('proposed', 'active', 'delivery-gated', 'blocked', 'paused', 'done'):
            with self.subTest(status=status):
                self.work_item()
                self.write_work_item_status('reader-bridge', 'status-reader', status)
                output = self.board()
                if status == 'done':
                    self.assertNotIn('README.md', rows(output))
                    self.assertIn('1 named and marked done, hidden', output)
                else:
                    self.assertIn(status, output)
                    self.assertIn('reader-bridge/status-reader', output)

    def test_missing_malformed_and_unregistered_store_state_is_visible_unknown(self):
        self.work_item()
        self.state_directory = self.home / 'missing-state'
        output = self.board()
        self.assertIn('unknown', output)
        self.assertIn('session store does not exist', output)

        database = self.write_work_item_status('reader-bridge', 'status-reader', 'active', schema=False)
        connection = sqlite3.connect(database)
        connection.executescript(
            'CREATE TABLE work_items (key TEXT, status TEXT);'
            'CREATE TABLE sessions (handle TEXT, repo TEXT, branch TEXT, cwd TEXT, work_item TEXT, '
            'role TEXT, ended_at REAL);'
            'PRAGMA user_version = 4;'
        )
        connection.close()
        output = self.board()
        self.assertIn('unknown', output)
        self.assertIn('missing required columns', output)

        database = self.write_work_item_status('other-feature', 'other-item', 'active')
        output = self.board()
        self.assertIn('unknown', output)
        self.assertIn('is not registered', output)
        self.assertTrue(database.is_file())

    def test_status_lookup_is_read_only(self):
        self.work_item()
        database = self.write_work_item_status('reader-bridge', 'status-reader', 'active')
        before = database.read_bytes()
        output = self.board()
        self.assertIn('active', output)
        self.assertEqual(before, database.read_bytes())

    def test_work_item_key_matches_feature_full_key_and_item(self):
        self.work_item()
        self.write_work_item_status('reader-bridge', 'status-reader', 'active')
        for needle in ('reader-bridge', 'reader-bridge/status-reader', 'status-reader'):
            with self.subTest(needle=needle):
                self.assertEqual({'README.md'}, self.listed(needle))

    def test_uppercase_plans_directory_is_not_a_canonical_work_item_root(self):
        self.repo_plan('Plans/features/reader-bridge/work-items/status-reader/README.md', '# status-reader\n')
        self.assertEqual({'Plans'}, {child.name for child in self.here.iterdir() if child.name.casefold() == 'plans'})
        self.assertNotIn('README.md', self.listed('status-reader'))

    @unittest.skipUnless(os.name == 'nt', 'Windows case-insensitive path traversal')
    def test_uppercase_plans_directory_keeps_legacy_plan_discovery(self):
        self.repo_plan('Plans/LEGACY_STATUS_PLAN.md')
        self.assertIn('LEGACY_STATUS_PLAN.md', self.listed('legacy'))

    def test_only_strict_lowercase_work_item_readmes_use_sqlite_status(self):
        self.work_item()
        self.repo_plan('plans/features/reader-bridge/README.md', '# feature\n')
        self.repo_plan('plans/features/reader-bridge/support/README.md', '# support\n')
        self.repo_plan('plans/features/reader-bridge/work-items/status-reader/Readme.md', '# mixed\n')
        self.write_work_item_status('reader-bridge', 'status-reader', 'active')
        output = self.board()
        self.assertIn('active', output)
        self.assertEqual({'README.md'}, rows(output))

    def test_out_of_scope_work_item_never_reads_the_store(self):
        other = self.repo('other-group', 'other-repo')
        self.work_item(repo=other)
        self.state_directory = self.home / 'missing-state'
        output = self.board()
        self.assertNotIn('unknown', output)
        self.assertNotIn('README.md', rows(output))

    def test_source_and_packaged_skill_layouts_load_their_own_runtime(self):
        self.work_item()
        self.write_work_item_status('reader-bridge', 'status-reader', 'active')
        copies = [SCRIPT]
        layouts = (
            '.agents/workflow/utility/status',
            'skills/status',
            'codex-skills/status',
        )
        for layout in layouts:
            package = self.home / layout.replace('/', '-')
            script = package / layout / 'scripts/status.py'
            script.parent.mkdir(parents=True)
            shutil.copy2(SCRIPT, script)
            (package / 'hooks').mkdir()
            shutil.copy2(ROOT / '.agents/hooks/problem_records.py', package / 'hooks/problem_records.py')
            shutil.copytree(
                ROOT / '.agents/dependencies/agent/.agents/agent-store/runtime',
                package / '.agents/agent-store/runtime',
            )
            copies.append(script)
        for script in copies:
            with self.subTest(script=script):
                self.assertIn('active', self.board(script=script))

    def test_packaged_status_loads_the_adjacent_hidden_runtime_in_isolated_python(self):
        package = self.home / 'packaged status'
        script = package / 'skills/status/scripts/status.py'
        script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, script)
        hooks = package / 'hooks'
        hooks.mkdir()
        shutil.copy2(ROOT / '.agents/hooks/problem_records.py', hooks / 'problem_records.py')
        shutil.copytree(ROOT / '.agents/dependencies/cli/.agents/cli/runtime/tj_cli', hooks / 'tj_cli')
        runtime = package / '.agents/agent-store/runtime'
        shutil.copytree(ROOT / '.agents/dependencies/agent/.agents/agent-store/runtime', runtime)
        result = self.isolated_capability_result(script)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_own_runtime_is_a_capability_failure(self):
        script = self.home / 'missing-runtime/.agents/workflow/utility/status/scripts/status.py'
        script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, script)
        result = self.capability_result(script)
        self.assertEqual(2, result.returncode)
        self.assertIn('status capability failure', result.stderr)

    def select(self, repo, text=None):
        (repo / '.problem-records.json').write_text(
            text or json.dumps({'schema_version': 1, 'provider': 'fixture:manage'}), encoding='utf-8')

    def test_selected_repository_lists_plans_as_supporting_context(self):
        self.repo_plan('plans/STALE_BACKLOG.md', '# backlog\n\n- [x] done\n- [ ] open\n')
        self.plan('demo/LOCAL_NOTES.md')
        self.select(self.here)
        output = self.board()
        self.assertEqual({'STALE_BACKLOG.md', 'LOCAL_NOTES.md'}, rows(output))
        backlog = next(line for line in ROW.findall(output) if line.endswith('STALE_BACKLOG.md'))
        self.assertIn('supporting', backlog)
        self.assertNotIn('live', backlog)
        self.assertIn('selected provider: fixture:manage', output)
        self.assertIn('list/read', output)

    def test_selected_canonical_plan_never_uses_local_execution_status(self):
        self.work_item()
        self.select(self.here)
        for status in ('active', 'done'):
            with self.subTest(status=status):
                self.write_work_item_status('reader-bridge', 'status-reader', status)
                output = self.board()
                self.assertIn('README.md', rows(output))
                line = next(line for line in ROW.findall(output) if line.endswith('README.md'))
                self.assertIn('supporting', line)
                self.assertIn('reader-bridge/status-reader', line)
                self.assertNotIn('unknown', output)
        self.state_directory = self.home / 'absent-state'
        self.assertIn('supporting', self.board())

    def test_sibling_selection_failures_are_skipped_without_aborting(self):
        application = self.repo('group', 'app')
        documentation = self.repo('group', 'docs')
        selected = self.repo('group', 'tracker')
        stale = self.repos / 'group' / 'stale'
        stale.mkdir()
        (stale / '.git').write_text('gitdir: %s\n' % (self.home / 'missing-gitdir'), encoding='utf-8')
        self.repo_plan('plans/payments/APP_PLAN.md', '# app\n\n- [ ] open\n', repo=application)
        self.repo_plan('plans/payments/DOCS_PLAN.md', repo=documentation)
        self.repo_plan('plans/payments/TRACKER_PLAN.md', '# tracker\n\n- [ ] open\n', repo=selected)
        self.select(documentation, '{')
        self.select(selected)
        output = self.board(cwd=application)
        self.assertEqual({'APP_PLAN.md', 'TRACKER_PLAN.md'}, rows(output))
        application_row = next(line for line in ROW.findall(output) if line.endswith('APP_PLAN.md'))
        self.assertIn('live 0/1', application_row)
        tracker_row = next(line for line in ROW.findall(output) if line.endswith('TRACKER_PLAN.md'))
        self.assertIn('supporting', tracker_row)
        skipped = [line for line in output.splitlines() if line.startswith('skipped: ')]
        self.assertEqual(2, len(skipped))
        self.assertTrue(any('docs' in line for line in skipped))
        self.assertTrue(any('stale' in line for line in skipped))
        self.assertIn('selected provider: fixture:manage', output)

    def test_invalid_selection_never_falls_back_to_plans(self):
        self.repo_plan('plans/STALE_BACKLOG.md')
        (self.here / '.problem-records.json').write_text('{', encoding='utf-8')
        result = self.capability_result(SCRIPT)
        self.assertEqual(2, result.returncode)
        self.assertIn('record selection failed', result.stderr)
        self.assertEqual('', result.stdout)

    def test_unsupported_script_anchor_is_a_capability_failure(self):
        script = self.home / 'unknown/status.py'
        script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, script)
        result = self.capability_result(script)
        self.assertEqual(2, result.returncode)
        self.assertIn('no supported runtime anchor', result.stderr)

    def test_reader_without_read_only_store_is_a_capability_failure(self):
        skill = self.status_skill_directory(
            'class StoreReadError(ValueError):\n    pass\n'
        )
        result = self.capability_result(skill)
        self.assertEqual(2, result.returncode)
        self.assertIn('own Agent Store reader lacks work-item support', result.stderr)

    def test_reader_without_work_item_is_a_capability_failure(self):
        skill = self.status_skill_directory(
            'class StoreReadError(ValueError):\n    pass\n\n'
            'class ReadOnlyWorkItemStore:\n    pass\n'
        )
        result = self.capability_result(skill)
        self.assertEqual(2, result.returncode)
        self.assertIn('own Agent Store reader lacks work-item support', result.stderr)

    def test_repository_identity_decodes_non_ascii_git_output_as_utf8(self):
        self.work_item()
        subprocess.run(['git', '-C', str(self.here), 'remote', 'set-url', 'origin',
                        'https://github.com/example/résumé.git'], check=True, capture_output=True,
                       text=True, encoding='utf-8')
        self.write_work_item_status('reader-bridge', 'status-reader', 'active')
        database = self.state_directory / 'sessions.db'
        connection = sqlite3.connect(database)
        connection.execute('DELETE FROM work_items')
        connection.execute('INSERT INTO work_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           ('github.com/example/résumé:reader-bridge/status-reader',
                            'github.com/example/résumé', 'reader-bridge', 'status-reader',
                            'active', None, None, None, None, 0))
        connection.commit()
        connection.close()
        self.assertIn('active', self.board())


if __name__ == '__main__':
    unittest.main()
