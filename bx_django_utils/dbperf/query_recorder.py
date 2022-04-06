from collections import defaultdict
from pprint import saferepr
from typing import Callable, List, Optional

from django.db import connections

from bx_django_utils.dbperf.cursor import RecordingCursorWrapper


class Logger:
    def __init__(self):
        self._queries = []  # list of (dbname, metrics) tuples for each query that was run
        self._databases = {}  # short summary
        self._sql_time = 0  # total execution time of all queries in milliseconds
        self._num_queries = 0  # total count of queries executed

    def record(self, alias, **kwargs):
        self._queries.append((alias, kwargs))

        if alias not in self._databases:
            self._databases[alias] = {
                "time_spent": kwargs["duration"],
                "num_queries": 1,
            }
        else:
            self._databases[alias]["time_spent"] += kwargs["duration"]
            self._databases[alias]["num_queries"] += 1

        self._sql_time += kwargs['duration']
        self._num_queries += 1

    @staticmethod
    def _similar_key(query):
        return query['raw_sql']

    @staticmethod
    def _duplicate_key(query):
        raw_params = () if query['raw_params'] is None else tuple(query['raw_params'])
        # saferepr() avoids problems because of unhashable types
        # (e.g. lists) when used as dictionary keys.
        return query['raw_sql'], saferepr(raw_params)

    def _aggregate(self, results):
        aliases = set()
        # todo: defaultdicts handle very awkwardly (e.g. with Django Templates),
        #  is collections.Counter a good replacement?
        queries_similar = defaultdict(lambda: defaultdict(int))
        queries_duplicated = defaultdict(lambda: defaultdict(int))
        num_queries_similar = 0
        num_queries_duplicated = 0

        # put every query into similar/duplicated dicts to aggregate their execution count
        for alias, query in self._queries:
            aliases.add(alias)
            queries_similar[alias][self._similar_key(query)] += 1
            queries_duplicated[alias][self._duplicate_key(query)] += 1

        # now that the aggregation is done we must strip all queries in the
        # aggregation dicts that were executed only once.
        for agg_dict in (queries_similar, queries_duplicated):
            for db, queries in agg_dict.items():
                del_keys = []
                for query, count in queries.items():
                    if count == 1:
                        del_keys.append(query)
                # map(lambda key: queries.pop(key), del_keys)
                for key in del_keys:
                    del queries[key]

        # for convenience, make a total for each aggregation across all databases and queries
        for db in queries_similar:
            num_queries_similar += len(queries_similar[db])
        for db in queries_duplicated:
            num_queries_duplicated += len(queries_duplicated[db])

        results['queries_similar'] = queries_similar
        results['queries_duplicated'] = queries_duplicated
        results['num_queries_similar'] = num_queries_similar
        results['num_queries_duplicated'] = num_queries_duplicated

    def dump(self, aggregate_queries=True):
        results = {
            'queries': self._queries,
            'databases': self._databases,
            'sql_time': self._sql_time,
            'num_queries': self._num_queries,
        }

        if aggregate_queries:
            self._aggregate(results)

        return results


class SQLQueryRecorder:
    """
    A context manager that allows recording SQL queries executed during its lifetime.
    Results of the recording can be read from the recorder in various formats after
    recording has stopped.

    In environments where not all databases in settings.DATABASES are available (e.g. unittests)
    you should pass the databases you want to observe to the constructor.

    Example usage:

        with SQLQueryRecorder(query_explain=True) as rec:
            func_that_makes_queries()
        print(rec.results(aggregate_results=True))

    """
    running = None

    def __init__(
        self,
        databases: Optional[List[str]] = None,
        collect_stacktrace: Optional[Callable] = None,
        query_explain: bool = False,  # Capture EXPLAIN SQL information?
    ):
        self.logger = Logger()
        self.query_explain = query_explain

        if databases:
            self.databases = [db for db in connections.all() if db.alias in databases]
        else:
            self.databases = connections.all()

        self.collect_stacktrace = collect_stacktrace

    def __enter__(self):
        for connection in self.databases:
            assert not hasattr(connection, '_recording_cursor'), \
                'the connection\'s cursor has not been unwrapped properly in a previous run'

            # wrap Django's default cursors in RecordingCursorWrapper
            connection._recording_cursor = connection.cursor
            connection._recording_chunked_cursor = connection.chunked_cursor

            def cursor():
                return RecordingCursorWrapper(
                    connection._recording_cursor(),
                    connection,
                    self.logger,
                    collect_stacktrace=self.collect_stacktrace,
                    query_explain=self.query_explain,
                )

            def chunked_cursor():
                return RecordingCursorWrapper(
                    connection._recording_chunked_cursor(),
                    connection,
                    self.logger,
                    collect_stacktrace=self.collect_stacktrace,
                    query_explain=self.query_explain,
                )

            connection.cursor = cursor
            connection.chunked_cursor = chunked_cursor

        self.running = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for connection in self.databases:
            assert hasattr(connection, '_recording_cursor'), \
                'the connection has already been unwrapped, this should not have happened'

            # undo the cursor wrapping so the connection is 'clean' again
            del connection._recording_cursor
            del connection.cursor
            del connection.chunked_cursor

        self.running = False

    def results(self, **dump_kwargs):
        assert not self.running, 'results can only be accessed after recording has stopped'
        return self.logger.dump(**dump_kwargs)
