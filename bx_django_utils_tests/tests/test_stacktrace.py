from django.test import TestCase

from bx_django_utils.stacktrace import get_stacktrace, iter_frameinfo
from bx_django_utils.test_utils.assertion import assert_equal


def foo():
    exclude_modules = (  # keep the test stacktrace minimal
        'unittest',
        'django.test',
        'pluggy',
        '_pytest',
        'pytest',
        'runpy',
    )
    return get_stacktrace(exclude_modules=exclude_modules)


def bar():
    return foo()


def baz():
    return bar()


class StacktraceTestCase(TestCase):

    def test_iter_frameinfo_offset(self):
        result = [func for file, line, func, code in iter_frameinfo()]
        assert result[0] == 'test_iter_frameinfo_offset'

    def test_get_stacktrace(self):
        stacktrace = get_stacktrace(tidy=False)
        last_frame = stacktrace[-1]
        assert last_frame.func == 'test_get_stacktrace'
        assert last_frame.code == 'stacktrace = get_stacktrace(tidy=False)'

    def test_get_stacktrace_output(self):
        out = baz()

        if out[0].func == '<module>':
            # cut off first entry, it's from the test runner binary and can't be
            # ignored by exclude_modules
            out = out[1:]

        expected = [
            ('test_get_stacktrace_output', 'out = baz()'),
            ('baz', 'return bar()'),
            ('bar', 'return foo()'),
            ('foo', 'return get_stacktrace(exclude_modules=exclude_modules)'),
        ]
        current_info = []
        for frameinfo in out:
            # only make rough assertions on file, line and locals_, they are too volatile
            assert isinstance(frameinfo.filename, str)
            assert len(frameinfo.filename) > 0
            assert isinstance(frameinfo.line, int)

            current_info.append(
                (frameinfo.func, frameinfo.code)
            )

        assert_equal(current_info, expected)
