import base64
import hashlib
import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
import zipfile


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
                    CI.provision(Path(temporary), system, machine)
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


if __name__ == '__main__':
    unittest.main()
