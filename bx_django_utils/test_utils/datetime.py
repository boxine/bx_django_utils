import datetime
from contextlib import ContextDecorator
from unittest.mock import patch

from bx_py_utils.test_utils.context_managers import MassContextManager
from bx_py_utils.test_utils.datetime import parse_dt
from django.utils import timezone


class MockDatetimeGenerator:
    """
    Mock django `timezone.now()` with generic time stamps in tests.

    Note: Set a lower offset if you use the Django test client!
          By default every timezone.now() will increase by 1 Year,
          so a session is practically always expired ;)

    e.g.:

    class FooBar(TestCase):
        @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
        def test_something_without_test_client(self):
            ...

    or:

    def test_foobar():
        offset = datetime.timedelta(minutes=1)
        with mock.patch.object(timezone, 'now', MockDatetimeGenerator(offset=offset)):
            ...
    """

    def __init__(self, offset=None):
        if offset is not None:
            assert isinstance(offset, datetime.timedelta)
            self.now = datetime.datetime(
                2000, 1, 1, 0, 0, 0,
                tzinfo=datetime.timezone.utc
            )
        else:
            self.now = None

        self.offset = offset
        self.num = 0

    def __call__(self):
        if self.offset is None:
            self.num += 1
            dt = datetime.datetime(
                2000 + self.num, 1, 1, 0, 0, 0,
                tzinfo=datetime.timezone.utc
            )
            return dt
        else:
            self.now += self.offset
            return self.now


class FreezeTimezoneNow(ContextDecorator, MassContextManager):
    """
    Context manager / Decorator to mock django.utils.timezone.now() with a fixed datetime.
    """

    def __init__(self, now: str = '2000-01-02T00:00:00+0000'):
        now_dt = parse_dt(now)
        self.mocks = (patch.object(timezone, 'now', return_value=now_dt),)
