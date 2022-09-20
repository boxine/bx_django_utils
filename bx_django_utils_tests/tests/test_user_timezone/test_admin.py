from http.cookies import SimpleCookie

from django.conf import settings
from django.test import TestCase
from playwright.sync_api import BrowserContext, expect

from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_django_utils.test_utils.playwright import PlaywrightTestCase
from bx_django_utils.test_utils.users import make_minimal_test_user


class UserTimezoneTestCase(HtmlAssertionMixin, TestCase):
    """
    Integration tests for user timezone into test project
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

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


class UserTimezonePlaywrightMixin:
    """
    Run User Timezone tests with Firefox and Chromium, via:
        * UserTimezoneFirefoxTestCase
        * UserTimezoneChromiumTestCase
    """

    def test_user_timezone(self):
        context: BrowserContext = self.browser.new_context(
            ignore_https_errors=True,  # StaticLiveServerTestCase has no valid certificate ;)
            locale='en_US',
            timezone_id='Europe/Berlin',
        )
        with context.new_page() as page:
            # Use our "Dynamic View Menu" index page from our "test_app":
            page.goto(f'{self.live_server_url}')
            expect(page).to_have_title('Dynamic View Menu - Index | Django site admin')

            # UserTimeZone cookie set?
            cookies = context.cookies()
            self.assertEqual(
                cookies,
                [
                    {
                        'domain': 'localhost',
                        'expires': -1,
                        'httpOnly': False,
                        'name': 'UserTimeZone',
                        'path': '/',
                        'sameSite': 'Lax',
                        'secure': False,
                        'value': 'Europe/Berlin',
                    }
                ],
            )

            # First request: The cookie is set in the client but not yet sent to the server.
            # So we get the default timezone:
            assert settings.TIME_ZONE == 'UTC'  # Check the default timezone
            expect(page.locator('text=Active Timezone: UTC')).to_be_visible()

            # Just reload the page to send the cookie to the server:
            page.reload()

            # Now the timezone should be active:
            expect(page.locator('text=Active Timezone: Europe/Berlin')).to_be_visible()


class UserTimezoneFirefoxTestCase(UserTimezonePlaywrightMixin, PlaywrightTestCase):
    BROWSER_NAME = 'firefox'


class UserTimezoneChromiumTestCase(UserTimezonePlaywrightMixin, PlaywrightTestCase):
    BROWSER_NAME = 'chromium'
