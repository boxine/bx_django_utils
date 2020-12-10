import datetime


class MockDatetimeGenerator:
    """
    Helper to mock datetime now in tests.
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


def parse_dt(dtstr):
    """
    >>> parse_dt(None) is None
    True
    >>> parse_dt('2020-01-01T00:00:00+0000')
    datetime.datetime(2020, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    """
    if dtstr is None:
        return None
    return datetime.datetime.strptime(dtstr, '%Y-%m-%dT%H:%M:%S%z')
