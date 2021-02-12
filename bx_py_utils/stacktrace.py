import inspect
import os
import sys
from importlib import import_module


DEFAULT_EXCLUDED_MODULES = (
    'socketserver',
    'threading',
    'wsgiref',
    'bx_py_utils',
    'django.db',
    'django.core.handlers',
    'django.core.servers',
    'django.utils.decorators',
    'django.utils.deprecation',
    'django.utils.functional',
)


class StackTrace(list):
    pass


class FrameInfo:
    def __init__(self, filename, line, func, code):
        self.filename = filename
        self.line = line
        self.func = func
        self.code = code

    def __str__(self):
        return f'{self.filename} {self.line} {self.func!r} {self.code!r}'

    def __repr__(self):
        return f'<FrameInfo {self}>'


def _exclude(file, excluded_modules):
    excluded_paths = []
    for module in excluded_modules:
        module = import_module(module)
        source_path = inspect.getsourcefile(module)
        if source_path.endswith('__init__.py'):
            source_path = os.path.dirname(source_path)
        excluded_paths.append(os.path.realpath(source_path))

    return any(file.startswith(excluded_path) for excluded_path in excluded_paths)


def iter_frameinfo(start_no=2):
    previous_frame = sys._getframe(start_no)
    while previous_frame:
        file, line, func, code, _ = inspect.getframeinfo(previous_frame, context=1)
        file = os.path.realpath(file)  # make it an absolute path
        code = code[0].strip()  # 0 is safe because we always have context=1

        yield (file, line, func, code)

        previous_frame = previous_frame.f_back


def get_stacktrace(tidy=True, exclude_modules=DEFAULT_EXCLUDED_MODULES):
    """
    Returns a StackTrace object, which is a list of FrameInfo objects.
    This construct contains information about the current stacktrace in an easy-to-process format.

    Optionally, you can filter the contained FrameInfo items via the ``tidy`` and ``exclude_modules``.
    Frames from modules in ``exclude_modules`` will we stripped if ``tidy`` is True.
    """
    stacktrace = StackTrace()

    for file, line, func, code in iter_frameinfo():
        if not tidy:
            stacktrace.append(FrameInfo(file, line, func, code))
        if tidy and not _exclude(file, exclude_modules):
            stacktrace.append(FrameInfo(file, line, func, code))

    stacktrace.reverse()
    return stacktrace


class StacktraceAfter:
    """
    Generate a stack trace after a package was visited.
    e.g.:
    After the code path used "django.db", to get the initial code that caused a database query.
    """

    def __init__(self, after_modules):
        self.after_modules = after_modules

    def __call__(self):
        stacktrace = StackTrace()

        before = True  # before we visit self.after_modules modules code
        after = False  # after we left self.after_modules modules code

        for file, line, func, code in iter_frameinfo(start_no=3):
            if before and not _exclude(file, self.after_modules):
                before = False
                continue

            if not after and not _exclude(file, self.after_modules):
                after = True

            if after:
                stacktrace.append(FrameInfo(file, line, func, code))

        stacktrace.reverse()
        return stacktrace
