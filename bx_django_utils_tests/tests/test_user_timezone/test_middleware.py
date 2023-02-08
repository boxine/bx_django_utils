import logging
import zoneinfo

from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone

from bx_django_utils.user_timezone.middleware import UserTimezoneMiddleware


DEFAULT_TIMEZONE = zoneinfo.ZoneInfo('America/Los_Angeles')


class UserTimezoneMiddlewareTestCase(SimpleTestCase):
    @timezone.override(DEFAULT_TIMEZONE)
    def test_middleware(self):
        self.assertEqual(timezone.get_current_timezone(), DEFAULT_TIMEZONE)

        def fake_get_response(request):
            return f'User timezone: "{timezone.get_current_timezone()}"'

        middleware = UserTimezoneMiddleware(get_response=fake_get_response)
        fake_request = RequestFactory().get('/foo/bar')

        ##########################################################################
        # No cookie set -> don't change current/default timezone:
        fake_response = middleware(request=fake_request)
        self.assertEqual(fake_response, 'User timezone: "America/Los_Angeles"')
        self.assertEqual(timezone.get_current_timezone(), DEFAULT_TIMEZONE)  # not changed?

        ##########################################################################
        # Temporary change timezone via cookie to: 'Europe/Berlin'
        fake_request.COOKIES['UserTimeZone'] = 'Europe/Berlin'
        fake_response = middleware(request=fake_request)
        self.assertEqual(fake_response, 'User timezone: "Europe/Berlin"')
        self.assertEqual(timezone.get_current_timezone(), DEFAULT_TIMEZONE)  # reset?

        ##########################################################################
        # Temporary change timezone via cookie to: 'Europe/London'
        fake_request.COOKIES['UserTimeZone'] = 'Europe/London'
        fake_response = middleware(request=fake_request)
        self.assertEqual(fake_response, 'User timezone: "Europe/London"')
        self.assertEqual(timezone.get_current_timezone(), DEFAULT_TIMEZONE)  # reset?

        ##########################################################################
        # If nonsense is in cookie -> just log a error and don't change the default timezone:
        fake_request.COOKIES['UserTimeZone'] = 'non/sense'
        with self.assertLogs(logger='bx_django_utils', level=logging.ERROR) as logs:
            fake_response = middleware(request=fake_request)

        # Default time zone?
        self.assertEqual(fake_response, 'User timezone: "America/Los_Angeles"')
        self.assertEqual(timezone.get_current_timezone(), DEFAULT_TIMEZONE)

        self.assertEqual(
            logs.output,
            [
                "ERROR:bx_django_utils.user_timezone.middleware:"
                "Unknown user time zone 'non/sense'"
            ],
        )
