import sys


TRACEBACK_MAX_CHARS = 100

DEFAULT_STOP_ON_FILE_PATH = (
    '/django/core/handlers/base.py',
    'django/core/management/base.py',
    'django/core/handlers/exception.py',
    f'/python{".".join(str(v) for v in sys.version_info[:2])}/wsgiref'
)


def print_exc_plus(exc=None, stop_on_file_path=None, max_chars=None):
    """ Print traceback information with a listing of all the local variables in each frame. """
    if exc is None:
        tb = sys.exc_info()[2]
    else:
        tb = exc.__traceback__  # FIXME: How to get the Traceback object better?

    while tb.tb_next:
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back

    print_local_vars = True

    if stop_on_file_path is None:
        stop_on_file_path = DEFAULT_STOP_ON_FILE_PATH

    if max_chars is None:
        max_chars = TRACEBACK_MAX_CHARS

    print(' -' * 50, file=sys.stderr)
    print('Locals by frame, most recent call first:', file=sys.stderr)
    for frame in stack:
        file_path = frame.f_code.co_filename
        print(
            f'\n File "{file_path}", line {frame.f_lineno}, in {frame.f_code.co_name}',
            end='',
            flush=True,
            file=sys.stderr)

        if stop_on_file_path and print_local_vars:
            for path_part in stop_on_file_path:
                if path_part in file_path:
                    print_local_vars = False
                    break

        if print_local_vars:
            print(file=sys.stderr)
            for key, value in list(frame.f_locals.items()):
                print('%30s =' % key, end=' ', file=sys.stderr)

                # We have to be careful not to cause a new error in our error
                # printer! Calling str() on an unknown object could cause an
                # error we don't want.
                value = repr(value)

                if len(value) + 3 > max_chars:
                    value = f'{value[:max_chars-3]}...'

                try:
                    print(value, file=sys.stderr)
                except BaseException:
                    print('<ERROR WHILE PRINTING VALUE>', file=sys.stderr)

    print(file=sys.stderr)
    print('=' * 100, file=sys.stderr)
