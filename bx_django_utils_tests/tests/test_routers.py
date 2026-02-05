from django.db import OperationalError
from django.test import TestCase
from model_bakery import baker

from bx_django_utils_tests.test_app.models import ColorFieldTestModel, ColorFieldTestModelSecondary


class DatabaseRoutersTestCase(TestCase):
    databases = ['default', 'second']

    def test_database_router(self):
        baker.make(
            ColorFieldTestModel,
            pk=1,
            required_color='#000002',
            optional_color='#000003',
        )
        with self.assertRaises(OperationalError):
            ColorFieldTestModel.objects.using("second").count()
        self.assertEqual(ColorFieldTestModel.objects.using("default").count(), 1)

    def test_database_router_secondary(self):
        baker.make(
            ColorFieldTestModelSecondary,
            pk=1,
            required_color='#000002',
            optional_color='#000003',
        )
        with self.assertRaises(OperationalError):
            ColorFieldTestModelSecondary.objects.using("default").count()
        self.assertEqual(ColorFieldTestModelSecondary.objects.using("second").count(), 1)
