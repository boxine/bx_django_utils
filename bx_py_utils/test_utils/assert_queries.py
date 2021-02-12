import re
from collections import Counter
from difflib import unified_diff
from typing import List, Optional

from bx_py_utils.dbperf.query_recorder import SQLQueryRecorder
from bx_py_utils.stacktrace import StacktraceAfter


def counter_diff(c1, c2, fromfile=None, tofile=None):
    def pformat(counter):
        lines = []
        for key, value in counter.items():
            lines.append(f'{key}: {value}\n')
        return sorted(lines)

    return ''.join(unified_diff(
        a=pformat(c1),
        b=pformat(c2),
        fromfile=fromfile,
        tofile=tofile
    ))


DEFAULT_AFTER_MODULES = (
    'django.db',
)


class AssertQueries(SQLQueryRecorder):
    """
    Assert executed database queries.

    Example usage:

        with AssertQueries() as queries:
            func_that_makes_queries()
        queries.assert_queries(
            query_count=3,
            table_names=['foo','bar'],
            double_tables=True,
            duplicated=True,
            similar=True,
        )

    More example can be found in tests, here:
        bx_py_utils_tests/tests/test_assert_queries.py
    """

    def __init__(self, databases=None, after_modules=None):
        if after_modules is None:
            after_modules = DEFAULT_AFTER_MODULES

        collect_stacktrace = StacktraceAfter(after_modules=after_modules)
        super().__init__(databases=databases, collect_stacktrace=collect_stacktrace)

    def count_table_names(self):
        table_name_count = Counter()
        for db, query in self.logger._queries:
            sql = query['sql']
            table_name = re.findall(r' FROM "(.+?)" ', sql)
            assert len(table_name) == 1, f'Error parsing: {sql!r}'
            table_name = table_name[0]
            table_name_count[table_name] += 1

        return table_name_count

    @property
    def query_info(self):
        parts = []
        for i, (db, query) in enumerate(self.logger._queries, start=1):
            stacktrace = query['stacktrace']
            frameinfo = stacktrace[-1]

            parts.append(
                f'{i:>3}. {query["sql"]}\n'
                f'    {frameinfo.filename} {frameinfo.line} {frameinfo.func!r}\n'
                f'    {frameinfo.code!r}\n'
            )

        return '\n'.join(parts)

    def build_error_message(self, msg):
        return (
            f'{msg}\n'
            f'Captured queries were:\n'
            f'{self.query_info}'
        )

    def assert_table_names(self, *expected_table_names):
        """
        Check tables are used.
        """
        expected_table_names = set(expected_table_names)

        table_name_count = self.count_table_names()
        used_tables = set(table_name_count.elements())

        if expected_table_names != used_tables:
            diff = ''.join(unified_diff(
                sorted(f'{n}\n' for n in expected_table_names),
                sorted(f'{n}\n' for n in used_tables),
                fromfile='expected table names',
                tofile='used table names'
            ))
            raise AssertionError(self.build_error_message(f'Table names does not match:\n{diff}'))

    def assert_table_counts(self, table_counts: Counter):
        table_name_count = self.count_table_names()
        if table_counts != table_name_count:
            diff = counter_diff(
                c1=table_counts,
                c2=table_name_count,
                fromfile='expected table counts',
                tofile='current table counts'
            )
            raise AssertionError(self.build_error_message(f'Table count error:\n{diff}'))

    def assert_not_double_tables(self):
        """
        Check if tables are used more than one time.
        """
        table_name_count = self.count_table_names()

        double_names = {
            table_name
            for table_name, count in table_name_count.items()
            if count > 1
        }
        assert not double_names, self.build_error_message(
            f'These tables was double used:\n{double_names}'
        )

    def assert_duplicated_queries(self, duplicated=True, similar=True):
        """
        Check similar and/or duplicated queries
        """
        assert duplicated or similar

        results = self.logger.dump(aggregate_queries=True)
        num_queries_duplicated = results['num_queries_duplicated']
        num_queries_similar = results['num_queries_similar']

        if duplicated and similar:
            assert num_queries_duplicated == 0 and num_queries_similar == 0, \
                self.build_error_message(
                    f'There are {num_queries_duplicated} duplicated'
                    f' and {num_queries_similar} similar queries.'
                )
        elif duplicated:
            assert num_queries_duplicated == 0, self.build_error_message(
                f'There are {num_queries_duplicated} duplicated queries.'
            )
        elif similar:
            assert num_queries_similar == 0, self.build_error_message(
                f'There are {num_queries_similar} similar queries.'
            )

    def assert_query_count(self, num):
        """
        Check the total executed database query count.
        Similar to: self.assertNumQueries(num=123)
        """
        captured_queries = self.logger._queries
        queries_count = len(captured_queries)
        if num != queries_count:
            raise AssertionError(
                self.build_error_message(f'{queries_count} queries executed, {num} expected.')
            )

    def assert_queries(
        self,
        table_counts: Optional[Counter] = None,
        double_tables: Optional[bool] = True,
        table_names: Optional[List[str]] = None,
        query_count: Optional[int] = None,
        duplicated: Optional[bool] = True,
        similar: Optional[bool] = True,
    ):
        """
        Shortcut to assert everything
        """
        if table_counts is not None:
            self.assert_table_counts(table_counts=table_counts)

        if double_tables:
            self.assert_not_double_tables()

        if table_names is not None:
            self.assert_table_names(*table_names)

        if query_count is not None:
            self.assert_query_count(num=query_count)

        if duplicated or similar:
            self.assert_duplicated_queries(duplicated=duplicated, similar=similar)
