from functools import partial
from unittest.mock import sentinel

from django.db import connections
from django.db.backends.utils import CursorWrapper
from django.test import TestCase

from bx_django_utils.dbperf.cursor import RecordingCursorWrapper
from bx_django_utils.dbperf.query_recorder import SQLQueryRecorder
from bx_django_utils_tests.test_app.models import CreateOrUpdateTestModel


class SQLQueryRecorderTestCase(TestCase):
    def test_cursor_wrapping(self):
        self.assertIsInstance(connections['default'].cursor(), CursorWrapper)
        with SQLQueryRecorder(databases=self.databases):
            self.assertIsInstance(connections['default'].cursor(), RecordingCursorWrapper)
        self.assertIsInstance(connections['default'].cursor(), CursorWrapper)

    def test_results_not_accessible_during_run(self):
        with SQLQueryRecorder(databases=self.databases) as rec:
            CreateOrUpdateTestModel.objects.count()
            with self.assertRaises(AssertionError):
                _ = rec.results()  # accessed before exiting context

    def test_results(self):
        with SQLQueryRecorder(databases=self.databases) as rec:
            CreateOrUpdateTestModel.objects.count()

        res = rec.results()
        self.assertCountEqual(res, (
            'queries',
            'databases',
            'sql_time',
            'num_queries',
            'queries_similar',
            'queries_duplicated',
            'num_queries_similar',
            'num_queries_duplicated',
        ))
        self.assertEqual(len(res['queries']), 1)
        self.assertGreater(res['sql_time'], 0)
        self.assertEqual(res['num_queries'], 1)
        self.assertEqual(len(res['queries_similar']), 1)
        self.assertEqual(len(res['queries_duplicated']), 1)

    def test_results_aggregation(self):
        with SQLQueryRecorder(databases=self.databases) as rec:
            # do some queries, explanation see below
            CreateOrUpdateTestModel.objects.count()
            CreateOrUpdateTestModel.objects.count()
            try:
                CreateOrUpdateTestModel.objects.only('id').get(id=99)
            except CreateOrUpdateTestModel.DoesNotExist:
                pass  # we just want the query to happen, not interested in the result
            len(CreateOrUpdateTestModel.objects.filter(name__iexact='foo').only('id'))
            len(CreateOrUpdateTestModel.objects.filter(name__iexact='bar').only('id'))
            len(CreateOrUpdateTestModel.objects.filter(name__iexact='baz').only('id'))
            len(CreateOrUpdateTestModel.objects.filter(name__iexact='foo').only('id'))

        res = rec.results()
        self.assertEqual(len(res['queries']), 7)
        self.assertGreater(res['sql_time'], 0)
        self.assertEqual(res['num_queries'], 7)

        self.assertEqual(len(res['queries_similar']['default']), 2)
        self.assertEqual(len(res['queries_duplicated']['default']), 2)
        self.assertEqual(res['num_queries_similar'], 2)
        self.assertEqual(res['num_queries_duplicated'], 2)

        #
        # CreateOrUpdateTestModel.objects.count()
        # we ran it twice, it should show as both similar and duplicate
        # because it doesn't have any params
        #
        query = 'SELECT COUNT(*) AS "__count" FROM "test_app_createorupdatetestmodel"'
        self.assertEqual(res['queries_similar']['default'][query], 2)
        self.assertEqual(res['queries_duplicated']['default'][(query, '()')], 2)

        #
        # CreateOrUpdateTestModel.objects.only('id').first()
        # we ran it once, so it shouldn't appear in either aggregation dict
        #
        query = 'SELECT "test_app_createorupdatetestmodel"."id" FROM "test_app_createorupdatetestmodel" WHERE "test_app_createorupdatetestmodel"."id" = %s'  # noqa: E501
        self.assertNotIn(query, res['queries_similar']['default'])
        self.assertNotIn(
            (query, "('00000000000000000000000000000063',)"),
            res['queries_duplicated']['default'],
        )

        #
        # TonieCloudUser.objects.filter(email__iexact=...).only('id')
        # we ran it quadruply, twice with the same params
        # it should show as both similar and duplicated
        #
        query = 'SELECT "test_app_createorupdatetestmodel"."id" FROM "test_app_createorupdatetestmodel" WHERE "test_app_createorupdatetestmodel"."name" LIKE %s ESCAPE \'\\\''  # noqa: E501
        self.assertEqual(res['queries_similar']['default'][query], 4)
        self.assertEqual(res['queries_duplicated']['default'][(query, "('foo',)")], 2)
        self.assertNotIn((query, "('bar',)"), res['queries_duplicated']['default'])
        self.assertNotIn((query, "('baz',)"), res['queries_duplicated']['default'])

    def test_exit_restores_preexisting_cursor_instance_attr(self):
        # If something else (e.g. Django's _DatabaseFailure) set cursor as an
        # instance attribute before we entered, __exit__ must restore that value
        # instead of deleting the attribute entirely.
        conn = connections['default']
        fake_cursor = partial(lambda: sentinel.cursor)
        conn.cursor = fake_cursor

        try:
            with SQLQueryRecorder(databases=['default']):
                # Inside the context the cursor is wrapped
                self.assertNotEqual(conn.cursor, fake_cursor)

            # After exit, the pre-existing instance attribute is restored
            self.assertIs(conn.cursor, fake_cursor)
        finally:
            del conn.cursor  # clean up so other tests see the class-level method

    def test_exit_removes_instance_attr_when_class_method_was_original(self):
        # If no instance-level cursor existed before entering, __exit__ must
        # delete the instance attribute (not leave a stale partial behind).
        # Temporarily remove any pre-existing instance cursor (e.g. set by
        # Django Debug Toolbar) so we can test the class-method restore path.
        conn = connections['default']
        preexisting = conn.__dict__.pop('cursor', None)
        preexisting_chunked = conn.__dict__.pop('chunked_cursor', None)
        try:
            self.assertNotIn('cursor', conn.__dict__)

            with SQLQueryRecorder(databases=['default']):
                self.assertIn('cursor', conn.__dict__)

            # The instance attribute must be gone; the class method is accessible again
            self.assertNotIn('cursor', conn.__dict__)
            self.assertIsInstance(conn.cursor(), CursorWrapper)
        finally:
            if preexisting is not None:
                conn.cursor = preexisting
            if preexisting_chunked is not None:
                conn.chunked_cursor = preexisting_chunked
