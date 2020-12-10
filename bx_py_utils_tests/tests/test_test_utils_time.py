import time
from unittest import mock

from bx_py_utils.test_utils.time import MockTimeMonotonicGenerator


def test_time_monotonic_mock():
    with mock.patch.object(time, 'monotonic', MockTimeMonotonicGenerator()):
        assert time.monotonic() == 1
        assert time.monotonic() == 2
        assert time.monotonic() == 3

    with mock.patch.object(time, 'monotonic', MockTimeMonotonicGenerator(offset=10)):
        assert time.monotonic() == 10
        assert time.monotonic() == 20
        assert time.monotonic() == 30
