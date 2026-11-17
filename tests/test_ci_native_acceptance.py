import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
import zipfile

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
for name in ('native_host_acceptance', 'ci_native_acceptance'):
    specification = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
CI = sys.modules['ci_native_acceptance']


class NativeProvisioningTests(unittest.TestCase):
    def archive(self, kind, member='native', link=False):
        buffer = io.BytesIO()
        if kind == 'zip':
            with zipfile.ZipFile(buffer, 'w') as archive:
                archive.writestr(member, b'payload')
                archive.writestr('../../outside', b'untrusted')
        else:
            with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
                item = tarfile.TarInfo(member)
                if link:
                    item.type = tarfile.SYMTYPE
                    item.linkname = '../../outside'
                    archive.addfile(item)
                else:
                    item.size = 7
                    archive.addfile(item, io.BytesIO(b'payload'))
        return buffer.getvalue()

    def test_digest_requires_supported_matching_metadata(self):
        payload = b'archive'
        for algorithm, separator in (('sha256', ':'), ('sha512', '-')):
            digest = hashlib.new(algorithm, payload)
            encoded = digest.hexdigest() if separator == ':' else base64.b64encode(digest.digest()).decode('ascii')
            expected = algorithm + separator + encoded
            CI.verify_digest(payload, expected, separator)
            with self.assertRaisesRegex(ValueError, 'does not match'):
                CI.verify_digest(b'corrupt', expected, separator)
        for value in (None, '', 'md5:abc'):
            with self.assertRaisesRegex(ValueError, 'supported integrity'):
                CI.verify_digest(payload, value, ':')

    def test_archive_reads_only_exact_regular_member(self):
        for kind in ('zip', 'tar.gz'):
            payload = self.archive(kind)
            self.assertEqual(b'payload', CI.archive_member(payload, 'native', kind))
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                CI.archive_member(payload, 'missing', kind)
        with self.assertRaisesRegex(ValueError, 'regular'):
            CI.archive_member(self.archive('tar.gz', link=True), 'native', 'tar.gz')

    def test_unsupported_platform_never_downloads(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(CI, 'download') as download:
            for system, machine in (('Darwin', 'x86_64'), ('Linux', 'aarch64')):
                with self.assertRaises(ValueError):
                    CI.provision(Path(temporary), system, machine, 'test-token')
            download.assert_not_called()

    def test_wrong_native_format_is_not_written(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'claude'
            with self.assertRaisesRegex(ValueError, 'native executable'):
                CI.write_executable(target, b'MZ' + b'x' * 5000, b'\x7fELF')
            self.assertFalse(target.exists())

    def test_provision_failure_cannot_run_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(CI.os.environ, {'RUNNER_TEMP': temporary}), mock.patch.object(
                CI, 'provision', side_effect=ValueError('bad integrity')
            ), mock.patch.object(CI.native_host_acceptance, 'main') as accept:
                self.assertEqual(1, CI.main())
                accept.assert_not_called()
                artifact = Path(temporary) / 'tj-agents-native-acceptance/artifacts/provision.failure.log'
                self.assertIn('bad integrity', artifact.read_text(encoding='utf-8'))


def test_release_token_is_omitted_from_asset_download(tmp_path: Path) -> None:
    asset_url = 'https://github.com/openai/codex/releases/download/pinned/codex.tar.gz'
    calls = []

    def fetch(url: str, *, headers: dict[str, str] | None = None) -> bytes:
        calls.append((url, headers))
        if headers is None:
            raise ValueError('asset download reached')
        return json.dumps({'assets': [{
            'name': 'codex-x86_64-unknown-linux-musl.tar.gz',
            'browser_download_url': asset_url,
        }]}).encode('utf-8')

    with mock.patch.object(CI, 'download', side_effect=fetch):
        with pytest.raises(ValueError, match='asset download reached'):
            CI.provision(tmp_path, 'Linux', 'x86_64', 'test-token')
    assert calls == [
        (f'https://api.github.com/repos/openai/codex/releases/tags/rust-v{CI.CODEX_VERSION}',
         {'Authorization': 'Bearer test-token'}),
        (asset_url, None),
    ]


def test_native_provisioning_requires_token_before_downloading(tmp_path: Path) -> None:
    with mock.patch.object(CI, 'download') as fetch:
        with pytest.raises(ValueError, match='requires GITHUB_TOKEN'):
            CI.provision(tmp_path, 'Linux', 'x86_64', None)
    fetch.assert_not_called()


def test_downloader_authenticates_the_metadata_request() -> None:
    with mock.patch.object(CI.urllib.request, 'urlopen', return_value=io.BytesIO(b'metadata')) as fetch:
        assert CI.download('https://api.github.com/repos/openai/codex/releases',
                           headers={'Authorization': 'Bearer test-token'}) == b'metadata'
    request = fetch.call_args.args[0]
    assert request.get_header('Authorization') == 'Bearer test-token'


if __name__ == '__main__':
    unittest.main()
