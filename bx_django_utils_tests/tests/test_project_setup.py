from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from manageprojects.test_utils.project_setup import check_editor_config, get_py_max_line_length
from model_bakery import baker
from packaging.version import Version

from bx_django_utils import __version__
from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_django_utils_tests.tests import PACKAGE_ROOT


class ProjectSetupTestCase(SimpleTestCase):
    def test_version(self):
        self.assertIsNotNone(__version__)

        version = Version(__version__)  # Will raise InvalidVersion() if wrong formatted
        self.assertEqual(str(version), __version__)

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
