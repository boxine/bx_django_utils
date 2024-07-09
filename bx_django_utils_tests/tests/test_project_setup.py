import subprocess
from importlib.metadata import version
from pathlib import Path

from bx_py_utils.path import assert_is_file
from bx_py_utils.test_utils.unittest_utils import assert_no_flat_tests_functions
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from manageprojects.test_utils.project_setup import check_editor_config, get_py_max_line_length
from model_bakery import baker
from packaging.version import Version

import bx_django_utils
from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin

PACKAGE_ROOT = Path(bx_django_utils.__file__).parent.parent
assert_is_file(PACKAGE_ROOT / 'pyproject.toml')


class ProjectSetupTestCase(SimpleTestCase):
    def test_code_style(self):
        try:
            output = subprocess.check_output(['make', 'lint'], stderr=subprocess.STDOUT, cwd=PACKAGE_ROOT, text=True)
        except subprocess.CalledProcessError:
            # Code style is not correct -> Try to fix it
            subprocess.check_call(['make', 'fix-code-style'], stderr=subprocess.STDOUT, cwd=PACKAGE_ROOT)

            # Check again:
            subprocess.check_call(['make', 'lint'], cwd=PACKAGE_ROOT)
        else:
            self.assertIn('darker', output)
            self.assertIn('flake8', output)

    def test_version(self):
        # We get a version string:
        bx_py_utils_version_str = version('bx_django_utils')
        self.assertIsInstance(bx_py_utils_version_str, str)
        self.assertTrue(bx_py_utils_version_str)

        # Note: The actual installed version may be different from the one in the __init__.py file.
        # So check this too:
        self.assertIsInstance(bx_django_utils.__version__, str)
        bx_py_utils_version = Version(bx_django_utils.__version__)
        self.assertIsInstance(bx_py_utils_version, Version)
        self.assertEqual(str(bx_py_utils_version), bx_django_utils.__version__)  # Don't allow wrong formatting

    def test_no_ignored_test_function(self):
        # In the past we used pytest ;)
        # Check if we still have some flat test function that will be not executed by unittests
        assert_no_flat_tests_functions(PACKAGE_ROOT / 'bx_django_utils')
        assert_no_flat_tests_functions(PACKAGE_ROOT / 'bx_django_utils_tests')

    def test_check_editor_config(self):
        check_editor_config(package_root=PACKAGE_ROOT)

        max_line_length = get_py_max_line_length(package_root=PACKAGE_ROOT)
        self.assertEqual(max_line_length, 119)


class DjangoProjectSetupTestCase(HtmlAssertionMixin, TestCase):
    def test_admin(self):
        response = self.client.get('/admin/')
        self.assertRedirects(response, expected_url='/admin/login/?next=/admin/')

        UserModel = get_user_model()
        user = baker.make(UserModel, is_staff=True, is_active=True, is_superuser=True)
        self.client.force_login(user)

        with self.settings(DEBUG=True):
            response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name='admin/index.html')
        self.assert_html_parts(
            response,
            parts=(
                '<title>Site administration | Django site admin</title>',
                '<link rel="stylesheet" href="/static/debug_toolbar/css/toolbar.css">',
            ),
        )
