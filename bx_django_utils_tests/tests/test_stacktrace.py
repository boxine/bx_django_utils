from bx_py_utils.test_utils.assertion import assert_equal
from django.test import TestCase

from bx_django_utils.stacktrace import get_stacktrace, iter_frameinfo


def foo():
    exclude_modules = (  # keep the test stacktrace minimal
        'unittest',
        'django.test',
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

        current_info = []
        for frameinfo in out:
            # only make rough assertions on file, line and locals_, they are too volatile
            assert isinstance(frameinfo.filename, str)
            assert len(frameinfo.filename) > 0
            assert isinstance(frameinfo.line, int)

            if 'test_stacktrace.py' in frameinfo.filename:
                # Just collect the "well known" entries
                current_info.append((frameinfo.func, frameinfo.code))

        expected = [
            ('test_get_stacktrace_output', 'out = baz()'),
            ('baz', 'return bar()'),
            ('bar', 'return foo()'),
            ('foo', 'return get_stacktrace(exclude_modules=exclude_modules)'),
        ]
        assert_equal(current_info, expected)
