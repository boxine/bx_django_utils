from django.conf import settings
from django.test import SimpleTestCase, override_settings

from bx_django_utils.user_timezone.checks import user_timezone_check


class ChecksTestCase(SimpleTestCase):
    def test_w001(self):
        errors = user_timezone_check(app_configs=None)
        self.assertEqual(errors, [])

        with self.settings(MIDDLEWARE=[]):
            errors = user_timezone_check(app_configs=None)
        self.assertEqual(len(errors), 1)
        warning = errors[0]
        self.assertEqual(warning.id, 'user_timezone.W001')
        self.assertEqual(warning.msg, 'Missing UserTimezoneMiddleware')

    @override_settings()
    def test_e001(self):
        del settings.VISIBLE_TIMEZONES

        errors = user_timezone_check(app_configs=None)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error.id, 'user_timezone.E001')
        self.assertEqual(error.msg, 'Your settings has no "VISIBLE_TIMEZONES" defined!')

    @override_settings(VISIBLE_TIMEZONES=['Europe/Berlin', 'non/sense'])
    def test_e002(self):
        errors = user_timezone_check(app_configs=None)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error.id, 'user_timezone.E002')
        self.assertEqual(error.msg, "settings.VISIBLE_TIMEZONES entry: 'non/sense' is invalid!")
