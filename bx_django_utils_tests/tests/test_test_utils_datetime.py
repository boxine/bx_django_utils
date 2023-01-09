import datetime
from unittest import mock

from django.test import SimpleTestCase
from django.utils import timezone

from bx_django_utils.test_utils.datetime import MockDatetimeGenerator


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
