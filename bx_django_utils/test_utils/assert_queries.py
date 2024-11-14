import collections
import re
from collections import Counter
from difflib import unified_diff
from pathlib import Path
from pprint import pformat

from bx_py_utils.test_utils.snapshot import assert_snapshot

from bx_django_utils.dbperf.query_recorder import SQLQueryRecorder
from bx_django_utils.stacktrace import StacktraceAfter


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
    Assert executed database queries: Check table names, duplicate/similar Queries.

    Example usage:

        with AssertQueries(query_explain=True) as queries:
            func_that_makes_queries()
        queries.assert_queries(
            query_count=3,
            table_names=['foo','bar'],
            double_tables=True,
            duplicated=True,
            similar=True,
        )

    More example can be found in tests, here:
        bx_django_utils_tests/tests/test_assert_queries.py
    """

    def __init__(
        self,
        databases=None,
        after_modules=None,
        query_explain=False,  # Capture EXPLAIN SQL information?
        max_stacktrace=3,  # How many stack line should be displayed in SQL listing?
    ):
        if after_modules is None:
            after_modules = DEFAULT_AFTER_MODULES

        collect_stacktrace = StacktraceAfter(after_modules=after_modules)
        super().__init__(
            databases=databases, collect_stacktrace=collect_stacktrace, query_explain=query_explain
        )
        assert (
            isinstance(max_stacktrace, int) and max_stacktrace >= 0
        ), f'invalid max_stacktrace: {max_stacktrace!r}'
        self.max_stacktrace = max_stacktrace

    @staticmethod
    def get_table_name(query):
        sql = query['sql']
        if sql.startswith('SAVEPOINT') or sql.startswith('RELEASE SAVEPOINT'):
            # transaction statements
            return

        table_name_match = re.search(
            r'(?:FROM|INSERT[A-Z ]+?INTO|UPDATE)\s+(?:(?P<unquoted>[a-zA-Z][_\w]+)|\"(?P<quoted>.+?)\")', sql
        )
        assert table_name_match, f'Error parsing: {sql!r}'
        table_name = table_name_match.group('unquoted') or table_name_match.group('quoted')
        return table_name

    def count_table_names(self):
        table_name_count = Counter()
        for _db, query in self.logger._queries:
            table_name = self.get_table_name(query)
            if table_name:
                table_name_count[table_name] += 1

        return table_name_count

    def get_explains(self):
        """
        Yields DB table name and captured SQL explain information.
        """
        assert self.query_explain, 'Explain way not captured!'

        for _db, query in self.logger._queries:
            table_name = self.get_table_name(query)
            explain_str = '\n'.join(query['explain'])

            yield table_name, explain_str

    def get_explain_dict(self):
        """
        Generate a dict with database table name and SQL explain entry.
        """
        result = collections.defaultdict(list)
        for table_name, explain_str in self.get_explains():
            result[table_name].append(explain_str)
        return dict(result)

    @property
    def query_info(self) -> str:
        """
        :return: Human readable information about the executed SQL queries
        """
        parts = []
        for i, (_db, query) in enumerate(self.logger._queries, start=1):
            parts.append(f'{i:>3}. {query["sql"]}')

            if self.max_stacktrace:
                stacktrace = query['stacktrace']
                stack_count = len(stacktrace)
                if stack_count > self.max_stacktrace:
                    parts.append('    ...')
                else:
                    parts.append('\n')

                max_lines_slice = -self.max_stacktrace
                stacktrace = stacktrace[max_lines_slice:]

                start_no = stack_count - self.max_stacktrace + 1
                for frame_no, frameinfo in enumerate(stacktrace, start=start_no):
                    parts.append(
                        f'    {frame_no:>2}.'
                        f'{frameinfo.filename} {frameinfo.line} {frameinfo.func}():'
                    )
                    parts.append(f'        {frameinfo.code!r}')
                parts.append('\n')

            if self.query_explain:
                for explain_line in query['explain']:
                    parts.append(f'    {explain_line}')
                parts.append('')

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

    def assert_table_counts(self, table_counts: Counter | dict, exclude: tuple[str, ...] | None = None):
        if not isinstance(table_counts, Counter):
            table_counts = Counter(table_counts)
        table_name_count = self.count_table_names()
        if exclude:
            for k in exclude:
                assert k not in table_counts, f'Excluded key {k!r} is listed in table_counts'
                if k in table_name_count:
                    del table_name_count[k]
        if table_counts != table_name_count:
            diff = counter_diff(
                c1=table_counts,
                c2=table_name_count,
                fromfile='expected table counts',
                tofile='current table counts'
            )
            msg = f'Table count error:\n{diff}\n'

            # Add copy&paste text to make updating the test easy:
            sorted_dict = dict(sorted((k, v) for k, v in table_name_count.items()))
            msg += f'Got these counts:\n{pformat(sorted_dict)}\n\n'

            raise AssertionError(self.build_error_message(msg))

    def snapshot_table_counts(self, *, exclude: tuple[str] | None = None, **kwargs):
        table_name_count = self.count_table_names()
        if exclude:
            for k in exclude:
                if k in table_name_count:
                    del table_name_count[k]
        assert_snapshot(got=table_name_count, self_file_path=Path(__file__), **kwargs)

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
        table_counts: Counter | dict | None = None,
        double_tables: bool | None = True,
        table_names: list[str] | None = None,
        query_count: int | None = None,
        duplicated: bool | None = True,
        similar: bool | None = True,
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
