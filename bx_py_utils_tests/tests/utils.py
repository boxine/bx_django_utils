import datetime


class MockDatetimeGenerator:
    """
    Helper to mock datetime now in tests.
    e.g.:

    class FooBar(TestCase):
        @mock.patch.object(timezone, 'now', MockDatetimeGenerator())
        def test_foobar(self):
            ...
    """

    def __init__(self):
        self.num = 0

    def __call__(self):
        self.num += 1
        dt = datetime.datetime(
            2000 + self.num, 1, 1, 0, 0, 0,
            tzinfo=datetime.timezone.utc
        )
        return dt


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
