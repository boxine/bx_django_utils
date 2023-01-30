import logging

from bx_py_utils.test_utils.snapshot import assert_snapshot
from django.contrib.auth.models import User
from django.test import TestCase

from bx_django_utils.admin_extra_views.utils import iter_admin_extra_views_urls


class AdminExtraViewsTestCase(TestCase):
    """
    Integrations tests for Admin Extra Views.
    Should be a copy&paste template for bx_django_utils user projects.
    """

    def test_anonymous_access(self):
        checked_urls = 0
        for url in iter_admin_extra_views_urls():
            with self.assertLogs('bx_django_utils', level=logging.WARNING) as logs, self.assertLogs(
                'django.request', level=logging.WARNING
            ):
                response = self.client.get(url)
            logs = '\n'.join(logs.output)
            self.assertIn('did not pass', logs)
            self.assertEqual(response.status_code, 403)
            checked_urls += 1
        self.assertGreaterEqual(checked_urls, 1)

    def test_superuser_access(self):
        superuser = User.objects.create_superuser(username='foobar')
        self.client.force_login(superuser)

        all_urls = []
        for url in iter_admin_extra_views_urls():
            respose = self.client.get(url)
            if url == '/admin/feature_flags/feature-flags-values-demo/':
                self.assertRedirects(respose, expected_url='/admin/', fetch_redirect_response=False)
            else:
                self.assertEqual(respose.status_code, 200)

            all_urls.append(url)
        self.assertGreaterEqual(len(all_urls), 1)
        assert_snapshot(got=all_urls)
