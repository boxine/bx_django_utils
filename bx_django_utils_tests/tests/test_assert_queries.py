import json
import pathlib
import tempfile
from collections import Counter

from bx_py_utils.environ import OverrideEnviron
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, Permission
from django.db import connection, transaction
from django.test import TestCase

from bx_django_utils.test_utils.assert_queries import AssertQueries


def make_database_queries(count=1):
    for _i in range(count):
        Permission.objects.all().first()


def make_database_queries2(count=1):
    make_database_queries(count)


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

    def test_get_table_name(self):
        self.assertEqual(
            AssertQueries.get_table_name(
                query={'sql': 'INSERT INTO "table_name1" ("foo_id", "bar_id") VALUES (1, 2)'}
            ),
            'table_name1',
        )
        self.assertEqual(
            AssertQueries.get_table_name(
                query={'sql': 'INSERT OR IGNORE INTO "table_name2" ("foo_id", "bar_id") VALUES (1, 2)'}
            ),
            'table_name2',
        )
        self.assertEqual(
            AssertQueries.get_table_name(
                query={
                    'sql': '''
                    SELECT
                     foo.id,
                     bar.id,
                     bar."timestamp",
                     xuu.id
                FROM foo
                    INNER JOIN bar
                        ON foo.item_id = bar.item_ptr_id
                    INNER JOIN xuu
                        ON bar.content_id = xuu.id
                '''
                }
            ),
            'foo',
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
        queries.assert_table_counts({'auth_permission': 1})

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

    def test_assert_table_counts_exclude(self):
        with AssertQueries() as queries:
            Permission.objects.all().first()
            Permission.objects.all().first()
            Group.objects.all().first()
            LogEntry.objects.all().first()

        queries.assert_table_counts(
            {'auth_permission': 2, 'django_admin_log': 1},
            exclude=('auth_group', 'not_mentioned'),
        )

        # Incorrect counts / added tables
        with self.assertRaises(AssertionError) as err:
            queries.assert_table_counts({'auth_permission': 3, 'foo': 1})
        msg = str(err.exception)
        assert 'Table count error:\n' in msg
        assert '-auth_permission: 3\n' in msg
        assert '-foo: 1\n' in msg
        assert '+auth_permission: 2\n' in msg
        assert 'Captured queries were:\n' in msg
        assert 'Got these counts:\n' in msg

        first_part = msg.partition('Captured queries were')[0]
        copy_past_part = first_part.partition('Got these counts:')[2]
        self.assertEqual(
            copy_past_part,
            "\n{'auth_group': 1, 'auth_permission': 2, 'django_admin_log': 1}\n\n\n",
        )

        # Missing counts
        with self.assertRaises(AssertionError) as err:
            queries.assert_table_counts({'auth_group': 1}, exclude=('foobar',))
        msg = str(err.exception)
        assert 'Table count error:\n' in msg
        assert '+auth_permission: 2\n' in msg

        # Excluding a table that is specified
        with self.assertRaises(AssertionError) as err:
            queries.assert_table_counts(
                {'auth_permission': 3, 'auth_group': 1}, exclude=('auth_permission',))
        msg = str(err.exception)
        assert msg == 'Excluded key \'auth_permission\' is listed in table_counts'

    def test_snapshot_table_counts(self):
        with AssertQueries() as queries:
            Permission.objects.all().first()
            Permission.objects.all().first()
            Group.objects.all().first()

        with AssertQueries() as second_queries:
            Permission.objects.all().first()
            Permission.objects.all().first()
            Permission.objects.all().first()
            Group.objects.all().first()

        with tempfile.TemporaryDirectory() as tmp_dir, OverrideEnviron(
            RAISE_SNAPSHOT_ERRORS='1'  # Maybe it's disabled in this test run!
        ), self.assertRaises(FileNotFoundError):
            queries.snapshot_table_counts(
                exclude=('auth_group',),
                root_dir=tmp_dir,
                snapshot_name='test',
            )

            queries.snapshot_table_counts(
                exclude=('auth_group',), root_dir=tmp_dir, snapshot_name='test'
            )

            snapshot_file = pathlib.Path(tmp_dir) / 'test.snapshot.json'
            snapshot_data = json.loads(snapshot_file.read_text())
            self.assertEqual(
                snapshot_data,
                {
                    'auth_permission': 2,
                },
            )

            with self.assertRaises(AssertionError) as error_capture:
                second_queries.snapshot_table_counts(
                    exclude=('auth_group',), root_dir=tmp_dir, snapshot_name='test'
                )

            message = str(error_capture.exception)
            self.assertIn('"auth_permission": 2', message)
            self.assertIn('"auth_permission": 3', message)

        # Use actual test files
        queries.snapshot_table_counts(exclude=('auth_group',))
        second_queries.snapshot_table_counts()

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
        assert 'bx_django_utils_tests/tests/test_assert_queries.py' in msg
        assert ' test_assert_duplicated_queries():\n' in msg
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

    def test_assert_queries_variants(self):

        # INSERT INTO "auth_group" ("name") VALUES (%s)

        with AssertQueries() as queries:
            Group.objects.create(name='foo')
        queries.assert_queries(
            table_counts=Counter({
                'auth_group': 1
            }),
            double_tables=True,
            table_names=['auth_group'],
            duplicated=True,
            similar=True,
        )

        # SELECT "auth_group"."id", "auth_group"."name" FROM...

        with AssertQueries() as queries:
            group = Group.objects.first()
        queries.assert_queries(
            table_counts=Counter({
                'auth_group': 1
            }),
            double_tables=True,
            table_names=['auth_group'],
            duplicated=True,
            similar=True,
        )

        # UPDATE "auth_group" SET "name" = %s WHERE...

        with AssertQueries() as queries:
            group.name = 'foo bar'
            group.save(update_fields=['name'])
        queries.assert_queries(
            table_counts=Counter({
                'auth_group': 1
            }),
            double_tables=True,
            table_names=['auth_group'],
            duplicated=True,
            similar=True,
        )

        # SAVEPOINT...RELEASE SAVEPOINT

        with AssertQueries() as queries:
            with transaction.atomic():
                group.name = 'foobar'
                group.save()

        queries.assert_queries(
            table_counts=Counter({
                'auth_group': 1
            }),
            double_tables=True,
            table_names=['auth_group'],
            duplicated=True,
            similar=True,
        )

        # INNER JOIN tables will be ignored:

        with AssertQueries() as queries:
            Group.objects.filter(
                permissions__in=Permission.objects.filter(content_type__app_label='not-exist')
            ).count()

        queries.assert_queries(
            table_counts=Counter({
                'auth_group': 1
            }),
            double_tables=True,
            table_names=['auth_group'],
            duplicated=True,
            similar=True,
        )

    def test_query_explain(self):
        with AssertQueries(query_explain=True) as queries:
            Permission.objects.all().first()

        results = list(queries.get_explains())
        self.assertEqual(len(results), 1)
        table_name, explain_str = results[0]

        self.assertEqual(table_name, 'auth_permission')
        self.assertIsInstance(explain_str, str)
        if connection.vendor == 'sqlite':
            # Depends on SQLite version/implementation!
            self.assertIn(' SCAN ', explain_str)
            self.assertIn(' USING INDEX ', explain_str)
            self.assertIn(' SEARCH ', explain_str)

    def test_query_info(self):
        with AssertQueries(query_explain=True) as queries:
            Permission.objects.all().first()
            Group.objects.all().first()

        query_info = queries.query_info
        self.assertIsInstance(query_info, str)
        self.assertIn('1. SELECT ', query_info)
        self.assertIn('2. SELECT ', query_info)
        self.assertIn('bx_django_utils_tests/tests/test_assert_queries.py ', query_info)
        self.assertIn(' test_query_info():\n', query_info)
        if connection.vendor == 'sqlite':
            # Depends on SQLite version/implementation!
            self.assertIn(' SCAN ', query_info)
            self.assertIn(' USING INDEX ', query_info)
            self.assertIn(' SEARCH ', query_info)

    def test_query_explain_not_captured(self):
        with AssertQueries() as queries:
            Permission.objects.all().first()

        with self.assertRaisesMessage(AssertionError, 'Explain way not captured!'):
            list(queries.get_explains())

    def test_query_info_max_stacktrace(self):
        with AssertQueries(max_stacktrace=2) as queries:
            make_database_queries2(count=1)

        query_info = queries.query_info
        self.assertIsInstance(query_info, str)
        self.assertIn('bx_django_utils_tests/tests/test_assert_queries.py ', query_info)
        self.assertIn('make_database_queries2():\n', query_info)  # <<< last two frames present
        self.assertIn('make_database_queries():\n', query_info)  # last frame

        with AssertQueries(max_stacktrace=1) as queries:
            make_database_queries2(count=1)

        query_info = queries.query_info
        self.assertIsInstance(query_info, str)
        self.assertIn('bx_django_utils_tests/tests/test_assert_queries.py ', query_info)
        self.assertNotIn('make_database_queries2():', query_info)  # <<< only last -> not present
        self.assertIn('make_database_queries():\n', query_info)  # last frame
