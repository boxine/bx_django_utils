import sys

from django.conf import settings
from django.core.checks import Error
from django.test import SimpleTestCase

from bx_django_utils.credentials.checks import credentials_check


class ImportErrorContextManager:  # TODO: Add to bx_py_utils
    """
    Simulate an import error by set `sys.modules[foobar]` to None

    Import error looks like:
        ModuleNotFoundError: import of foobar halted; None in sys.modules
    """

    def __init__(self, packages: list):
        self.packages = packages
        self._old_sys_modules = {}

    def __enter__(self):
        for name in self.packages:
            assert name in sys.modules, f'Package {name!r} is not installed!'

            self._old_sys_modules[name] = sys.modules.get(name)
            sys.modules[name] = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        for name, module in self._old_sys_modules.items():
            sys.modules[name] = module

        if exc_type:
            return False


class ChecksTestCase(SimpleTestCase):
    def test_checks(self):
        with self.settings(CREDENTIALS_INFO_BYTES=None):
            # Can be None
            errors = credentials_check(app_configs=None)
            self.assertEqual(errors, [])

            # Is optional:
            del settings.CREDENTIALS_INFO_BYTES
            errors = credentials_check(app_configs=None)
            self.assertEqual(errors, [])

        # Can be bytes:
        with self.settings(CREDENTIALS_INFO_BYTES=b'foobar'):
            errors = credentials_check(app_configs=None)
            self.assertEqual(errors, [])

        # Must be bytes:
        with self.settings(CREDENTIALS_INFO_BYTES='foobar'):
            errors = credentials_check(app_configs=None)
            self.assertEqual(
                errors,
                [
                    Error(
                        msg='settings.CREDENTIALS_INFO_BYTES must be None or bytes!',
                        id='credentials.E002',
                    )
                ],
            )

        with ImportErrorContextManager(packages=['cryptography']):
            errors = credentials_check(app_configs=None)
            self.assertEqual(
                errors,
                [
                    Error(
                        msg=(
                            'Package "cryptography" is not installed:'
                            ' import of cryptography halted; None in sys.modules'
                        ),
                        hint='Add "cryptography" to your project requirements.',
                        id='credentials.E001',
                    )
                ],
            )
