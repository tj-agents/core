"""Real temporary Git repositories; GitHub, the merge proof and agent-store are replaced by doubles."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / '.agents/engineering/workflow/merge/scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('worktree_sweep', SCRIPTS / 'worktree_sweep.py')
SWEEP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SWEEP)
sys.path.insert(0, str(Path(__file__).resolve().parent / 'fixtures'))
import fake_cli


def git(cwd, *arguments):
    subprocess.run(['git', '-C', str(cwd), *arguments], check=True, capture_output=True, text=True)


class SweepTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sweep ü ')
        self.primary = Path(self.temp.name) / 'repo'
        self.primary.mkdir()
        git(self.primary, 'init', '-q', '-b', 'main')
        git(self.primary, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'init')
        self.worktrees = {}
        for branch in ('Feature/Merged', 'Feature/Open', 'Feature/Base', 'Feature/Busy'):
            path = self.primary / '.worktrees' / branch.replace('/', '-')
            git(self.primary, 'worktree', 'add', '-q', '-b', branch, str(path))
            self.worktrees[branch] = path
        self.heads = {branch: self.head(path) for branch, path in self.worktrees.items()}
        self.removed = []

    def tearDown(self):
        self.temp.cleanup()

    def sweep(self, live=()):
        def removable(primary, worktree):
            merged = worktree['branch'] in ('Feature/Merged', 'Feature/Base', 'Feature/Busy')
            return (True, 'merged') if merged else (False, 'PR #9 is not MERGED')

        def delete(primary, worktree):
            self.removed.append(worktree['branch'])
            return True, 'removed'

        def merged(primary):
            return set(self.heads.items())

        return SWEEP.sweep_repository(self.primary, list(live), removable=removable,
                                      based=lambda primary, branch: branch == 'Feature/Base', delete=delete,
                                      merged=merged)

    def head(self, path):
        return subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'], capture_output=True, text=True,
                              check=True).stdout.strip()

    def outcome(self, outcomes, branch):
        return next(value for key, value in outcomes.items()
                    if Path(key).resolve() == self.worktrees[branch].resolve())

    def test_only_a_merged_unused_worktree_that_bases_nothing_is_removed(self):
        busy = str(self.worktrees['Feature/Busy'] / 'src')

        outcomes = self.sweep(live=[busy])

        self.assertEqual(['Feature/Merged'], self.removed)
        self.assertEqual('removed', self.outcome(outcomes, 'Feature/Merged'))
        self.assertEqual('kept: PR #9 is not MERGED', self.outcome(outcomes, 'Feature/Open'))
        self.assertEqual('kept: an open pull request is based on its branch', self.outcome(outcomes, 'Feature/Base'))
        self.assertEqual('kept: a session is working in it', self.outcome(outcomes, 'Feature/Busy'))
        self.assertEqual(4, len(outcomes))


    def test_the_primary_checkout_is_never_a_candidate(self):
        outcomes = self.sweep()

        self.assertNotIn(str(self.primary), outcomes)
        self.assertNotIn('main', self.removed)

    def test_a_missing_worktree_directory_is_skipped(self):
        os.rename(self.worktrees['Feature/Merged'], Path(self.temp.name) / 'moved')

        self.sweep()

        self.assertNotIn('Feature/Merged', self.removed)

    def fake_agent_store(self, response):
        environment = fake_cli.install(Path(self.temp.name) / 'tools', {'agent-store launches': response},
                                       names=('agent-store',))
        self.enterContext(fake_cli.environment({**environment, 'PATH': str(Path(self.temp.name) / 'tools')}))
        return environment

    def test_only_active_launches_with_a_worktree_count_as_working(self):
        launches = [
            {'launch_id': 'a', 'cwd': 'C:/a', 'worktree': 'C:/a', 'state': 'active'},
            {'launch_id': 'b', 'cwd': 'C:/b', 'worktree': 'C:/b', 'state': 'ended'},
            {'launch_id': 'c', 'cwd': 'C:/c', 'worktree': 'C:/c', 'state': 'closing'},
            {'launch_id': 'd', 'cwd': 'C:/d', 'worktree': None, 'state': 'active'},
        ]
        environment = self.fake_agent_store(
            {'stdout': {'ok': True, 'schema_version': 1, 'data': {'launches': launches}}})

        rows = SWEEP.launch_rows()

        self.assertEqual(['C:/a'], SWEEP.live_worktrees(rows))
        self.assertEqual(['agent-store launches'], [call['command'] for call in fake_cli.calls(environment)])

    def test_repositories_are_discovered_from_every_launch_directory(self):
        launches = [{'cwd': str(self.worktrees['Feature/Merged']), 'state': 'ended'},
                    {'cwd': str(self.primary), 'state': 'active'}, {'cwd': None, 'state': 'active'}]

        self.assertEqual([self.primary.resolve()], SWEEP.discover_repositories(launches))

    def test_links_inside_a_worktree_are_unlinked_without_touching_their_target(self):
        target = Path(self.temp.name) / 'real skills'
        target.mkdir()
        (target / 'SKILL.md').write_text('keep', encoding='utf-8')
        link = self.worktrees['Feature/Merged'] / '.Codex' / 'skills'
        link.parent.mkdir()
        try:
            if os.name == 'nt':
                subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], check=True, capture_output=True)
            else:
                link.symlink_to(target, target_is_directory=True)
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f'cannot create a directory link here: {error}')

        removed = SWEEP.unlink_links(self.worktrees['Feature/Merged'])

        self.assertEqual([link], removed)
        self.assertFalse(os.path.lexists(link))
        self.assertEqual('keep', (target / 'SKILL.md').read_text(encoding='utf-8'))

    def test_only_empty_unregistered_folders_are_cleared(self):
        empty = self.primary / '.worktrees' / 'Fix-Gone'
        empty.mkdir()
        kept = self.primary / '.worktrees' / 'Fix-HasFiles'
        kept.mkdir()
        (kept / 'notes.md').write_text('x', encoding='utf-8')
        fresh = self.primary / '.worktrees' / 'Fix-BeingCreated'
        fresh.mkdir()
        old = empty.stat().st_mtime - SWEEP.ORPHAN_AGE_SECONDS - 60
        os.utime(empty, (old, old))

        outcomes = self.sweep()

        self.assertFalse(empty.exists())
        self.assertTrue((kept / 'notes.md').is_file())
        self.assertTrue(fresh.is_dir())
        self.assertIn('removed empty leftover folder', outcomes.values())

    def test_a_dry_run_reports_empty_leftovers_without_removing_them(self):
        empty = self.primary / '.worktrees' / 'Fix-Gone'
        empty.mkdir()
        old = empty.stat().st_mtime - SWEEP.ORPHAN_AGE_SECONDS - 60
        os.utime(empty, (old, old))

        outcomes = SWEEP.sweep_repository(self.primary, [], removable=lambda primary, worktree: (False, 'no'),
                                          based=lambda primary, branch: False, dry_run=True,
                                          merged=lambda primary: set())

        self.assertTrue(empty.is_dir())
        self.assertIn('would remove empty leftover folder', outcomes.values())

    def test_only_worktrees_at_a_merged_pr_head_reach_the_proof(self):
        proved = []

        def removable(primary, worktree):
            proved.append(worktree['branch'])
            return True, 'merged'

        merged = {('Feature/Merged', self.head(self.worktrees['Feature/Merged']))}
        outcomes = SWEEP.sweep_repository(self.primary, [], removable=removable,
                                          based=lambda primary, branch: False,
                                          delete=lambda primary, worktree: (True, 'removed'),
                                          merged=lambda primary: merged)

        self.assertEqual(['Feature/Merged'], proved)
        self.assertEqual(3, list(outcomes.values()).count('kept: no merged pull request at this commit'))

    def test_an_unreadable_merged_pr_list_removes_nothing(self):
        outcomes = SWEEP.sweep_repository(self.primary, [], removable=lambda primary, worktree: (True, 'merged'),
                                          based=lambda primary, branch: False,
                                          delete=lambda primary, worktree: (True, 'removed'),
                                          merged=lambda primary: None)

        self.assertNotIn('removed', outcomes.values())

    def test_a_failed_launch_listing_stops_the_run(self):
        for response in ({'stdout': {'ok': False, 'schema_version': 1,
                                     'error': {'code': 'storage', 'message': 'locked'}}, 'code': 5},
                         {'stdout': 'not json'},
                         {'stdout': {'ok': True, 'schema_version': 1, 'data': {}}}):
            with self.subTest(response=response):
                self.fake_agent_store(response)
                with self.assertRaises(SWEEP.UnreadableLaunches):
                    SWEEP.launch_rows()

    def test_a_missing_agent_store_removes_nothing(self):
        empty = Path(self.temp.name) / 'empty tools'
        empty.mkdir()
        output = io.StringIO()
        with fake_cli.environment({'PATH': str(empty)}), contextlib.redirect_stdout(output):
            code = SWEEP.main(['--repo', str(self.primary)])

        self.assertEqual(1, code)
        self.assertIn('agent-store is not on PATH', json.loads(output.getvalue())['error'])
        self.assertTrue(all(path.is_dir() for path in self.worktrees.values()))

    def test_recent_edits_keep_a_worktree_and_old_ones_do_not(self):
        worktree = self.worktrees['Feature/Merged']
        notes = worktree / 'notes.md'
        notes.write_text('thinking', encoding='utf-8')

        self.assertTrue(SWEEP.recently_edited(worktree))
        old = notes.stat().st_mtime - SWEEP.RECENT_EDIT_SECONDS - 60
        os.utime(notes, (old, old))
        self.assertFalse(SWEEP.recently_edited(worktree))

    def test_a_branch_that_moved_past_the_proven_commit_is_kept(self):
        worktree = self.worktrees['Feature/Merged']
        proven = subprocess.run(['git', '-C', str(worktree), 'rev-parse', 'HEAD'], capture_output=True,
                                text=True, check=True).stdout.strip()
        git(worktree, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'late')

        done, result = SWEEP.remove(self.primary, {'path': str(worktree), 'branch': 'Feature/Merged',
                                                   'head': proven})

        self.assertTrue(done)
        self.assertIn('branch kept', result)
        branches = subprocess.run(['git', '-C', str(self.primary), 'branch', '--list', 'Feature/Merged'],
                                  capture_output=True, text=True, check=True).stdout
        self.assertIn('Feature/Merged', branches)

    def test_worktree_listing_parses_branches_and_detached_heads(self):
        porcelain = ('worktree C:/r\nHEAD aaa\nbranch refs/heads/main\n\n'
                     'worktree C:/r/.worktrees/x\nHEAD bbb\ndetached\n\n'
                     'worktree C:/r/.worktrees/y\nHEAD ccc\nbranch refs/heads/Fix/Y\n')

        parsed = SWEEP.parse_worktrees(porcelain)

        self.assertEqual(['main', None, 'Fix/Y'], [entry.get('branch') for entry in parsed])
        self.assertEqual('C:/r/.worktrees/x', parsed[1]['path'])


if __name__ == '__main__':
    unittest.main()
