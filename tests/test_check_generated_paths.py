"""check_generated_paths.py over throwaway git repositories; the real checkout is never read."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('check_generated_paths', ROOT / 'scripts/check_generated_paths.py')
GUARD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUARD
SPEC.loader.exec_module(GUARD)


def git(cwd, *arguments):
    subprocess.run(
        ['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid', *arguments],
        cwd=cwd, check=True, capture_output=True, text=True,
    )


def catalog(digest, description='a package'):
    return {'releases': [{'plugins': [{'id': 'market/pkg', 'description': description, 'digest': digest}]}]}


class GeneratedPathGuardTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='generated guard ')
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        git(self.repo, 'init', '--quiet', '--initial-branch=main')
        # A commit may start git's automatic gc or maintenance in the background, which then writes into
        # .git while the temporary directory is being removed.
        git(self.repo, 'config', 'gc.auto', '0')
        git(self.repo, 'config', 'maintenance.auto', 'false')
        self.write('.agents/plugins/sources.json', {'generated_roots': ['plugins']})
        self.write(GUARD.CATALOG, catalog('sha256:old'))
        self.write('plugins/pkg/file.txt', 'generated')
        self.commit('base')
        git(self.repo, 'switch', '--quiet', '-c', 'feature')

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content, indent=2) + '\n')

    def commit(self, message):
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '--quiet', '-m', message)

    def offending(self):
        return GUARD.offending_paths('main', root=self.repo)

    def test_an_authored_change_passes(self):
        self.write('src.py', 'print(1)\n')
        self.write(GUARD.CATALOG, catalog('sha256:old', description='edited by hand'))
        self.commit('authored')
        self.assertEqual(self.offending(), [])

    def test_a_generated_path_is_rejected(self):
        self.write('plugins/pkg/file.txt', 'regenerated')
        self.commit('generated')
        self.assertEqual(self.offending(), ['plugins/pkg/file.txt'])

    def test_a_committed_catalog_digest_is_rejected(self):
        self.write(GUARD.CATALOG, catalog('sha256:new'))
        self.commit('digest')
        self.assertEqual(self.offending(), [f'{GUARD.CATALOG} digest of market/pkg'])

    def test_a_new_catalog_entry_may_arrive_with_its_digest(self):
        added = catalog('sha256:old')
        added['releases'][0]['plugins'].append({'id': 'market/new', 'digest': 'sha256:first'})
        self.write(GUARD.CATALOG, added)
        self.commit('new package')
        self.assertEqual(self.offending(), [])


if __name__ == '__main__':
    unittest.main()
