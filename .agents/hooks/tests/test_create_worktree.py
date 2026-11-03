"""Real temporary Git repositories exercise the deterministic worktree creation path."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / '.agents/engineering/operation/open-worktree/scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('create_worktree', SCRIPTS / 'create_worktree.py')
CREATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CREATE)


def git(cwd, *arguments):
    subprocess.run(['git', '-C', str(cwd), *arguments], check=True, capture_output=True, text=True)


class CreateWorktreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='create-worktree ü ')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-q', '-b', 'main')
        git(self.repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'init')

    def test_new_branch_lands_nested_inside_the_repository_never_a_sibling(self):
        result = CREATE.create('Feature/BrowserCredentials', cwd=self.repo)
        expected = self.repo / '.worktrees' / 'Feature-BrowserCredentials'
        self.assertEqual(expected.resolve(), Path(result['path']).resolve())
        self.assertTrue(expected.is_dir())
        sibling = self.repo.parent / f'{self.repo.name}.worktrees' / 'Feature-BrowserCredentials'
        self.assertFalse(sibling.exists())

    def test_branch_hierarchy_is_flattened_not_nested_as_a_subdirectory(self):
        result = CREATE.create('Fix/Nested/Branch', cwd=self.repo)
        expected = self.repo / '.worktrees' / 'Fix-Nested-Branch'
        self.assertEqual(expected.resolve(), Path(result['path']).resolve())

    def test_an_existing_local_branch_is_checked_out_without_a_new_start_point(self):
        git(self.repo, 'branch', 'Feature/Existing')
        result = CREATE.create('Feature/Existing', cwd=self.repo)
        expected = self.repo / '.worktrees' / 'Feature-Existing'
        self.assertEqual(expected.resolve(), Path(result['path']).resolve())
        self.assertEqual('(existing branch)', result['base'])

    def test_an_explicit_start_point_is_used_for_a_dependent_stack_layer(self):
        git(self.repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'parent')
        parent_tip = subprocess.run(['git', '-C', str(self.repo), 'rev-parse', 'HEAD'],
                                    capture_output=True, text=True, check=True).stdout.strip()
        result = CREATE.create('Feature/DependentLayer', start_point=parent_tip, cwd=self.repo)
        self.assertEqual(parent_tip, result['head'])
        self.assertEqual(parent_tip, result['base'])

    def test_refuses_to_create_a_worktree_that_already_exists(self):
        CREATE.create('Feature/Repeated', cwd=self.repo)
        with self.assertRaises(CREATE.CreateWorktreeError):
            CREATE.create('Feature/Repeated', cwd=self.repo)

    def test_creation_works_from_an_existing_worktree_not_only_the_primary_checkout(self):
        first = CREATE.create('Feature/First', cwd=self.repo)
        result = CREATE.create('Feature/Second', cwd=Path(first['path']))
        expected = self.repo / '.worktrees' / 'Feature-Second'
        self.assertEqual(expected.resolve(), Path(result['path']).resolve())


if __name__ == '__main__':
    unittest.main()
