import difflib

from bx_py_utils.humanize.pformat import pformat


def pformat_ndiff(obj1, obj2):
    """
    Generate a ndiff from two objects, using pformat()
    """
    return '\n'.join(
        difflib.ndiff(
            pformat(obj1).splitlines(),
            pformat(obj2).splitlines()
        )
    )


def assert_equal(obj1, obj2, msg=None):
    """
    Check if the two objects are the same. Display a nice diff, using pformat()
    """
    if obj1 != obj2:
        if not msg:
            msg = 'Objects are not equal:'
        raise AssertionError(f'{msg}\n{pformat_ndiff(obj1,obj2)}')
