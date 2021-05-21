"""
https://gist.github.com/Chiron1991/8199fc1a41c2107982053aba809838c6

tests functions from the gist were moved to utilities.tests.test_processify
so they can be picked up by our test runner
"""

import sys
import traceback
from functools import wraps
from multiprocessing import Process, Queue


def processify(func):
    """
    Decorator to run a function as a process.
    Be sure that every argument and the return value
    is *pickable*.
    The created process is joined, so the code does not
    run in parallel.
    """

    def process_func(q, *args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except Exception:
            ex_type, ex_value, tb = sys.exc_info()
            error = ex_type, ex_value, ''.join(traceback.format_tb(tb))
            ret = None
        else:
            error = None

        q.put((ret, error))

    # register original function with different name
    # in sys.modules so it is pickable
    process_func.__name__ = func.__name__ + 'processify_func'
    setattr(sys.modules[__name__], process_func.__name__, process_func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        q = Queue()
        p = Process(target=process_func, args=(q,) + args, kwargs=kwargs)
        p.start()
        ret, error = q.get()
        p.join()

        if error:
            ex_type, ex_value, tb_str = error
            message = f'{str(ex_value)} (in subprocess)\n{tb_str}'
            raise ex_type(message)

        return ret

    return wrapper
