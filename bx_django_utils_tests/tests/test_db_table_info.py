import logging

from django.contrib.auth.models import User
from django.test import TestCase

from bx_django_utils.admin_extra_views.utils import reverse_admin_extra_view
from bx_django_utils.test_utils.html_assertion import (
    HtmlAssertionMixin,
    assert_html_response_snapshot,
    get_django_name_suffix,
)
from bx_django_utils.test_utils.users import make_max_test_user, make_minimal_test_user
from bx_django_utils_tests.test_app.admin_views import DatabaseTableInfoAdminExtraView


class DatabaseTableInfoViewTestCase(HtmlAssertionMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_user = make_minimal_test_user(username='staff', is_staff=True, permissions=())
        cls.non_staff_user = make_max_test_user(is_staff=False, exclude_permissions=())
        cls.superuser = User.objects.create_superuser(
            username='superuser', password='ThisIsNotAPassword!'
        )

    def get_url(self):
        return reverse_admin_extra_view(DatabaseTableInfoAdminExtraView)

    def test_anonymous_403(self):
        url = self.get_url()
        with self.assertLogs('bx_django_utils', level=logging.WARNING), self.assertLogs(
            'django.request', level=logging.WARNING
        ):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_non_staff_403(self):
        self.client.force_login(self.non_staff_user)
        url = self.get_url()
        with self.assertLogs('bx_django_utils', level=logging.WARNING), self.assertLogs(
            'django.request', level=logging.WARNING
        ):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_staff_200_sqlite(self):
        self.client.force_login(self.staff_user)
        url = self.get_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Both test DBs are SQLite — verify graceful skip output
        self.assert_html_parts(
            response,
            parts=(
                'Skipped databases (not PostgreSQL):',
                '<code>default</code>',
                '<code>second</code>',
            ),
        )
        assert_html_response_snapshot(
            response,
            query_selector='#content',
            validate=False,
            name_suffix=get_django_name_suffix(),
        )
