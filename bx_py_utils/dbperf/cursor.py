import datetime
import json
import time

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_str

from bx_py_utils.stacktrace import get_stacktrace


try:
    from psycopg2._json import Json as PostgresJson
except ImportError:
    PostgresJson = None


class RecordingCursorWrapper:
    """
    An implementation of django.db.backends.utils.CursorWrapper.

    It exposes the same public interface, but logs executed queries
    to the provided logger before delegating them to the wrapped cursor.
    """

    def __init__(self, cursor, db, logger, collect_stacktrace=None):
        self.cursor = cursor
        self.db = db
        self.logger = logger  # must implement 'record' method

        if collect_stacktrace is None:
            self.get_stacktrace = get_stacktrace
        else:
            self.get_stacktrace = collect_stacktrace

    def __getattr__(self, attr):
        return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def _quote_expr(self, element):
        if isinstance(element, str):
            return "'%s'" % element.replace("'", "''")
        else:
            return repr(element)

    def _quote_params(self, params):
        if not params:
            return params
        if isinstance(params, dict):
            return {key: self._quote_expr(value) for key, value in params.items()}
        return [self._quote_expr(p) for p in params]

    def _decode(self, param):
        if PostgresJson and isinstance(param, PostgresJson):
            return param.dumps(param.adapted)

        # decode each item separately for data containers
        if isinstance(param, (tuple, list)):
            return [self._decode(element) for element in param]
        if isinstance(param, dict):
            return {key: self._decode(value) for key, value in param.items()}

        # make sure datetime, date and time are converted to string by force_str
        CONVERT_TYPES = (datetime.datetime, datetime.date, datetime.time)
        try:
            return force_str(param, strings_only=not isinstance(param, CONVERT_TYPES))
        except UnicodeDecodeError:
            return repr(param)

    def _record(self, method, sql, params):
        start = time.monotonic()
        try:
            return method(sql, params)
        finally:
            stop = time.monotonic()
            duration = (stop - start) * 1000

            try:
                _params_decoded = json.dumps(self._decode(params), cls=DjangoJSONEncoder)
            except TypeError:
                _params_decoded = ''  # object not JSON serializable, we have to live with that

            sql = str(sql)  # is sometimes an object, e.g. psycopg Composed, so ensure string
            stacktrace = self.get_stacktrace()

            self.logger.record(**{
                'alias': getattr(self.db, 'alias', 'default'),
                'vendor': getattr(self.db.connection, 'vendor', 'unknown'),
                'raw_sql': sql,
                'sql': self.db.ops.last_executed_query(
                    self.cursor,
                    sql,
                    self._quote_params(params)
                ),
                'raw_params': params,
                'params': _params_decoded,
                'duration': duration,
                'stacktrace': stacktrace,
            })

    def callproc(self, procname, params=None):
        return self._record(self.cursor.callproc, procname, params)

    def execute(self, sql, params=None):
        return self._record(self.cursor.execute, sql, params)

    def executemany(self, sql, param_list):
        return self._record(self.cursor.executemany, sql, param_list)
