from collections import Counter
from unittest import mock

from django.contrib.auth.models import Permission
from django.test import TestCase

from bx_py_utils import stacktrace
from bx_py_utils.test_utils.assert_queries import AssertQueries


def make_database_queries(count=1):
    for i in range(count):
        Permission.objects.all().first()


class AssertQueriesTestCase(TestCase):

    def get_instance(self):
        with AssertQueries() as queries:
            Permission.objects.all().first()
        return queries

    def test_assert_queries(self):
        queries = self.get_instance()
        queries.assert_queries(
            query_count=1,
            table_names=['auth_permission'],
            double_tables=True,
            duplicated=True,
            similar=True,
        )

    def test_assert_table_names(self):
        queries = self.get_instance()
        queries.assert_table_names('auth_permission')

        with self.assertRaises(AssertionError) as err:
            queries.assert_table_names('foo', 'bar')
        msg = str(err.exception)
        assert 'Table names does not match:' in msg
        assert '-bar\n' in msg
        assert '-foo\n' in msg
        assert '+auth_permission\n' in msg
        assert 'Captured queries were:\n' in msg
        assert '1. SELECT "auth_permission"' in msg

    def test_assert_table_counts(self):
        queries = self.get_instance()
        queries.assert_table_counts(Counter(auth_permission=1))

        with self.assertRaises(AssertionError) as err:
            queries.assert_table_counts(Counter(auth_permission=2, foo=1, bar=3))
        msg = str(err.exception)
        assert 'Table count error:\n' in msg
        assert '-auth_permission: 2\n' in msg
        assert '-bar: 3\n' in msg
        assert '-foo: 1\n' in msg
        assert '+auth_permission: 1\n' in msg
        assert 'Captured queries were:\n' in msg
        assert '1. SELECT "auth_permission"' in msg

    def test_assert_not_double_tables(self):
        queries = self.get_instance()
        queries.assert_not_double_tables()

        with self.assertRaises(AssertionError) as err:
            with AssertQueries() as queries:
                Permission.objects.all().first()
                Permission.objects.all().first()
            queries.assert_not_double_tables()
        msg = str(err.exception)
        assert 'These tables was double used:\n' in msg
        assert "{'auth_permission'}\n" in msg
        assert 'Captured queries were:\n' in msg
        assert '1. SELECT "auth_permission"' in msg
        assert '2. SELECT "auth_permission"' in msg

    def test_assert_duplicated_queries(self):
        queries = self.get_instance()
        queries.assert_duplicated_queries(duplicated=True, similar=True)

        # duplicated + similar

        with self.assertRaises(AssertionError) as err, \
                AssertQueries() as queries:
            Permission.objects.all().first()  # Query 1
            Permission.objects.all().first()  # Query 2
            queries.assert_duplicated_queries(duplicated=True, similar=True)
        msg = str(err.exception)
        assert 'There are 1 duplicated and 1 similar queries.\n' in msg
        assert 'Captured queries were:\n' in msg

        assert '1. SELECT "auth_permission"' in msg
        assert 'bx_py_utils_tests/tests/test_assert_queries.py' in msg
        assert "'test_assert_duplicated_queries'\n" in msg
        assert "Permission.objects.all().first()  # Query 1" in msg

        assert '2. SELECT "auth_permission"' in msg
        assert "Permission.objects.all().first()  # Query 2" in msg

        # no duplicated, but similar

        with self.assertRaises(AssertionError) as err, \
                AssertQueries() as queries:
            Permission.objects.exclude(name='query 3').first()
            Permission.objects.exclude(name='query 4').first()
            queries.assert_duplicated_queries(duplicated=True, similar=True)
        msg = str(err.exception)
        assert 'There are 0 duplicated and 1 similar queries.\n' in msg
        assert 'Captured queries were:\n' in msg
        assert '1. SELECT "auth_permission"' in msg
        assert "Permission.objects.exclude(name='query 3').first()" in msg
        assert '2. SELECT "auth_permission"' in msg
        assert "Permission.objects.exclude(name='query 4').first()" in msg

        # only duplicated

        with self.assertRaises(AssertionError) as err, \
                AssertQueries() as queries:
            Permission.objects.all().first()  # Query 5
            Permission.objects.all().first()  # Query 6
            queries.assert_duplicated_queries(duplicated=True, similar=False)
        msg = str(err.exception)
        assert 'There are 1 duplicated queries.\n' in msg
        assert 'Captured queries were:\n' in msg
        assert '1. SELECT "auth_permission"' in msg
        assert "Permission.objects.all().first()  # Query 5" in msg
        assert '2. SELECT "auth_permission"' in msg
        assert "Permission.objects.all().first()  # Query 6" in msg

        # only similar

        with self.assertRaises(AssertionError) as err, \
                AssertQueries() as queries:
            Permission.objects.exclude(name='query 7').first()
            Permission.objects.exclude(name='query 8').first()
            queries.assert_duplicated_queries(duplicated=False, similar=True)
        msg = str(err.exception)
        assert 'There are 1 similar queries.\n' in msg
        assert 'Captured queries were:\n' in msg
        assert '1. SELECT "auth_permission"' in msg
        assert "Permission.objects.exclude(name='query 7').first()" in msg
        assert '2. SELECT "auth_permission"' in msg
        assert "Permission.objects.exclude(name='query 8').first()" in msg

    def test_assert_query_count(self):
        queries = self.get_instance()
        queries.assert_query_count(num=1)

        with self.assertRaises(AssertionError) as err:
            queries.assert_query_count(num=2)
        msg = str(err.exception)
        assert '1 queries executed, 2 expected.\n' in msg
        assert 'Captured queries were:\n' in msg
        assert '1. SELECT "auth_permission"' in msg
