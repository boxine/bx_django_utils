import datetime
from unittest import mock

from django.utils import timezone

from bx_py_utils.test_utils.datetime import MockDatetimeGenerator


def test_daetime_timezone_now_mock():
    with mock.patch.object(timezone, 'now', MockDatetimeGenerator()):
        assert timezone.now() == datetime.datetime(2001, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
        assert timezone.now() == datetime.datetime(2002, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
        assert timezone.now() == datetime.datetime(2003, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

    offset = datetime.timedelta(minutes=1)
    with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)):
        assert timezone.now() == datetime.datetime(2000, 1, 1, 0, 1, tzinfo=datetime.timezone.utc)
        assert timezone.now() == datetime.datetime(2000, 1, 1, 0, 2, tzinfo=datetime.timezone.utc)
        assert timezone.now() == datetime.datetime(2000, 1, 1, 0, 3, tzinfo=datetime.timezone.utc)
