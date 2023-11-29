import zoneinfo
from http.cookies import SimpleCookie

from bx_py_utils.test_utils.log_utils import NoLogs
from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone
from playwright.sync_api import BrowserContext, expect

from bx_django_utils.test_utils.html_assertion import HtmlAssertionMixin
from bx_django_utils.test_utils.playwright import PlaywrightTestCase
from bx_django_utils.test_utils.users import make_minimal_test_user
from bx_django_utils.user_timezone.middleware import InvalidUserTimeZone, UserTimezoneMiddleware, validate


class ValidateUserTimeZone(SimpleTestCase):
    def validate(self, raw_time_zone: str):
        validate(
            raw_time_zone=raw_time_zone,
            min_length=UserTimezoneMiddleware.MIN_LENGTH,
            max_length=UserTimezoneMiddleware.MAX_LENGTH,
            usertimezone_re=UserTimezoneMiddleware.USERTIMEZONE_RE,
        )

    def test_validate(self):
        count = 0
        for timezone_name in zoneinfo.available_timezones():
            self.validate(raw_time_zone=timezone_name)
            count += 1
        self.assertGreaterEqual(count, 10)

    def test_invalid(self):
        with self.assertRaisesMessage(InvalidUserTimeZone, 'Expected max length'):
            self.validate(raw_time_zone='A' * (UserTimezoneMiddleware.MAX_LENGTH + 1))
        with self.assertRaisesMessage(InvalidUserTimeZone, 'Expected min length'):
            self.validate(raw_time_zone='A' * (UserTimezoneMiddleware.MIN_LENGTH - 1))
        with self.assertRaisesMessage(InvalidUserTimeZone, 'Expected min length'):
            self.validate(raw_time_zone='A' * (UserTimezoneMiddleware.MIN_LENGTH - 1))
        with self.assertRaisesMessage(InvalidUserTimeZone, 'Only ASCII'):
            self.validate(raw_time_zone='Foo\N{SNOWMAN}Far')
        with self.assertRaisesMessage(InvalidUserTimeZone, 'Not match'):
            self.validate(raw_time_zone='Bam!')


class StoreTimezone:
    def __enter__(self):
        self.old_timezone = timezone.get_current_timezone_name()
        return self

    def __call__(self, request):
        self.request_timezone = timezone.get_current_timezone_name()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False


class UserTimezoneMiddlewareTestCase(TestCase):
    def check(self, raw_time_zone: str) -> str:
        self.assertEqual(timezone.get_current_timezone_name(), 'UTC')

        request = RequestFactory().get('/test_app/')
        request.COOKIES['UserTimeZone'] = raw_time_zone
        with StoreTimezone() as store_timezone:
            middleware = UserTimezoneMiddleware(get_response=store_timezone)
            middleware(request)

        return store_timezone.request_timezone

    def test_set_timezone(self):
        matrix = (
            ('Europe/London', 'Europe/London'),
            ('America/Argentina/ComodRivadavia', 'America/Argentina/ComodRivadavia'),
            ('NZ', 'NZ'),
            ('GB', 'GB'),
            ('Etc/GMT+12', '-12'),
            ('Etc/GMT-14', '+14'),
        )
        for raw_time_zone, expected_timezone in matrix:
            with self.subTest(raw_time_zone=raw_time_zone):
                request_timezone = self.check(raw_time_zone=raw_time_zone)
                self.assertEqual(
                    request_timezone,
                    expected_timezone,
                    f'Got {request_timezone!r} from UserTimeZone={raw_time_zone!r}',
                )

    def test_invalid(self):
        with self.assertRaisesMessage(InvalidUserTimeZone, 'Only ASCII'):
            self.check(raw_time_zone='Foo\N{SNOWMAN}Far')
        # All other variants are tested in ValidateUserTimeZone ;)


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
        with context.new_page() as page, NoLogs('django.request'):
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
