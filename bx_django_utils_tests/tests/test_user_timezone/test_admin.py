from http.cookies import SimpleCookie

from django.test import TestCase

from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_django_utils.test_utils.users import make_minimal_test_user


class UserTimezoneTestCase(HtmlAssertionMixin, TestCase):
    """
    Integration tests for user timezone into test project
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff_user = make_minimal_test_user(username='foobar', is_staff=True, permissions=())

    def test_admin_index(self):
        self.client.cookies = SimpleCookie({'UserTimeZone': 'Europe/London'})
        self.client.force_login(self.staff_user)

        response = self.client.get('/admin/')
        self.assert_html_parts(
            response,
            parts=(
                '<title>Site administration | Django site admin</title>',
                '<span>Active Timezone:&nbsp;Europe/London</span>',
            ),
        )
