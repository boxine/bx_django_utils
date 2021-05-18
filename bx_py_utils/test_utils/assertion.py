import difflib

from bx_py_utils.humanize.pformat import pformat


def text_ndiff(txt1, txt2, fromfile=None, tofile=None):
    """
    Generate a ndiff between two text strings.
    (fromfile/tofile are ignored, only for compatibility with text_unified_diff signature)
    """
    return '\n'.join(difflib.ndiff(txt1.splitlines(), txt2.splitlines()))


def pformat_ndiff(obj1, obj2, fromfile=None, tofile=None):
    """
    Generate a ndiff from two objects, using pformat()
    (fromfile/tofile are ignored, only for compatibility with pformat_unified_diff signature)
    """
    return '\n'.join(
        difflib.ndiff(
            pformat(obj1).splitlines(),
            pformat(obj2).splitlines()
        )
    )


def _unified_diff(txt1, txt2, fromfile: str = 'got', tofile: str = 'expected'):
    assert isinstance(txt1, str)
    assert isinstance(txt2, str)
    return '\n'.join(
        difflib.unified_diff(
            txt1.splitlines(), txt2.splitlines(),
            fromfile=fromfile, tofile=tofile
        )
    )


def text_unified_diff(txt1, txt2, fromfile: str = 'got', tofile: str = 'expected'):
    """
    Generate a unified diff between two text strings.
    """
    return _unified_diff(txt1, txt2, fromfile=fromfile, tofile=tofile)


def pformat_unified_diff(obj1, obj2, fromfile: str = 'got', tofile: str = 'expected'):
    """
    Generate a unified diff from two objects, using pformat()
    """
    return _unified_diff(pformat(obj1), pformat(obj2), fromfile=fromfile, tofile=tofile)


def assert_equal(
        obj1,
        obj2,
        msg=None,
        fromfile: str = 'got',
        tofile: str = 'expected',
        diff_func=pformat_unified_diff):
    """
    Check if the two objects are the same. Display a nice diff, using pformat()
    """
    if obj1 != obj2:
        if not msg:
            msg = 'Objects are not equal:'
        raise AssertionError(f'{msg}\n{diff_func(obj1,obj2, fromfile=fromfile, tofile=tofile)}')


def assert_text_equal(
        txt1,
        txt2,
        msg=None,
        fromfile: str = 'got',
        tofile: str = 'expected',
        diff_func=text_unified_diff):
    """
    Check if the two text strings are the same. Display a error message with a diff.
    """
    assert isinstance(txt1, str)
    assert isinstance(txt2, str)
    if txt1 != txt2:
        if not msg:
            msg = 'Text not equal:'
        raise AssertionError(f'{msg}\n{diff_func(txt1, txt2, fromfile=fromfile, tofile=tofile)}')
