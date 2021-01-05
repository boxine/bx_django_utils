import os
from unittest import TestCase

from bx_py_utils.processify import processify


@processify
def _test_function():
    return os.getpid()


@processify
def _test_deadlock():
    return range(30000)


@processify
def _test_exception():
    raise RuntimeError('xyz')


class ProcessifyTestCase(TestCase):
    def test(self):
        assert os.getpid() != _test_function()

        assert len(_test_deadlock()) == 30000

        self.assertRaises(RuntimeError, _test_exception)
