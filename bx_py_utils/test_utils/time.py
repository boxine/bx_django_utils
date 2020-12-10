class MockTimeMonotonicGenerator:
    """
    Helper to mock time.monotonic() in tests.

    e.g.:

    class FooBar(TestCase):
        @mock.patch.object(time, 'monotonic', MockTimeMonotonicGenerator())
        def test_something(self):
            ...
    """

    def __init__(self, offset=1):
        self.offset = offset
        self.num = 0

    def __call__(self):
        self.num += self.offset
        return self.num
