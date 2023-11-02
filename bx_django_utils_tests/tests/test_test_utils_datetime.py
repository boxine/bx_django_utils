import datetime
from unittest import mock

from bx_py_utils.test_utils.datetime import parse_dt
from django.test import SimpleTestCase
from django.utils import timezone

from bx_django_utils.test_utils.datetime import FreezeTimezoneNow, MockDatetimeGenerator


class MockDatetimeGeneratorTestCase(SimpleTestCase):
    def test_daetime_timezone_now_mock(self):
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator()):
            assert timezone.now() == datetime.datetime(
                2001, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
            )
            assert timezone.now() == datetime.datetime(
                2002, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
            )
            assert timezone.now() == datetime.datetime(
                2003, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
            )

        offset = datetime.timedelta(minutes=1)
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)):
            assert timezone.now() == datetime.datetime(
                2000, 1, 1, 0, 1, tzinfo=datetime.timezone.utc
            )
            assert timezone.now() == datetime.datetime(
                2000, 1, 1, 0, 2, tzinfo=datetime.timezone.utc
            )
            assert timezone.now() == datetime.datetime(
                2000, 1, 1, 0, 3, tzinfo=datetime.timezone.utc
            )

    def test_freeze_timezone_now(self):
        """
        Test FreezeTimezoneNow
        """
        # Test as context manager:
        with FreezeTimezoneNow(now='2020-01-02T12:34:56+0000'):
            self.assertEqual(timezone.now(), parse_dt('2020-01-02T12:34:56+0000'))

        # Test as decorator:
        @FreezeTimezoneNow()
        def get_now():
            return timezone.now()

        self.assertEqual(get_now(), parse_dt('2000-01-02T00:00:00+0000'))
