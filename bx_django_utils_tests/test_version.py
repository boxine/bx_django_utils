from unittest import mock

from django.test import SimpleTestCase

from bx_django_utils.version import determine_version


class VersionTest(SimpleTestCase):
    def test_determine_version(self):
        status_output = b' M .ebextensions/\n'

        def fake_git(args, **kwargs):
            if args == ['git', 'tag', '--points-at', 'HEAD']:
                return b'v2\ntest-two\n'
            elif args == ['git', 'rev-parse', '--short', 'HEAD']:
                return b'1234abc\n'
            elif args == ['git', 'status', '--untracked-files=no', '--porcelain']:
                return status_output

            raise NotImplementedError(f'{args!r} is not implemented')

        with mock.patch('subprocess.check_output', fake_git):
            self.assertEqual(determine_version(), 'v2/test-two/1234abc')

        status_output = b' M foo.py\n'
        with mock.patch('subprocess.check_output', fake_git):
            self.assertEqual(determine_version(), 'v2/test-two/1234abc+changes')

        status_output = b'\n'
        with mock.patch('subprocess.check_output', fake_git):
            self.assertEqual(determine_version(), 'v2/test-two/1234abc')

    def test_git_unavailable(self):
        with mock.patch('subprocess.check_output', side_effect=FileNotFoundError('Could not run git')):
            with self.assertRaises(FileNotFoundError):
                determine_version(raise_error=True)

            self.assertEqual(determine_version(raise_error=False), 'unknown')
