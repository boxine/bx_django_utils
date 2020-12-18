from django.test import TestCase

from bx_py_utils.stacktrace import get_stacktrace


def foo():
    exclude_modules = (  # keep the test stacktrace minimal
        'unittest',
        'django.test',
        'pluggy',
        '_pytest',
        'pytest',
    )
    return get_stacktrace(exclude_modules=exclude_modules)


def bar():
    return foo()


def baz():
    return bar()


class StacktraceTestCase(TestCase):

    def test_get_stacktrace_output(self):
        out = baz()
        # cut off last entry, it's from the test runner binary and can't be
        # ignored by exclude_modules
        out = out[:-1]

        expected = [
            ('foo', 'return get_stacktrace(exclude_modules=exclude_modules)'),
            ('bar', 'return foo()'),
            ('baz', 'return bar()'),
            ('test_get_stacktrace_output', 'out = baz()'),
        ]

        # for file, line, func, text, locals_ in out:
        for frameinfo, expected in zip(out, expected):
            # only make rough assertions on file, line and locals_, they are too volatile
            assert isinstance(frameinfo.filename, str)
            assert len(frameinfo.filename) > 0
            assert isinstance(frameinfo.line, int)

            expected_func, expected_code = expected
            assert frameinfo.func == expected_func
            assert frameinfo.code == expected_code
