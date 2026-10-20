"""Real temporary Git repositories; GitHub, the merge proof and process liveness are replaced by doubles."""

import importlib.util
import os
from pathlib import Path
import sqlite3
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

        return SWEEP.sweep_repository(self.primary, list(live), removable=removable,
                                      based=lambda primary, branch: branch == 'Feature/Base', delete=delete)

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

    def test_only_unended_sessions_with_a_live_process_count_as_working(self):
        database = Path(self.temp.name) / 'sessions.db'
        connection = sqlite3.connect(database)
        connection.execute('CREATE TABLE sessions (cwd TEXT, pid INTEGER, ended_at REAL)')
        connection.executemany('INSERT INTO sessions VALUES (?, ?, ?)', [
            ('C:/a', 10, None), ('C:/b', 11, 5.0), ('C:/c', 12, None), (None, 13, None)])
        connection.commit()
        connection.close()

        rows = SWEEP.session_rows(database)
        live = SWEEP.live_session_directories(rows, alive=lambda pid: pid != 12)

        self.assertEqual(['C:/a'], live)

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
                                          based=lambda primary, branch: False, dry_run=True)

        self.assertTrue(empty.is_dir())
        self.assertIn('would remove empty leftover folder', outcomes.values())

    def test_an_unreadable_session_registry_stops_the_run(self):
        database = Path(self.temp.name) / 'sessions.db'
        database.write_bytes(b'not a sqlite database at all' * 100)

        with self.assertRaises(SWEEP.UnreadableSessions):
            SWEEP.session_rows(database)

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
