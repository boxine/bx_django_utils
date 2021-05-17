import difflib

from bx_py_utils.humanize.pformat import pformat


def text_ndiff(txt1, txt2):
    """
    Generate a ndiff between two text strings.
    """
    return '\n'.join(difflib.ndiff(txt1.splitlines(), txt2.splitlines()))


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


def assert_text_equal(txt1, txt2, msg=None):
    """
    Check if the two text strings are the same. Display a error message with a ndiff.
    """
    assert isinstance(txt1, str)
    assert isinstance(txt2, str)
    if txt1 != txt2:
        if not msg:
            msg = 'Text not equal:'
        raise AssertionError(f'{msg}\n{text_ndiff(txt1, txt2)}')
