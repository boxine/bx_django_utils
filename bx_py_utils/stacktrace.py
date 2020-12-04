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


def _exclude(file, excluded_modules):
    excluded_paths = []
    for module in excluded_modules:
        module = import_module(module)
        source_path = inspect.getsourcefile(module)
        if source_path.endswith('__init__.py'):
            source_path = os.path.dirname(source_path)
        excluded_paths.append(os.path.realpath(source_path))

    return any(file.startswith(excluded_path) for excluded_path in excluded_paths)


def get_stacktrace(tidy=True, exclude_modules=DEFAULT_EXCLUDED_MODULES):
    """
    Returns a StackTrace object, which is a list of FrameInfo objects.
    This construct contains information about the current stacktrace in an easy-to-process format.

    Optionally, you can filter the contained FrameInfo items via the ``tidy`` and ``exclude_modules``.
    Frames from modules in ``exclude_modules`` will we stripped if ``tidy`` is True.
    """
    stacktrace = StackTrace()

    previous_frame = sys._getframe(1)
    while previous_frame:
        file, line, func, code, _ = inspect.getframeinfo(previous_frame, context=1)
        file = os.path.realpath(file)  # make it an absolute path
        code = code[0].strip()  # 0 is safe because we always have context=1

        if not tidy:
            stacktrace.append(FrameInfo(file, line, func, code))
        if tidy and not _exclude(file, exclude_modules):
            stacktrace.append(FrameInfo(file, line, func, code))

        previous_frame = previous_frame.f_back

    return stacktrace
